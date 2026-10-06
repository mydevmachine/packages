import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parent.parent / "files" / "devmachine-caddy-logs"
loader = SourceFileLoader("devmachine_caddy_logs", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("devmachine_caddy_logs", loader)
devmachine_caddy_logs = importlib.util.module_from_spec(spec)
sys.modules["devmachine_caddy_logs"] = devmachine_caddy_logs
loader.exec_module(devmachine_caddy_logs)


@pytest.fixture(autouse=True)
def on_linux(monkeypatch):
    monkeypatch.setattr(devmachine_caddy_logs.platform, "system", lambda: "Linux")


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_prints_journalctl_output(monkeypatch, capsys):
    m = devmachine_caddy_logs
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FakeResult(stdout="line one\nline two\n")

    monkeypatch.setattr(m.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["devmachine-caddy-logs", "--lines", "50"])
    assert m.main() == 0
    assert calls[0] == ["journalctl", "-u", "caddy", "-n", "50", "--no-pager"]
    assert capsys.readouterr().out == "line one\nline two\n"


def test_default_line_count(monkeypatch):
    m = devmachine_caddy_logs
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FakeResult(stdout="")

    monkeypatch.setattr(m.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["devmachine-caddy-logs"])
    m.main()
    assert calls[0] == ["journalctl", "-u", "caddy", "-n", "200", "--no-pager"]


def test_reports_a_failed_journalctl(monkeypatch, capsys):
    m = devmachine_caddy_logs

    def fake_run(cmd, **kwargs):
        return FakeResult(returncode=1, stderr="Unit caddy.service not found.")

    monkeypatch.setattr(m.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["devmachine-caddy-logs"])
    assert m.main() == 1
    assert "not found" in capsys.readouterr().err


def test_journalctl_missing(monkeypatch, capsys):
    m = devmachine_caddy_logs

    def fake_run(cmd, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(m.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["devmachine-caddy-logs"])
    assert m.main() == 1
    assert "journalctl" in capsys.readouterr().err


def test_a_mac_has_no_caddy_journal(monkeypatch, capsys):
    m = devmachine_caddy_logs

    def fake_run(cmd, **kwargs):
        raise AssertionError("journalctl must not run on a Mac")

    monkeypatch.setattr(m.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(m.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["devmachine-caddy-logs"])
    assert m.main() == 0
    assert capsys.readouterr().out == "-- No entries --\n"
