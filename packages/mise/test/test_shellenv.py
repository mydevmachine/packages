import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks", "main.yml")
NAME = "Activate mise in every shell"

FAKE_MISE = """#!/bin/sh
[ "$1" = activate ] && printf 'activated_for=%s\\n' "$2"
"""


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def task(name):
    lines = read(TASKS).splitlines()
    start = next(i for i, line in enumerate(lines) if line == "- name: " + name)
    end = next((i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith("- name: ")), len(lines))
    return "\n".join(lines[start:end])


def block(name):
    lines = task(name).splitlines()
    body = next(i for i, line in enumerate(lines) if line.strip() == "block: |") + 1
    content = []
    for line in lines[body:]:
        if line.strip() and not line.startswith(" " * 6):
            break
        content.append(line[6:])
    return "\n".join(content).strip() + "\n"


class Activation(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home)
        self.env = {"HOME": self.home, "PATH": "/usr/bin:/bin"}

    def install_mise(self):
        bin_dir = os.path.join(self.home, ".local", "bin")
        os.makedirs(bin_dir)
        mise = os.path.join(bin_dir, "mise")
        with open(mise, "w", encoding="utf-8") as handle:
            handle.write(FAKE_MISE)
        os.chmod(mise, 0o755)

    def run_in(self, shell, after):
        return subprocess.run([shell, "-c", block(NAME) + after], env=self.env, check=True, capture_output=True,
                              text=True).stdout

    def test_zsh_and_bash_activate_for_themselves(self):
        self.install_mise()
        for name in ("zsh", "bash"):
            shell = shutil.which(name)
            if not shell:
                continue
            with self.subTest(shell=name):
                self.assertEqual(self.run_in(shell, 'printf %s "$activated_for"'), name)

    def test_any_other_shell_gets_the_shims(self):
        shell = shutil.which("dash")
        if not shell:
            self.skipTest("no dash here")
        self.install_mise()
        shims = os.path.join(self.home, ".local", "share", "mise", "shims")
        self.assertEqual(self.run_in(shell, 'printf %s "$activated_for|$PATH"'), "|" + shims + ":/usr/bin:/bin")

    def test_no_mise_yet_is_not_an_error(self):
        for name in ("sh", "bash", "zsh", "dash"):
            shell = shutil.which(name)
            if not shell:
                continue
            with self.subTest(shell=name):
                self.assertEqual(self.run_in(shell, 'printf %s "$PATH"'), "/usr/bin:/bin")

    def test_it_goes_to_shellenv_and_leaves_zshenv(self):
        self.assertIn("/.devmachine/shellenv", task(NAME))
        self.assertIn("state: absent", read(TASKS))


if __name__ == "__main__":
    unittest.main()
