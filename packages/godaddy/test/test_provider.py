import json
import os
import re
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

RECORDS_ROUTE = re.compile(r"^/v1/domains/([^/]+)/records(?:/([^/]+)/([^/]+))?$")
PROVIDER = os.path.join(os.path.dirname(__file__), "..", "bin", "provider")


class FakeGoDaddy(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        return json.loads(self.rfile.read(length))

    def _reply(self, status, payload=None):
        body = json.dumps(payload).encode() if payload is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self, method):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        body = self._body()
        self.server.requests.append((method, parsed.path, query, body))

        if self.server.force_status:
            default = {"code": "FORCED", "message": "forced failure"}
            self._reply(self.server.force_status, self.server.force_body or default)
            return

        if method == "GET" and parsed.path == "/v1/domains":
            self._domains(query)
            return

        match = RECORDS_ROUTE.match(parsed.path)
        if match:
            self._records(method, match, body)
            return

        self._reply(404, {"code": "NOT_FOUND", "message": "no such route"})

    def _records(self, method, match, body):
        domain, record_type, name = match.groups()
        if domain not in self.server.records:
            self._reply(404, {"code": "UNKNOWN_DOMAIN", "message": "The given domain is not registered"})
            return
        records = self.server.records[domain]
        selected = [r for r in records if record_type in (None, r["type"]) and name in (None, r["name"])]
        if method == "GET":
            self._reply(200, selected)

    def _domains(self, query):
        active = [d for d in self.server.domains if d["status"] in query.get("statuses", [d["status"]])]
        limit = min(int(query.get("limit", ["1000"])[0]), self.server.page_size)
        marker = query.get("marker", [None])[0]
        if marker:
            names = [d["domain"] for d in active]
            active = active[names.index(marker) + 1:]
        self._reply(200, active[:limit])

    def do_GET(self):
        self._handle("GET")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")


class FakeServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.domains = []
        self.records = {}
        self.requests = []
        self.page_size = 1000
        self.force_status = None
        self.force_body = None


class ProviderTest(unittest.TestCase):
    def setUp(self):
        self.server = FakeServer(("127.0.0.1", 0), FakeGoDaddy)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.base_url = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_provider(self, args, stdin="", token="gd_pat_test"):
        env = dict(os.environ)
        env["GODADDY_API_TOKEN"] = token
        env["DEVMACHINE_DNS_BASE"] = self.base_url
        env["DEVMACHINE_DNS_PAGE_LIMIT"] = str(self.server.page_size)
        return subprocess.run(
            [sys.executable, PROVIDER] + args,
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_zones_lists_only_active_domains(self):
        self.server.domains = [
            {"domain": "example.com", "status": "ACTIVE"},
            {"domain": "example.net", "status": "CANCELLED"},
        ]
        result = self.run_provider(["zones"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"zones": ["example.com"]})

    def test_zones_follows_the_marker_until_a_short_page(self):
        self.server.page_size = 2
        self.server.domains = [{"domain": d, "status": "ACTIVE"} for d in ("a.example", "b.example", "c.example")]
        result = self.run_provider(["zones"])
        self.assertEqual(json.loads(result.stdout), {"zones": ["a.example", "b.example", "c.example"]})
        markers = [r[2].get("marker", [None])[0] for r in self.server.requests]
        self.assertEqual(markers, [None, "b.example"])

    def test_zones_is_empty_when_no_domain_is_active(self):
        self.server.domains = [{"domain": "example.com", "status": "CANCELLED"}]
        result = self.run_provider(["zones"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"zones": []})

    def test_a_missing_token_fails_before_any_request(self):
        result = self.run_provider(["zones"], token="")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"]["kind"], "unauthenticated")
        self.assertEqual(self.server.requests, [])

    def test_each_status_maps_to_its_kind(self):
        for status, kind in ((401, "unauthenticated"), (403, "forbidden"), (429, "rate_limited"), (422, "invalid_record")):
            with self.subTest(status=status):
                self.server.force_status = status
                result = self.run_provider(["zones"])
                self.assertEqual(json.loads(result.stdout)["error"]["kind"], kind)

    def test_a_403_carries_godaddys_code_and_message(self):
        self.server.force_status = 403
        self.server.force_body = {"code": "ACCESS_DENIED", "message": "Authenticated user is not allowed access"}
        result = self.run_provider(["zones"])
        message = json.loads(result.stdout)["error"]["message"]
        self.assertIn("ACCESS_DENIED", message)
        self.assertIn("not allowed access", message)

    def test_a_429_is_never_retried(self):
        self.server.force_status = 429
        self.run_provider(["zones"])
        self.assertEqual(len(self.server.requests), 1)

    def test_help_lists_every_command_the_manifest_declares(self):
        result = self.run_provider(["help"])
        names = [c["name"] for c in json.loads(result.stdout)["commands"]]
        self.assertEqual(names, ["zones", "list", "upsert", "delete", "help"])

    def test_a_command_that_needs_a_zone_says_so(self):
        result = self.run_provider(["list"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"]["kind"], "invalid_record")

    def test_list_maps_data_to_value_and_keeps_the_apex_label(self):
        self.server.records["example.com"] = [
            {"type": "A", "name": "@", "data": "203.0.113.10", "ttl": 600},
            {"type": "CNAME", "name": "www", "data": "example.com", "ttl": 3600},
            {"type": "MX", "name": "@", "data": "mail.example.com", "ttl": 3600, "priority": 10},
        ]
        out = json.loads(self.run_provider(["list", "example.com"]).stdout)
        self.assertEqual(out, {"records": [
            {"name": "@", "type": "A", "value": "203.0.113.10", "ttl": 600},
            {"name": "www", "type": "CNAME", "value": "example.com", "ttl": 3600},
        ]})

    def test_list_of_an_empty_zone_is_empty_not_missing(self):
        self.server.records["example.com"] = []
        result = self.run_provider(["list", "example.com"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"records": []})

    def test_list_of_an_unknown_domain_is_zone_not_found(self):
        result = self.run_provider(["list", "example.net"])
        self.assertEqual(json.loads(result.stdout)["error"]["kind"], "zone_not_found")

    def test_the_zone_is_lowercased_and_the_trailing_dot_dropped(self):
        self.server.records["example.com"] = []
        self.run_provider(["list", "Example.COM."])
        self.assertEqual(self.server.requests[-1][1], "/v1/domains/example.com/records")


if __name__ == "__main__":
    unittest.main()
