import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks", "main.yml")
DARWIN_VARS = os.path.join(ROOT, "vars", "Darwin.yml")
DEFAULT_VARS = os.path.join(ROOT, "vars", "main.yml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def block(name):
    lines = read(TASKS).splitlines()
    start = next(i for i, line in enumerate(lines) if line == "- name: " + name)
    body = start + next(i for i, line in enumerate(lines[start:]) if line.strip() == "block: |") + 1
    content = []
    for line in lines[body:]:
        if line.strip() and not line.startswith(" " * 6):
            break
        content.append(line[6:])
    return "\n".join(content).strip() + "\n"


def path_block(directories):
    return re.sub(r"\{\{ devmachine_zsh_path_prefix \| reverse \| join\(' '\) \}\}",
                  " ".join(reversed(directories)), block("Put the package manager on the account's PATH"))


def path_after(script, path):
    return subprocess.run(["/bin/sh", "-c", script + 'printf %s "$PATH"'], env={"PATH": path}, check=True,
                          capture_output=True, text=True).stdout


class AutoAttach(unittest.TestCase):
    def test_a_missing_tmux_never_ends_the_login(self):
        self.assertIn("command -v tmux >/dev/null 2>&1", block("Attach to tmux on an SSH login"))


class LoginPath(unittest.TestCase):
    def test_linux_adds_nothing(self):
        self.assertRegex(read(DEFAULT_VARS), r"(?m)^devmachine_zsh_path_prefix: \[\]$")

    def test_a_mac_names_the_package_manager_prefix(self):
        darwin = read(DARWIN_VARS)
        self.assertIn("devmachine_zsh_path_prefix:", darwin)
        self.assertIn("'/opt/local/bin', '/opt/local/sbin'", darwin)
        self.assertIn("/opt/homebrew", darwin)

    def test_the_prefix_comes_first_in_order(self):
        path = path_after(path_block(["/opt/local/bin", "/opt/local/sbin"]), "/usr/bin:/bin")
        self.assertEqual(path, "/opt/local/bin:/opt/local/sbin:/usr/bin:/bin")

    def test_a_directory_already_on_path_is_not_added_again(self):
        script = path_block(["/opt/local/bin", "/opt/local/sbin"])
        path = path_after(script + script, "/usr/bin:/opt/local/sbin")
        self.assertEqual(path, "/opt/local/bin:/usr/bin:/opt/local/sbin")


if __name__ == "__main__":
    unittest.main()
