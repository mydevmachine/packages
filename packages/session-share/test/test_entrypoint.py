import os
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRYPOINT = os.path.join(ROOT, "bin", "session-share")
TASKS = os.path.join(ROOT, "tasks", "main.yml")


def run(home, *args):
    env = dict(os.environ, HOME=home)
    return subprocess.run([sys.executable, ENTRYPOINT, *args], env=env, capture_output=True, text=True)


def fake_binary(home):
    path = os.path.join(home, ".local", "bin", "session-share")
    os.makedirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class Entrypoint(unittest.TestCase):
    def test_a_command_reaches_the_account_binary_with_its_arguments(self):
        with tempfile.TemporaryDirectory() as home:
            fake_binary(home)
            result = run(home, "start", "api", "--mode", "write")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), ["start", "api", "--mode", "write"])

    def test_chat_reaches_the_binary(self):
        with tempfile.TemporaryDirectory() as home:
            fake_binary(home)
            result = run(home, "chat", "abcdefghijkl", "hi there")
            self.assertEqual(result.stdout.splitlines(), ["chat", "abcdefghijkl", "hi there"])

    def test_the_provider_asks_for_every_share_as_json(self):
        with tempfile.TemporaryDirectory() as home:
            fake_binary(home)
            result = run(home, "shares")
            self.assertEqual(result.stdout.split(), ["list", "--all", "--json"])

    def test_a_command_it_does_not_know_is_refused(self):
        with tempfile.TemporaryDirectory() as home:
            fake_binary(home)
            result = run(home, "attach", "abc")
            self.assertEqual(result.returncode, 2)
            self.assertIn("usage", result.stderr)

    def test_a_missing_binary_says_how_to_get_it(self):
        with tempfile.TemporaryDirectory() as home:
            result = run(home, "list")
            self.assertEqual(result.returncode, 1)
            self.assertIn("sync", result.stderr)


class Install(unittest.TestCase):
    def test_the_download_is_checked_against_the_release_checksums(self):
        with open(TASKS, encoding="utf-8") as handle:
            tasks = handle.read()
        self.assertIn('checksum: "sha256:{{ devmachine_session_share_base }}/checksums.txt"', tasks)

    def test_the_binary_keeps_one_path_across_versions(self):
        with open(TASKS, encoding="utf-8") as handle:
            tasks = handle.read()
        self.assertIn('dest: "{{ devmachine_session_share_home }}/.local/bin/session-share"', tasks)


if __name__ == "__main__":
    unittest.main()
