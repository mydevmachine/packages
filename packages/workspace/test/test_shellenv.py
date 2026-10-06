import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks", "main.yml")
DARWIN_VARS = os.path.join(ROOT, "vars", "Darwin.yml")
DEFAULT_VARS = os.path.join(ROOT, "vars", "main.yml")


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


def path_block(directories):
    return re.sub(r"\{\{ devmachine_workspace_path_prefix \| reverse \| join\(' '\) \}\}",
                  " ".join(reversed(directories)), block("Put the package manager on the account's PATH"))


def run(shell, script, env):
    return subprocess.run([shell, "-c", script], env=env, check=True, capture_output=True, text=True).stdout


def path_after(script, path):
    return run("/bin/sh", script + 'printf %s "$PATH"', {"PATH": path})


class LoginPath(unittest.TestCase):
    def test_linux_adds_nothing(self):
        self.assertRegex(read(DEFAULT_VARS), r"(?m)^devmachine_workspace_path_prefix: \[\]$")

    def test_a_mac_names_the_package_manager_prefix(self):
        darwin = read(DARWIN_VARS)
        self.assertIn("devmachine_workspace_path_prefix:", darwin)
        self.assertIn("'/opt/local/bin', '/opt/local/sbin'", darwin)
        self.assertIn("/opt/homebrew", darwin)

    def test_the_prefix_comes_first_in_order(self):
        path = path_after(path_block(["/opt/local/bin", "/opt/local/sbin"]), "/usr/bin:/bin")
        self.assertEqual(path, "/opt/local/bin:/opt/local/sbin:/usr/bin:/bin")

    def test_a_directory_already_on_path_is_not_added_again(self):
        script = path_block(["/opt/local/bin", "/opt/local/sbin"])
        path = path_after(script + script, "/usr/bin:/opt/local/sbin")
        self.assertEqual(path, "/opt/local/bin:/usr/bin:/opt/local/sbin")

    def test_it_goes_to_shellenv(self):
        self.assertIn("/.devmachine/shellenv", task("Put the package manager on the account's PATH"))


class Secrets(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home)
        self.env = {"HOME": self.home, "PATH": "/usr/bin:/bin"}

    def test_a_secret_reaches_a_program_the_shell_starts(self):
        os.makedirs(os.path.join(self.home, ".devmachine"))
        with open(os.path.join(self.home, ".devmachine", "env"), "w", encoding="utf-8") as handle:
            handle.write("ALICE_TOKEN='a b$c'\n")
        out = run("/bin/sh", block("Load the workspace's secrets in every shell") + 'sh -c \'printf %s "$ALICE_TOKEN"\'',
                  self.env)
        self.assertEqual(out, "a b$c")

    def test_no_secrets_file_is_not_an_error(self):
        run("/bin/sh", block("Load the workspace's secrets in every shell"), self.env)

    def test_it_goes_to_shellenv(self):
        self.assertIn("/.devmachine/shellenv", task("Load the workspace's secrets in every shell"))


class Hook(unittest.TestCase):
    NAME = "Read ~/.devmachine/shellenv from every shell's startup files"

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home)
        self.env = {"HOME": self.home, "PATH": "/usr/bin:/bin"}

    def write_shellenv(self, text):
        os.makedirs(os.path.join(self.home, ".devmachine"), exist_ok=True)
        with open(os.path.join(self.home, ".devmachine", "shellenv"), "w", encoding="utf-8") as handle:
            handle.write(text)

    def shells(self):
        return [shell for shell in ("/bin/sh", shutil.which("bash"), shutil.which("zsh")) if shell]

    def test_two_startup_files_in_one_shell_read_it_once(self):
        self.write_shellenv("loads=$((loads + 1))\n")
        hook = block(self.NAME)
        for shell in self.shells():
            with self.subTest(shell=shell):
                self.assertEqual(run(shell, "loads=0\n" + hook + hook + 'printf %s "$loads"', self.env), "1")

    def test_a_shell_it_starts_reads_it_again(self):
        self.write_shellenv("alice_loaded=yes\n")
        hook = block(self.NAME)
        nested = hook + 'printf %s "$alice_loaded"'
        script = hook + "sh -c " + "'" + nested.replace("'", "'\\''") + "'"
        self.assertEqual(run("/bin/sh", script, self.env), "yes")

    def test_no_shellenv_is_not_an_error(self):
        for shell in self.shells():
            with self.subTest(shell=shell):
                run(shell, block(self.NAME), self.env)

    def test_it_is_read_before_bashrc_returns_for_a_shell_that_is_not_interactive(self):
        self.assertIn("insertbefore: BOF", task(self.NAME))

    def test_every_shell_has_a_startup_file_that_reads_it(self):
        hooked = task(self.NAME)
        for startup in (".zshenv", ".bashrc", ".profile", ".bash_profile"):
            self.assertIn(startup, hooked)


def every_task():
    packages = os.path.dirname(ROOT)
    for package in sorted(os.listdir(packages)):
        tasks = os.path.join(packages, package, "tasks", "main.yml")
        if not os.path.isfile(tasks):
            continue
        for chunk in re.split(r"\n(?=- name: )", read(tasks)):
            if chunk.startswith("- name: "):
                yield package, chunk


class Packages(unittest.TestCase):
    def test_only_the_workspace_hook_writes_a_zsh_startup_file_for_the_environment(self):
        for package, chunk in every_task():
            if ".zshenv" not in chunk or "path:" not in chunk:
                continue
            with self.subTest(package=package, task=chunk.splitlines()[0]):
                self.assertTrue("state: absent" in chunk or (package == "workspace" and "shellenv" in chunk))

    def test_a_block_written_by_many_packages_is_the_same_in_each(self):
        marker = 'marker: "# {mark} devmachine — ~/.local/bin on PATH"'
        blocks = {package: chunk.split("block: |", 1)[1] for package, chunk in every_task() if marker in chunk}
        self.assertGreater(len(blocks), 1)
        self.assertEqual(len(set(blocks.values())), 1, blocks)

    def test_dev_writes_that_block_the_same_way(self):
        dev = os.path.join(os.path.dirname(ROOT), "dev", "tasks", "main.yml")
        chunk = next(c for p, c in every_task() if p == "claude-code" and "~/.local/bin on PATH" in c)
        shared = chunk.split("block: |", 1)[1].rstrip()
        rendered = re.search(r"block: \|(.*?)\n  loop:", read(dev), re.S).group(1)
        self.assertEqual(rendered.replace("{{ devmachine_dev_path_dir[2:] }}", ".local/bin"), shared)


if __name__ == "__main__":
    unittest.main()
