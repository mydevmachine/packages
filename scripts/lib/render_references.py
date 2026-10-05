#!/usr/bin/env python3
"""Render the devmachine-skills reference copies from a devmachine-cli docs/ tree.

Invoked by sync-skill-references.sh. Not meant to be run standalone, but it is
a pure function of its inputs: same docs tree in, same bytes out, every time.
"""
import posixpath
import re
import sys
from pathlib import Path

BASE_URL = "https://mydevmachine.sh"

# Each skill lists the docs it needs, as (docs-relative source path,
# references-relative destination path). Order matters only for readability;
# output is identical regardless of order.
SKILLS = {
    "use-devmachine": [
        ("reference/commands.md", "commands.md"),
        ("reference/settings.md", "settings.md"),
        ("troubleshooting.md", "troubleshooting.md"),
        ("concepts/agent-skills.md", "concepts/agent-skills.md"),
        ("concepts/configuration.md", "concepts/configuration.md"),
        ("concepts/credentials.md", "concepts/credentials.md"),
        ("concepts/dns.md", "concepts/dns.md"),
        ("concepts/machines-and-workspaces.md", "concepts/machines-and-workspaces.md"),
        ("concepts/packages.md", "concepts/packages.md"),
        ("concepts/publishing.md", "concepts/publishing.md"),
        ("how-it-works/what-a-machine-needs.md", "what-a-machine-needs.md"),
    ],
    "create-devmachine-package": [
        ("reference/package-format.md", "package-format.md"),
        ("reference/dns-provider-contract.md", "dns-provider-contract.md"),
        ("concepts/packages.md", "concepts/packages.md"),
        ("how-it-works/packages-on-many-systems.md", "multi-os.md"),
    ],
}

LINK_RE = re.compile(r"(\]\()([^)\s]+)(\))")


def split_anchor(target):
    if "#" in target:
        path, anchor = target.split("#", 1)
        return path, "#" + anchor
    return target, ""


def rewrite_links(text, source_docs_path, copied_set):
    source_dir = posixpath.dirname(source_docs_path)

    def repl(match):
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        path, anchor = split_anchor(target)

        if not path.endswith(".md"):
            return match.group(0)
        if path.startswith(("http://", "https://")):
            return match.group(0)

        resolved = posixpath.normpath(posixpath.join(source_dir, path))

        if resolved in copied_set:
            dest_of_source = copied_set[source_docs_path]
            dest_of_target = copied_set[resolved]
            new_target = posixpath.relpath(
                dest_of_target, posixpath.dirname(dest_of_source) or "."
            )
        else:
            without_ext = resolved[: -len(".md")]
            new_target = f"{BASE_URL}/{without_ext}/{anchor}"
            return f"{prefix}{new_target}{suffix}"

        return f"{prefix}{new_target}{anchor}{suffix}"

    return LINK_RE.sub(repl, text)


def render(docs_dir: Path, out_dir: Path):
    for skill_name, files in SKILLS.items():
        copied_set = {src: dest for src, dest in files}
        skill_out = out_dir / skill_name
        for src, dest in files:
            source_path = docs_dir / src
            if not source_path.is_file():
                raise SystemExit(f"missing source doc: {source_path}")
            text = source_path.read_text(encoding="utf-8")
            rewritten = rewrite_links(text, src, copied_set)
            dest_path = skill_out / dest
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(rewritten, encoding="utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_references.py <docs-dir> <out-dir>")
    docs_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    render(docs_dir, out_dir)


if __name__ == "__main__":
    main()
