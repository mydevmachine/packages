import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks", "main.yml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class AutoAttach(unittest.TestCase):
    def test_a_missing_tmux_never_ends_the_login(self):
        self.assertIn("command -v tmux >/dev/null 2>&1", read(TASKS))


class OldBlocks(unittest.TestCase):
    def test_the_blocks_the_workspace_package_now_writes_leave_zshenv(self):
        tasks = read(TASKS)
        for marker in ("# {mark} devmachine — workspace secrets", "# {mark} devmachine — package manager on PATH"):
            self.assertIn('- "' + marker + '"', tasks)
        self.assertIn("state: absent", tasks)
        self.assertNotIn("devmachine_zsh_path_prefix", tasks)


if __name__ == "__main__":
    unittest.main()
