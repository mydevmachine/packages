import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

PROVIDER = os.path.join(os.path.dirname(__file__), "..", "bin", "provider")


class FakeHostinger(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        return json.loads(self.rfile.read(length))

    def _reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.server.user_agents.append(self.headers.get("User-Agent"))
        self.server.requests.append(("GET", self.path, None))
        if self.path.startswith("/api/domains/v1/portfolio"):
            self._reply(200, self.server.portfolio)
            return
        zone = self.server.zone
        if zone is None:
            self._reply(401, {"message": "Unauthenticated.", "correlation_id": "c-1"})
            return
        if self.server.not_found:
            self._reply(404, {"message": "Domain not found", "correlation_id": "c-2"})
            return
        self._reply(200, zone)

    def do_PUT(self):
        body = self._body()
        self.server.requests.append(("PUT", self.path, body))
        if self.server.rate_limited:
            self._reply(429, {"message": "Too many requests", "correlation_id": "c-3"})
            return
        for entry in body["zone"]:
            self.server.zone = self.server.zone or []
            existing = next(
                (r for r in self.server.zone if r["name"] == entry["name"] and r["type"] == entry["type"]),
                None,
            )
            if body["overwrite"] or existing is None:
                self.server.zone = [
                    r for r in self.server.zone if not (r["name"] == entry["name"] and r["type"] == entry["type"])
                ]
                self.server.zone.append(entry)
            else:
                existing["ttl"] = entry["ttl"]
                existing["records"].extend(entry["records"])
        self._reply(200, {"message": "Request accepted"})

    def do_DELETE(self):
        body = self._body()
        self.server.requests.append(("DELETE", self.path, body))
        for f in body["filters"]:
            self.server.zone = [
                r for r in self.server.zone if not (r["name"] == f["name"] and r["type"] == f["type"])
            ]
        self._reply(200, {"message": "Request accepted"})


class FakeServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zone = []
        self.requests = []
        self.user_agents = []
        self.not_found = False
        self.rate_limited = False
        self.portfolio = []


class ProviderTest(unittest.TestCase):
    def setUp(self):
        self.server = FakeServer(("127.0.0.1", 0), FakeHostinger)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.base_url = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def run_provider(self, args, stdin="", extra_env=None):
        env = dict(os.environ)
        env["HOSTINGER_API_TOKEN"] = "hpat_test_token"
        env["DEVMACHINE_DNS_BASE"] = self.base_url
        env.update(extra_env or {})
        result = subprocess.run(
            [sys.executable, PROVIDER] + args,
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
        )
        return result

    def test_list_flattens_an_rrset(self):
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        result = self.run_provider(["list", "example.com"])
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(
            out,
            {"records": [{"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 300}]},
        )

    def test_list_writes_every_type_the_way_a_zone_file_does(self):
        self.server.zone = [
            {"name": "@", "type": "MX", "ttl": 300, "records": [{"content": "10 Mail.Example.com."}]},
            {"name": "_sip._tcp", "type": "SRV", "ttl": 300, "records": [{"content": "10 5 5060 sip.example.com."}]},
            {"name": "@", "type": "NS", "ttl": 300, "records": [{"content": "ns1.example.net."}]},
            {"name": "@", "type": "CAA", "ttl": 300, "records": [{"content": '0 issue "ca.example.net"'}]},
            {"name": "www", "type": "CNAME", "ttl": 300, "records": [{"content": "example.com."}]},
            {"name": "@", "type": "SOA", "ttl": 300, "records": [{"content": "ns1.example.net. hostmaster.example.net. 1 2 3 4 5"}]},
        ]
        result = self.run_provider(["list", "example.com"])
        out = json.loads(result.stdout)
        # Hostinger adds a trailing dot to every host it stores; the value
        # the CLI compares against never has one.
        self.assertEqual(
            [(r["type"], r["value"]) for r in out["records"]],
            [
                ("MX", "10 mail.example.com"),
                ("SRV", "10 5 5060 sip.example.com"),
                ("NS", "ns1.example.net"),
                ("CAA", '0 issue "ca.example.net"'),
                ("CNAME", "example.com"),
            ],
        )

    def test_upsert_sends_an_mx_as_one_content_string(self):
        self.server.zone = []
        record = {"name": "@", "type": "MX", "value": "10 mail.example.com", "ttl": 0}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0, result.stdout)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["type"], "MX")
        self.assertEqual(puts[0][2]["zone"][0]["records"], [{"content": "10 mail.example.com"}])

    def test_upsert_sees_an_mx_already_right_despite_hostingers_trailing_dot(self):
        self.server.zone = [
            {"name": "@", "type": "MX", "ttl": 300, "records": [{"content": "10 mail.example.com."}]},
        ]
        record = {"name": "@", "type": "MX", "value": "10 mail.example.com", "ttl": 0}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        writes = [r for r in self.server.requests if r[0] in ("PUT", "DELETE")]
        self.assertEqual(writes, [])

    def test_append_adds_a_value_next_to_the_existing_ones(self):
        self.server.zone = [
            {"name": "@", "type": "MX", "ttl": 300, "records": [{"content": "10 mail.example.com."}]},
        ]
        record = {"name": "@", "type": "MX", "value": "20 mail2.example.com", "ttl": 0}
        result = self.run_provider(["append", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout), {})
        writes = [r for r in self.server.requests if r[0] in ("PUT", "DELETE")]
        # One PUT with overwrite: false, which is Hostinger's append. No
        # DELETE: the value already there is the point of this command.
        self.assertEqual([w[0] for w in writes], ["PUT"])
        self.assertFalse(writes[0][2]["overwrite"])
        self.assertEqual(writes[0][2]["zone"][0]["records"], [{"content": "20 mail2.example.com"}])
        self.assertEqual(writes[0][2]["zone"][0]["ttl"], 300)
        contents = [e["content"] for e in self.server.zone[0]["records"]]
        self.assertEqual(contents, ["10 mail.example.com.", "20 mail2.example.com"])

    def test_append_does_nothing_when_the_value_is_already_there(self):
        self.server.zone = [
            {"name": "@", "type": "MX", "ttl": 300, "records": [{"content": "10 mail.example.com."}]},
        ]
        record = {"name": "@", "type": "MX", "value": "10 mail.example.com", "ttl": 0}
        result = self.run_provider(["append", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        writes = [r for r in self.server.requests if r[0] in ("PUT", "DELETE")]
        self.assertEqual(writes, [])

    def test_append_to_a_name_that_holds_nothing_creates_it(self):
        self.server.zone = []
        record = {"name": "@", "type": "MX", "value": "10 mail.example.com", "ttl": 0}
        result = self.run_provider(["append", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["ttl"], 3600)
        self.assertFalse(puts[0][2]["overwrite"])

    def test_append_with_a_ttl_sets_the_sets_ttl(self):
        self.server.zone = [
            {"name": "@", "type": "MX", "ttl": 300, "records": [{"content": "10 mail.example.com."}]},
        ]
        record = {"name": "@", "type": "MX", "value": "20 mail2.example.com", "ttl": 600}
        self.run_provider(["append", "example.com"], stdin=json.dumps(record))
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["ttl"], 600)

    def test_delete_one_mx_among_several_matches_despite_the_trailing_dot(self):
        self.server.zone = [
            {
                "name": "@",
                "type": "MX",
                "ttl": 300,
                "records": [{"content": "10 mail.example.com."}, {"content": "20 mail2.example.com."}],
            },
        ]
        record = {"name": "@", "type": "MX", "value": "10 mail.example.com", "ttl": 0}
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        kept = puts[0][2]["zone"][0]["records"]
        self.assertEqual([r["content"] for r in kept], ["20 mail2.example.com."])

    def test_upsert_creates_by_appending_to_nothing(self):
        self.server.zone = []
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 300}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(len(puts), 1)
        self.assertFalse(puts[0][2]["overwrite"])

    def test_upsert_does_nothing_when_the_value_is_already_right(self):
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 300}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})
        writes = [r for r in self.server.requests if r[0] in ("PUT", "DELETE")]
        self.assertEqual(writes, [])

    def test_upsert_replaces_rather_than_appends(self):
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.20", "ttl": 300}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        # DELETE then PUT with overwrite: false. The one-call path needs
        # overwrite: true, and nothing Hostinger documents says the names
        # absent from that payload survive it.
        writes = [r for r in self.server.requests if r[0] in ("DELETE", "PUT")]
        self.assertEqual([w[0] for w in writes], ["DELETE", "PUT"])
        self.assertFalse(writes[1][2]["overwrite"])
        contents = writes[1][2]["zone"][0]["records"]
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["content"], "198.51.100.20")

    def test_upsert_gives_a_new_record_a_default_ttl_when_none_is_given(self):
        self.server.zone = []
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 0}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["ttl"], 3600)

    def test_upsert_keeps_an_explicit_ttl_for_a_new_record(self):
        self.server.zone = []
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 120}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["ttl"], 120)

    def test_upsert_rejects_an_explicit_ttl_below_the_minimum(self):
        self.server.zone = []
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 30}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertNotEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out["error"]["kind"], "invalid_record")
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts, [])

    def test_upsert_keeps_the_existing_ttl_when_none_is_given_on_replace(self):
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.20", "ttl": 0}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts[0][2]["zone"][0]["ttl"], 300)

    def test_upsert_always_sends_overwrite_explicitly(self):
        # overwrite defaults to true on Hostinger's API; a request that omits
        # it is the destructive choice, so every PUT body carries the field.
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.20", "ttl": 300}
        self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        for _, _, body in puts:
            self.assertIn("overwrite", body)

    def test_delete_takes_the_whole_set_when_it_holds_only_that_value(self):
        self.server.zone = [
            {"name": "www", "type": "A", "ttl": 300, "records": [{"content": "198.51.100.10"}]},
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 0}
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        deletes = [r for r in self.server.requests if r[0] == "DELETE"]
        self.assertEqual(len(deletes), 1)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts, [])

    def test_delete_keeps_the_other_values_of_the_same_name(self):
        self.server.zone = [
            {
                "name": "www",
                "type": "A",
                "ttl": 300,
                "records": [{"content": "198.51.100.10"}, {"content": "198.51.100.20"}],
            },
        ]
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 0}
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        deletes = [r for r in self.server.requests if r[0] == "DELETE"]
        self.assertEqual(len(deletes), 1)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(len(puts), 1)
        kept = puts[0][2]["zone"][0]["records"]
        self.assertEqual([r["content"] for r in kept], ["198.51.100.20"])

    def test_delete_with_no_value_takes_the_whole_set(self):
        self.server.zone = [
            {
                "name": "www",
                "type": "A",
                "ttl": 300,
                "records": [{"content": "198.51.100.10"}, {"content": "198.51.100.20"}],
            },
        ]
        record = {"name": "www", "type": "A", "value": "", "ttl": 0}
        result = self.run_provider(["delete", "example.com"], stdin=json.dumps(record))
        self.assertEqual(result.returncode, 0)
        deletes = [r for r in self.server.requests if r[0] == "DELETE"]
        self.assertEqual(len(deletes), 1)
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(puts, [])

    def test_every_call_names_itself_instead_of_pythons_default_agent(self):
        self.server.zone = []
        result = self.run_provider(["list", "example.com"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.server.user_agents)
        for agent in self.server.user_agents:
            self.assertFalse(agent.startswith("Python-urllib"), agent)
            self.assertTrue(agent.startswith("devmachine-hostinger"), agent)

    def test_a_404_is_reported_as_zone_not_found(self):
        self.server.not_found = True
        result = self.run_provider(["list", "example.com"])
        self.assertNotEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out["error"]["kind"], "zone_not_found")

    def test_a_401_is_reported_as_unauthenticated(self):
        self.server.zone = None
        result = self.run_provider(["list", "example.com"])
        self.assertNotEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out["error"]["kind"], "unauthenticated")

    def test_a_429_is_reported_as_rate_limited_and_not_retried(self):
        self.server.zone = []
        self.server.rate_limited = True
        record = {"name": "www", "type": "A", "value": "198.51.100.10", "ttl": 300}
        result = self.run_provider(["upsert", "example.com"], stdin=json.dumps(record))
        self.assertNotEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out["error"]["kind"], "rate_limited")
        puts = [r for r in self.server.requests if r[0] == "PUT"]
        self.assertEqual(len(puts), 1)

    def test_zones_reports_what_the_token_can_see(self):
        self.server.portfolio = [{"domain": "example.com"}, {"domain": "example.net"}]
        result = self.run_provider(["zones"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"zones": ["example.com", "example.net"]})

    def test_zones_uses_the_configured_list_without_portfolio_permission(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as zones:
            json.dump(["example.com", "example.net"], zones)
            zones.flush()
            result = self.run_provider(
                ["zones"], extra_env={"DEVMACHINE_HOSTINGER_ZONES_FILE": zones.name}
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"zones": ["example.com", "example.net"]})
        self.assertEqual(self.server.requests, [])

    def test_zones_takes_no_zone(self):
        # `zones` is how the CLI finds out which registrar holds a name, so
        # asking it for a zone first would be circular.
        self.server.portfolio = []
        self.assertEqual(self.run_provider(["zones"]).returncode, 0)

    def test_help_lists_every_command_the_manifest_declares(self):
        # `devmachine packages help` asks the package itself. A manifest that
        # declares a command the entrypoint refuses is a lie nothing catches.
        result = self.run_provider(["help"])
        self.assertEqual(result.returncode, 0)
        names = [c["name"] for c in json.loads(result.stdout)["commands"]]
        self.assertEqual(sorted(names), ["append", "delete", "help", "list", "upsert", "zones"])

    def test_a_command_that_needs_a_zone_says_so(self):
        result = self.run_provider(["list"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"]["kind"], "invalid_record")

if __name__ == "__main__":
    unittest.main()
