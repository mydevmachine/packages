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
            return
        if method == "PUT":
            if any("data" not in item for item in body):
                self._reply(422, {"code": "INVALID_BODY", "message": "Request body doesn't fulfill schema",
                                  "fields": [{"path": "records[0].data", "code": "REQUIRED", "message": "is required"}]})
                return
            records[:] = [r for r in records if r not in selected]
            records.extend(dict(item, type=record_type, name=name) for item in body)
            self._reply(200)
            return
        if method == "DELETE":
            if not selected:
                self._reply(404, {"code": "UNKNOWN_RECORD", "message": "No such record"})
                return
            records[:] = [r for r in records if r not in selected]
            self._reply(204)

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

    def test_zones_follows_the_marker_until_an_empty_page(self):
        self.server.page_size = 2
        self.server.domains = [{"domain": d, "status": "ACTIVE"} for d in ("a.example", "b.example", "c.example")]
        result = self.run_provider(["zones"])
        self.assertEqual(json.loads(result.stdout), {"zones": ["a.example", "b.example", "c.example"]})
        markers = [r[2].get("marker", [None])[0] for r in self.server.requests]
        self.assertEqual(markers, [None, "b.example", "c.example"])

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
        for status, kind in ((400, "invalid_record"), (401, "unauthenticated"), (403, "forbidden"), (429, "rate_limited"), (422, "invalid_record")):
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

    def test_an_unmapped_status_names_the_http_status_and_godaddys_message(self):
        self.server.force_status = 500
        self.server.force_body = {"code": "INTERNAL", "message": "something broke upstream"}
        out = json.loads(self.run_provider(["zones"]).stdout)["error"]
        self.assertEqual(out["kind"], "invalid_record")
        self.assertIn("HTTP 500", out["message"])
        self.assertIn("something broke upstream", out["message"])

    def test_zones_with_an_error_object_page_is_an_error(self):
        self.server.force_status = 404
        self.server.force_body = {"code": "NOT_FOUND", "message": "no such listing"}
        result = self.run_provider(["zones"])
        self.assertNotEqual(result.returncode, 0)
        out = json.loads(result.stdout)["error"]
        self.assertEqual(out["kind"], "zone_not_found")
        self.assertIn("no such listing", out["message"])

    def test_a_record_that_is_not_an_object_is_invalid(self):
        result = self.run_provider(["upsert", "example.com"], stdin="[]")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"]["kind"], "invalid_record")

    def test_a_record_missing_its_type_is_invalid(self):
        record = json.dumps({"name": "www", "value": "203.0.113.1"})
        for command in ("upsert", "delete"):
            with self.subTest(command=command):
                result = self.run_provider([command, "example.com"], stdin=record)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["error"]["kind"], "invalid_record")

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

    def test_upsert_replaces_the_whole_set_with_one_value(self):
        self.server.records["example.com"] = [
            {"type": "A", "name": "www", "data": "203.0.113.10", "ttl": 600},
            {"type": "A", "name": "www", "data": "203.0.113.11", "ttl": 600},
        ]
        record = json.dumps({"name": "www", "type": "A", "value": "203.0.113.20", "ttl": 300})
        result = self.run_provider(["upsert", "example.com"], stdin=record)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual(self.server.records["example.com"], [{"type": "A", "name": "www", "data": "203.0.113.20", "ttl": 300}])
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[-1][1], "/v1/domains/example.com/records/A/www")

    def test_upsert_with_ttl_zero_leaves_ttl_to_godaddy(self):
        record = json.dumps({"name": "www", "type": "A", "value": "203.0.113.20", "ttl": 0})
        self.server.records["example.com"] = []
        self.run_provider(["upsert", "example.com"], stdin=record)
        body = [r for r in self.server.requests if r[0] == "PUT"][-1][3]
        self.assertEqual(body, [{"data": "203.0.113.20"}])

    def test_upsert_keeps_a_txt_value_verbatim(self):
        value = 'v=spf1 include:"_spf.example.net" ~all'
        record = json.dumps({"name": "@", "type": "TXT", "value": value, "ttl": 600})
        self.server.records["example.com"] = []
        self.run_provider(["upsert", "example.com"], stdin=record)
        self.assertEqual(self.server.records["example.com"][0]["data"], value)

    def test_upsert_reports_a_422_with_the_field_messages(self):
        self.server.force_status = 422
        self.server.force_body = {"code": "INVALID_BODY", "message": "Request body doesn't fulfill schema",
                                  "fields": [{"path": "records[0].data", "code": "UNEXPECTED_TYPE", "message": "is not a valid IPv4"}]}
        record = json.dumps({"name": "www", "type": "A", "value": "nope", "ttl": 600})
        out = json.loads(self.run_provider(["upsert", "example.com"], stdin=record).stdout)
        self.assertEqual(out["error"]["kind"], "invalid_record")
        self.assertIn("is not a valid IPv4", out["error"]["message"])

    def test_upsert_rejects_stdin_that_is_not_json(self):
        out = json.loads(self.run_provider(["upsert", "example.com"], stdin="{").stdout)
        self.assertEqual(out["error"]["kind"], "invalid_record")

    def test_delete_of_the_only_value_deletes_the_set(self):
        self.server.records["example.com"] = [{"type": "A", "name": "www", "data": "203.0.113.10", "ttl": 600}]
        record = json.dumps({"name": "www", "type": "A", "value": "203.0.113.10"})
        result = self.run_provider(["delete", "example.com"], stdin=record)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual(self.server.records["example.com"], [])
        self.assertEqual([r[0] for r in self.server.requests][-1], "DELETE")

    def test_delete_of_one_value_among_several_puts_the_rest_back(self):
        self.server.records["example.com"] = [
            {"type": "A", "name": "www", "data": "203.0.113.10", "ttl": 600},
            {"type": "A", "name": "www", "data": "203.0.113.11", "ttl": 600},
        ]
        record = json.dumps({"name": "www", "type": "A", "value": "203.0.113.10"})
        self.run_provider(["delete", "example.com"], stdin=record)
        self.assertEqual(self.server.records["example.com"], [{"type": "A", "name": "www", "data": "203.0.113.11", "ttl": 600}])
        self.assertNotIn("DELETE", [r[0] for r in self.server.requests])

    def test_delete_with_no_value_removes_the_whole_set(self):
        self.server.records["example.com"] = [
            {"type": "A", "name": "www", "data": "203.0.113.10", "ttl": 600},
            {"type": "A", "name": "www", "data": "203.0.113.11", "ttl": 600},
        ]
        self.run_provider(["delete", "example.com"], stdin=json.dumps({"name": "www", "type": "A", "value": ""}))
        self.assertEqual(self.server.records["example.com"], [])

    def test_delete_of_a_value_not_there_is_a_no_op(self):
        self.server.records["example.com"] = [{"type": "A", "name": "www", "data": "203.0.113.10", "ttl": 600}]
        before = len(self.server.requests)
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps({"name": "www", "type": "A", "value": "203.0.113.99"}))
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual([r[0] for r in self.server.requests[before:]], ["GET"])

    def test_delete_of_a_name_that_does_not_exist_succeeds(self):
        self.server.records["example.com"] = []
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps({"name": "gone", "type": "A", "value": ""}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
