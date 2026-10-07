import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "files" / "devmachine-stats"
loader = SourceFileLoader("devmachine_stats", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("devmachine_stats", loader)
devmachine_stats = importlib.util.module_from_spec(spec)
sys.modules["devmachine_stats"] = devmachine_stats
loader.exec_module(devmachine_stats)


def fake_run(table):
    def _run(cmd, timeout=10):
        return table[cmd[0]]
    return _run


def test_owner_from_home():
    m = devmachine_stats
    assert m.owner_from_home("/home/alice/compose") == "alice"
    assert m.owner_from_home("/home/alice") == "alice"
    assert m.owner_from_home("/opt/compose") is None
    assert m.owner_from_home("") is None


def test_read_memory_and_swap(monkeypatch):
    m = devmachine_stats
    free_output = (
        "              total        used        free      shared  buff/cache   available\n"
        "Mem:     8589934592  4294967296  1073741824    16777216  3221225472  4160749568\n"
        "Swap:    2147483648   104857600  2042626048\n"
    )
    monkeypatch.setattr(m, "run", fake_run({"free": (True, free_output, None)}))
    memory, swap = m.read_memory_and_swap([])
    assert memory == {
        "total_bytes": 8589934592,
        "used_bytes": 4294967296,
        "available_bytes": 4160749568,
    }
    assert swap == {"total_bytes": 2147483648, "used_bytes": 104857600}


def test_read_memory_and_swap_missing_tool(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", fake_run({"free": (False, "", None)}))
    errors = []
    memory, swap = m.read_memory_and_swap(errors)
    assert memory == {"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}
    assert swap == {"total_bytes": 0, "used_bytes": 0}
    assert errors == ["free: not found"]


def test_read_disk(monkeypatch):
    m = devmachine_stats
    df_output = "     used       avail      pcent\n1073741824  8589934592   11%\n"
    monkeypatch.setattr(m, "run", fake_run({"df": (True, df_output, None)}))
    disk = m.read_disk([])
    assert disk == {
        "path": "/",
        "used_bytes": 1073741824,
        "available_bytes": 8589934592,
        "used_percent": 11,
    }


def test_read_load(monkeypatch, tmp_path):
    m = devmachine_stats
    loadavg = tmp_path / "loadavg"
    loadavg.write_text("0.52 0.58 0.59 2/812 12345\n")
    real_open = open
    monkeypatch.setattr("builtins.open", lambda *a, **k: real_open(str(loadavg), encoding="utf-8"))
    load = m.read_load([])
    assert load == {"load1": 0.52, "load5": 0.58, "load15": 0.59}


def test_parse_size():
    m = devmachine_stats
    assert m.parse_size("12.34MiB") == int(12.34 * 1024**2)
    assert m.parse_size("512KiB") == 512 * 1024
    assert m.parse_size("1.5GiB") == int(1.5 * 1024**3)
    assert m.parse_size("garbage") == 0


def test_read_docker(monkeypatch):
    m = devmachine_stats
    stats_out = "web|12.3MiB / 1.943GiB|1.50%\ndb|256MiB / 512MiB|0.00%\n"
    ps_out = "web|/home/alice/compose\ndb|\n"

    def run_stub(cmd, timeout=10):
        if cmd[:2] == ["docker", "stats"]:
            return True, stats_out, None
        if cmd[:2] == ["docker", "ps"]:
            return True, ps_out, None
        raise AssertionError("unexpected command: %r" % cmd)

    monkeypatch.setattr(m, "run", run_stub)
    docker = m.read_docker([])
    assert docker["available"] is True
    assert docker["containers"] == [
        {
            "name": "web",
            "mem_used_bytes": m.parse_size("12.3MiB"),
            "mem_limit_bytes": m.parse_size("1.943GiB"),
            "cpu_percent": 1.5,
            "owner": "alice",
        },
        {
            "name": "db",
            "mem_used_bytes": m.parse_size("256MiB"),
            "mem_limit_bytes": m.parse_size("512MiB"),
            "cpu_percent": 0.0,
            "owner": None,
        },
    ]


def test_read_docker_not_installed(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", fake_run({"docker": (False, "", None)}))
    errors = []
    docker = m.read_docker(errors)
    assert docker == {"available": False, "containers": []}
    assert errors == []


def test_read_users(monkeypatch):
    m = devmachine_stats
    ps_out = "alice 1024\nbob 4096\nalice 2048\n"
    monkeypatch.setattr(m, "run", fake_run({"ps": (True, ps_out, None)}))
    users = m.read_users([])
    assert users == [
        {"user": "bob", "rss_bytes": 4096 * 1024},
        {"user": "alice", "rss_bytes": 3072 * 1024},
    ]


def test_published_ports_single_and_range():
    m = devmachine_stats
    assert m.published_ports("0.0.0.0:8810->80/tcp, [::]:8810->80/tcp") == {8810}
    assert m.published_ports("0.0.0.0:9000-9001->9000-9001/tcp") == {9000, 9001}
    assert m.published_ports("not a mapping") == set()


def test_listening_port_and_first_pid():
    m = devmachine_stats
    line = 'LISTEN 0 4096 *:22 *:* users:(("sshd",pid=123,fd=3))'
    assert m.listening_port(line) == 22
    assert m.first_pid(line) == 123
    assert m.listening_port("too short") is None
    assert m.first_pid("no pid here") is None


def test_read_ports_container_wins_over_process(monkeypatch):
    m = devmachine_stats

    def run_stub(cmd, timeout=10):
        if cmd[:2] == ["docker", "ps"]:
            return True, "web|/home/alice/compose|0.0.0.0:8810->80/tcp\n", None
        if cmd[:2] == ["ps", "-eo"]:
            return True, "100 root\n", None
        if cmd[:1] == ["ss"]:
            return True, 'LISTEN 0 4096 *:8810 *:* users:(("docker-proxy",pid=100,fd=3))\n', None
        raise AssertionError("unexpected command: %r" % cmd)

    monkeypatch.setattr(m, "run", run_stub)
    ports = m.read_ports([])
    assert ports == [{"port": 8810, "owner": "alice"}]


def test_read_ports_falls_back_to_process_owner(monkeypatch):
    m = devmachine_stats

    def run_stub(cmd, timeout=10):
        if cmd[:2] == ["docker", "ps"]:
            return True, "", None
        if cmd[:2] == ["ps", "-eo"]:
            return True, "555 bob\n", None
        if cmd[:1] == ["ss"]:
            return True, 'LISTEN 0 4096 *:5432 *:* users:(("postgres",pid=555,fd=3))\n', None
        raise AssertionError("unexpected command: %r" % cmd)

    monkeypatch.setattr(m, "run", run_stub)
    ports = m.read_ports([])
    assert ports == [{"port": 5432, "owner": "bob"}]


def test_collect_never_fails_when_every_tool_is_missing(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", lambda cmd, timeout=10: (False, "", None))
    doc = m.collect()
    assert doc["memory"] == {"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}
    assert doc["docker"] == {"available": False, "containers": []}
    assert doc["ports"] == []
    assert isinstance(doc["errors"], list)
    assert "collected_at" in doc


VM_STAT_OUTPUT = (
    "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
    "Pages free:                                6624.\n"
    "Pages active:                            484660.\n"
    "Pages inactive:                          482131.\n"
    "Pages speculative:                         2284.\n"
    "Pages throttled:                              0.\n"
    "Pages wired down:                        268583.\n"
    "Pages purgeable:                          15582.\n"
    '"Translation faults":               65678077727.\n'
    "File-backed pages:                       252182.\n"
    "Anonymous pages:                         716893.\n"
    "Pages stored in compressor:             2323554.\n"
    "Pages occupied by compressor:            286086.\n"
)


def test_owner_from_home_on_macos():
    m = devmachine_stats
    assert m.owner_from_home("/Users/alice/compose") == "alice"
    assert m.owner_from_home("/Users/") is None


def test_read_memory_and_swap_darwin(monkeypatch):
    m = devmachine_stats

    def run_stub(cmd, timeout=10):
        if cmd == ["sysctl", "-n", "hw.memsize"]:
            return True, "25769803776\n", None
        if cmd == ["vm_stat"]:
            return True, VM_STAT_OUTPUT, None
        if cmd == ["sysctl", "-n", "vm.swapusage"]:
            return True, "total = 2048.00M  used = 1024.50M  free = 1023.50M  (encrypted)\n", None
        raise AssertionError("unexpected command: %r" % cmd)

    monkeypatch.setattr(m, "run", run_stub)
    errors = []
    memory, swap = m.read_memory_and_swap_darwin(errors)
    used = (716893 - 15582 + 268583 + 286086) * 16384
    assert memory == {
        "total_bytes": 25769803776,
        "used_bytes": used,
        "available_bytes": 25769803776 - used,
    }
    assert swap == {"total_bytes": 2048 * 1024**2, "used_bytes": int(1024.5 * 1024**2)}
    assert errors == []


def test_read_memory_darwin_without_anonymous_pages_counts_active(monkeypatch):
    m = devmachine_stats
    older = "\n".join(l for l in VM_STAT_OUTPUT.splitlines() if not l.startswith("Anonymous"))

    def run_stub(cmd, timeout=10):
        if cmd == ["sysctl", "-n", "hw.memsize"]:
            return True, "25769803776\n", None
        if cmd == ["vm_stat"]:
            return True, older, None
        return True, "total = 0.00M  used = 0.00M  free = 0.00M\n", None

    monkeypatch.setattr(m, "run", run_stub)
    memory, swap = m.read_memory_and_swap_darwin([])
    assert memory["used_bytes"] == (484660 + 268583 + 286086) * 16384
    assert swap == {"total_bytes": 0, "used_bytes": 0}


def test_read_memory_and_swap_darwin_missing_tools(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", lambda cmd, timeout=10: (False, "", None))
    errors = []
    memory, swap = m.read_memory_and_swap_darwin(errors)
    assert memory == {"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}
    assert swap == {"total_bytes": 0, "used_bytes": 0}
    assert errors == ["sysctl: not found"]


def test_read_disk_darwin(monkeypatch):
    m = devmachine_stats
    df_output = (
        "Filesystem   1024-blocks      Used Available Capacity iused      ifree %iused  Mounted on\n"
        "/dev/disk3s1   482797652 228300500 203498492    53% 3649589 2034984920    0%   /System/Volumes/Data\n"
    )
    seen = []

    def run_stub(cmd, timeout=10):
        seen.append(cmd)
        return True, df_output, None

    monkeypatch.setattr(m, "run", run_stub)
    monkeypatch.setattr(m.os.path, "isdir", lambda p: p == "/System/Volumes/Data")
    disk = m.read_disk_darwin([])
    assert seen == [["df", "-k", "/System/Volumes/Data"]]
    assert disk == {
        "path": "/System/Volumes/Data",
        "used_bytes": 228300500 * 1024,
        "available_bytes": 203498492 * 1024,
        "used_percent": 53,
    }


def test_read_load_darwin(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", fake_run({"sysctl": (True, "{ 2.01 2.74 3.63 }\n", None)}))
    assert m.read_load_darwin([]) == {"load1": 2.01, "load5": 2.74, "load15": 3.63}


def test_read_ports_darwin(monkeypatch):
    m = devmachine_stats
    lsof_out = (
        "p571\nLalice\nf8\nn*:7000\nf9\nn*:7000\n"
        "p615\nLbob\nf4\nn127.0.0.1:5432\nf5\nn[::1]:5432\n"
        "p700\nLroot\nf3\nn*:8810\n"
    )

    def run_stub(cmd, timeout=10):
        if cmd[:2] == ["docker", "ps"]:
            return True, "web|/Users/alice/compose|0.0.0.0:8810->80/tcp\n", None
        if cmd[0] == "lsof":
            return True, lsof_out, None
        raise AssertionError("unexpected command: %r" % cmd)

    monkeypatch.setattr(m, "run", run_stub)
    assert m.read_ports_darwin([]) == [
        {"port": 5432, "owner": "bob"},
        {"port": 7000, "owner": "alice"},
        {"port": 8810, "owner": "alice"},
    ]


def test_read_ports_darwin_nothing_listening(monkeypatch):
    m = devmachine_stats

    def run_stub(cmd, timeout=10):
        if cmd[0] == "docker":
            return False, "", None
        return False, "", "lsof: exit 1"

    monkeypatch.setattr(m, "run", run_stub)
    errors = []
    assert m.read_ports_darwin(errors) == []
    assert errors == []


def test_collect_on_darwin_has_the_linux_shape(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", lambda cmd, timeout=10: (False, "", None))
    darwin = m.collect("Darwin")
    linux = m.collect("Linux")
    assert list(darwin) == list(linux)
    for key in ("memory", "swap", "disk", "load", "docker"):
        assert list(darwin[key]) == list(linux[key])


PACKAGE_YML = Path(__file__).parent.parent / "package.yml"

PY_TYPES = {"string": str, "number": (int, float), "bool": bool, "list": list, "object": dict}


def declared_returns(provider):
    """The returns of one provider, read from package.yml's flow mapping
    `returns: {a: t, b: t}` under `providers.<provider>`, without a YAML
    library: CI's Python has none."""
    lines = PACKAGE_YML.read_text().splitlines()
    start = lines.index("providers:")
    inside = False
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break
        if line.strip() == provider + ":":
            inside = True
            continue
        if inside and line.strip().startswith("returns:"):
            body = line.split("{", 1)[1].rsplit("}", 1)[0]
            return {k.strip(): v.strip() for k, v in (pair.split(":", 1) for pair in body.split(","))}
    raise AssertionError("no returns for provider %s in package.yml" % provider)


def test_stats_answer_matches_the_declared_provider(monkeypatch):
    m = devmachine_stats
    monkeypatch.setattr(m, "run", lambda cmd, timeout=10: (False, "", None))
    answer = m.collect(system="Linux")
    returns = declared_returns("stats")
    assert set(answer) == set(returns)
    for field, kind in returns.items():
        optional = kind.endswith("?")
        value = answer[field]
        if optional and value is None:
            continue
        assert isinstance(value, PY_TYPES[kind.rstrip("?")]), (field, kind, value)
