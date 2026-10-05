import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "files" / "hardware-guard"
loader = SourceFileLoader("hardware_guard", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("hardware_guard", loader)
hardware_guard = importlib.util.module_from_spec(spec)
sys.modules["hardware_guard"] = hardware_guard
loader.exec_module(hardware_guard)

m = hardware_guard
FIXTURES = Path(__file__).parent / "fixtures"


def config(**overrides):
    c = dict(m.DEFAULTS)
    c.update(overrides)
    return c


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ── Linux readings ──────────────────────────────────────────────────────

def laptop_sysfs(root):
    write(root, "class/thermal/thermal_zone0/type", "x86_pkg_temp\n")
    write(root, "class/thermal/thermal_zone0/temp", "42000\n")
    # An unused zone many laptops report as 0: not a temperature.
    write(root, "class/thermal/thermal_zone1/type", "SEN1\n")
    write(root, "class/thermal/thermal_zone1/temp", "0\n")
    write(root, "class/hwmon/hwmon0/name", "coretemp\n")
    write(root, "class/hwmon/hwmon0/temp1_input", "61500\n")
    write(root, "class/hwmon/hwmon0/temp1_label", "Package id 0\n")
    write(root, "class/power_supply/AC0/type", "Mains\n")
    write(root, "class/power_supply/AC0/online", "1\n")
    write(root, "class/power_supply/BAT0/type", "Battery\n")
    write(root, "class/power_supply/BAT0/status", "Not charging\n")
    write(root, "class/power_supply/BAT0/energy_now", "30000000\n")
    write(root, "class/power_supply/BAT0/energy_full", "40000000\n")
    write(root, "class/power_supply/BAT0/temp", "312\n")
    write(root, "class/power_supply/BAT0/charge_control_end_threshold", "100\n")


def test_linux_sensors_skip_implausible_zones(tmp_path):
    laptop_sysfs(tmp_path)
    sensors = m.linux_sensors(str(tmp_path))
    assert [(s["name"], s["label"], s["celsius"]) for s in sensors] == [
        ("x86_pkg_temp", "", 42.0),
        ("coretemp", "Package id 0", 61.5),
    ]


def test_linux_battery(tmp_path):
    laptop_sysfs(tmp_path)
    b = m.linux_battery(str(tmp_path))
    assert b["percent"] == 75
    assert b["celsius"] == 31.2
    assert b["status"] == "Not charging"
    assert b["charge_limit"] == 100
    assert b["external_power"] is True
    assert b["charge_limit_path"].endswith("BAT0/charge_control_end_threshold")


def test_linux_without_battery(tmp_path):
    write(tmp_path, "class/thermal/thermal_zone0/type", "cpu-thermal\n")
    write(tmp_path, "class/thermal/thermal_zone0/temp", "36000\n")
    assert m.linux_battery(str(tmp_path)) is None
    assert m.linux_sensors(str(tmp_path))[0]["celsius"] == 36.0


def test_apply_charge_limit(tmp_path):
    laptop_sysfs(tmp_path)
    b = m.linux_battery(str(tmp_path))
    m.apply_charge_limit(b, 60)
    assert (tmp_path / "class/power_supply/BAT0/charge_control_end_threshold").read_text() == "60"


def test_apply_charge_limit_from_a_float_setting(tmp_path):
    laptop_sysfs(tmp_path)
    m.apply_charge_limit(m.linux_battery(str(tmp_path)), 60.0)
    assert (tmp_path / "class/power_supply/BAT0/charge_control_end_threshold").read_text() == "60"


def test_apply_charge_limit_zero_leaves_it(tmp_path):
    laptop_sysfs(tmp_path)
    m.apply_charge_limit(m.linux_battery(str(tmp_path)), 0)
    assert (tmp_path / "class/power_supply/BAT0/charge_control_end_threshold").read_text() == "100\n"


# ── macOS readings ──────────────────────────────────────────────────────

def test_parse_ioreg_battery_apple_silicon():
    b = m.parse_ioreg_battery((FIXTURES / "ioreg-apple-silicon.xml").read_text())
    assert b["percent"] == 80
    assert b["celsius"] == 30.5
    assert b["status"] == "Charging"
    assert b["external_power"] is True


def test_parse_ioreg_battery_intel_reports_mah():
    b = m.parse_ioreg_battery((FIXTURES / "ioreg-intel.xml").read_text())
    assert b["percent"] == 50


def test_parse_ioreg_without_battery():
    assert m.parse_ioreg_battery('<?xml version="1.0"?><plist version="1.0"><array/></plist>') is None
    assert m.parse_ioreg_battery("not xml") is None


def test_parse_pmset_therm():
    assert m.parse_pmset_therm((FIXTURES / "pmset-therm-limited.txt").read_text()) == 70
    assert m.parse_pmset_therm("Note: No thermal warning level has been recorded\n") is None


# ── decisions ───────────────────────────────────────────────────────────

def r(hottest=None, battery_celsius=None, speed_limit=None):
    battery = {"celsius": battery_celsius, "percent": 80, "status": "Charging"} if battery_celsius else None
    return {"sensors": [], "hottest_celsius": hottest, "battery": battery, "cpu_speed_limit": speed_limit}


def kinds(actions):
    return [a["kind"] for a in actions]


def test_cool_machine_only_sends_the_first_heartbeat():
    state = {}
    assert kinds(m.decide(r(40), config(), state, 1000)) == ["heartbeat"]
    assert kinds(m.decide(r(40), config(), state, 1060)) == []


def test_heartbeat_off():
    assert m.decide(r(40), config(heartbeat_hours=0), {}, 1000) == []


def test_heartbeat_repeats_after_the_interval():
    state = {}
    m.decide(r(40), config(heartbeat_hours=24), state, 0)
    assert kinds(m.decide(r(40), config(heartbeat_hours=24), state, 24 * 3600)) == ["heartbeat"]


def test_warning_is_rate_limited_and_recovers():
    c = config(heartbeat_hours=0, warn_celsius=75, repeat_minutes=30)
    state = {}
    assert kinds(m.decide(r(78), c, state, 0)) == ["alert"]
    assert kinds(m.decide(r(79), c, state, 60)) == []
    assert kinds(m.decide(r(79), c, state, 30 * 60)) == ["alert"]
    # Just under the line is not "back to normal" yet.
    assert kinds(m.decide(r(73), c, state, 31 * 60)) == []
    assert kinds(m.decide(r(69), c, state, 32 * 60)) == ["recovered"]
    assert kinds(m.decide(r(60), c, state, 33 * 60)) == []


def test_shutdown_needs_the_limit_to_hold():
    c = config(heartbeat_hours=0, warn_celsius=75, shutdown_celsius=85, sustain_seconds=120)
    state = {}
    assert kinds(m.decide(r(90), c, state, 0)) == ["alert"]
    assert kinds(m.decide(r(90), c, state, 60)) == []
    assert kinds(m.decide(r(90), c, state, 120)) == ["shutdown"]
    assert state["tripped"] == {"cpu": 120}
    # Announced once per episode.
    assert kinds(m.decide(r(90), c, state, 180)) == []


def test_a_spike_resets_the_clock():
    c = config(heartbeat_hours=0, warn_celsius=75, shutdown_celsius=85, sustain_seconds=120)
    state = {}
    m.decide(r(90), c, state, 0)
    m.decide(r(80), c, state, 60)
    assert "shutdown" not in kinds(m.decide(r(90), c, state, 130))
    assert "shutdown" in kinds(m.decide(r(90), c, state, 250))


def test_cooling_down_clears_the_trip():
    c = config(heartbeat_hours=0, warn_celsius=75, shutdown_celsius=85, sustain_seconds=0)
    state = {}
    m.decide(r(90), c, state, 0)
    assert state["tripped"]
    m.decide(r(60), c, state, 60)
    assert state["tripped"] == {}


def test_battery_has_its_own_limits():
    c = config(heartbeat_hours=0, battery_warn_celsius=45, battery_shutdown_celsius=50, sustain_seconds=0)
    actions = m.decide(r(40, battery_celsius=52), c, {}, 0)
    assert kinds(actions) == ["shutdown", "alert"]
    assert actions[0]["message"].startswith("Battery at 52°C")


def test_macos_throttle_alerts_and_recovers():
    c = config(heartbeat_hours=0)
    state = {}
    assert kinds(m.decide(r(speed_limit=70), c, state, 0)) == ["alert"]
    assert kinds(m.decide(r(speed_limit=70), c, state, 60)) == []
    assert kinds(m.decide(r(speed_limit=100), c, state, 120)) == ["recovered"]


def test_no_sensors_is_not_an_alert():
    assert m.decide(r(), config(heartbeat_hours=0), {}, 0) == []


def test_summary():
    text = m.summary(r(41.6, battery_celsius=30.0))
    assert text == "Running: hottest 42°C; battery 80%, 30°C, charging."
    assert m.summary(r()) == "Running: no sensors readable."


# ── configuration ───────────────────────────────────────────────────────

def test_load_config_coerces_types(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"warn_celsius": "75", "shutdown": "False", "sustain_seconds": "x"}))
    c = m.load_config(str(path))
    assert c["warn_celsius"] == 75.0
    assert c["shutdown"] is False
    assert c["sustain_seconds"] == m.DEFAULTS["sustain_seconds"]


def test_load_config_missing_file_gives_defaults(tmp_path):
    c = m.load_config(str(tmp_path / "absent.json"))
    assert c["shutdown"] is True
    assert c["notify_url"] == ""


# ── check, end to end without side effects ──────────────────────────────

def test_check_with_shutdown_off_never_powers_off(tmp_path, monkeypatch):
    laptop_sysfs(tmp_path)
    write(tmp_path, "class/hwmon/hwmon0/temp1_input", "95000\n")
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"shutdown": False, "sustain_seconds": 0, "heartbeat_hours": 0}))
    sent, powered = [], []
    monkeypatch.setattr(m, "is_macos", lambda: False)
    monkeypatch.setattr(m, "notify", lambda url, kind, message: sent.append((kind, message)) or True)
    monkeypatch.setattr(m, "power_off", lambda: powered.append(True))
    monkeypatch.setenv("HARDWARE_GUARD_CONFIG", str(cfg))
    monkeypatch.setenv("HARDWARE_GUARD_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("HARDWARE_GUARD_SYSFS", str(tmp_path))
    assert m.main(["check"]) == 0
    assert powered == []
    assert any("Shutdown is off" in message for _, message in sent)


def test_check_powers_off_while_tripped(tmp_path, monkeypatch):
    laptop_sysfs(tmp_path)
    write(tmp_path, "class/hwmon/hwmon0/temp1_input", "95000\n")
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"sustain_seconds": 0, "heartbeat_hours": 0}))
    sent, powered = [], []
    monkeypatch.setattr(m, "is_macos", lambda: False)
    monkeypatch.setattr(m, "notify", lambda url, kind, message: sent.append(kind) or True)
    monkeypatch.setattr(m, "power_off", lambda: powered.append(True))
    monkeypatch.setenv("HARDWARE_GUARD_CONFIG", str(cfg))
    monkeypatch.setenv("HARDWARE_GUARD_STATE", str(tmp_path / "state.json"))
    monkeypatch.setenv("HARDWARE_GUARD_SYSFS", str(tmp_path))
    m.main(["check"])
    m.main(["check"])
    assert powered == [True, True]
    assert sent.count("shutdown") == 1


def test_notify_posts_one_json_event(monkeypatch):
    sent = []

    class Done:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(request, timeout):
        sent.append(request)
        return Done()

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.socket, "gethostname", lambda: "home")
    assert m.notify("https://example.com/hook", "alert", "Hottest sensor at 81°C.") is True
    body = json.loads(sent[0].data)
    assert body == {"host": "home", "kind": "alert", "message": "Hottest sensor at 81°C."}
    assert sent[0].get_header("Content-type") == "application/json"


def test_notify_without_url_only_logs():
    assert m.notify("", "alert", "x") is False
