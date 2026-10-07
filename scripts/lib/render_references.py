#!/usr/bin/env python3
"""Render the devmachine-skills reference copies from a devmachine-cli docs/ tree.

Invoked by sync-skill-references.sh. Not meant to be run standalone, but it is
a pure function of its inputs: same docs tree in, same bytes out, every time.
A file entry may name a "##" heading as a third field; then only that section
is copied.
"""
import posixpath
import re
import sys
from pathlib import Path

BASE_URL = "https://mydevmachine.sh"

# Each skill lists the docs it needs, as (docs-relative source path,
# references-relative destination path[, "##" heading]). With a heading, only
# that section of the page is copied. Order matters only for readability;
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
    "edit-devmachine-boards": [
        ("concepts/widgets.md", "concepts/widgets.md"),
        ("reference/widget-format.md", "widget-format.md"),
        ("reference/commands.md", "commands-widgets.md", "widgets"),
    ],
}

LINK_RE = re.compile(r"(\]\()([^)\s]+)(\))")
ANCHOR_RE = re.compile(r"(\]\()(#[^)\s]+)(\))")
FENCE_RE = re.compile(r"^(```|~~~)")


def slug(heading):
    """The anchor the site gives a heading: lower case, punctuation dropped,
    spaces to dashes."""
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return re.sub(r" +", "-", text)


def extract_section(text, heading):
    """The lines from "## <heading>" up to the next "## " heading outside a
    code fence, or the end of the page."""
    out, inside, fenced = [], False, False
    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            fenced = not fenced
        is_h2 = not fenced and line.startswith("## ")
        if is_h2 and inside:
            break
        if is_h2 and line[3:].strip() == heading:
            inside = True
        if inside:
            out.append(line)
    if not out:
        raise SystemExit(f"missing section: ## {heading}")
    return "".join(out)


def section_anchors(text):
    """Every anchor a copied section keeps: its own headings, outside fences."""
    anchors, fenced = set(), False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
        elif not fenced and line.startswith("#"):
            anchors.add(slug(line.lstrip("#")))
    return anchors


def split_anchor(target):
    if "#" in target:
        path, anchor = target.split("#", 1)
        return path, "#" + anchor
    return target, ""


def site_url(docs_path, anchor):
    return f"{BASE_URL}/{docs_path[: -len('.md')]}/{anchor}"


def rewrite_links(text, source_docs_path, copied_set, kept_anchors):
    """Points every relative link at its copy, or at the site when the page,
    or the part of it the anchor names, was not copied. kept_anchors maps a
    section copy's source onto the anchors it holds."""
    source_dir = posixpath.dirname(source_docs_path)

    def repl(match):
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        path, anchor = split_anchor(target)

        if not path.endswith(".md"):
            return match.group(0)
        if path.startswith(("http://", "https://")):
            return match.group(0)

        resolved = posixpath.normpath(posixpath.join(source_dir, path))
        partial = resolved in kept_anchors and anchor[1:] not in kept_anchors[resolved]
        if resolved not in copied_set or partial:
            return f"{prefix}{site_url(resolved, anchor)}{suffix}"

        dest_of_source = copied_set[source_docs_path]
        dest_of_target = copied_set[resolved]
        new_target = posixpath.relpath(dest_of_target, posixpath.dirname(dest_of_source) or ".")
        return f"{prefix}{new_target}{anchor}{suffix}"

    def anchor_repl(match):
        prefix, anchor, suffix = match.group(1), match.group(2), match.group(3)
        if source_docs_path in kept_anchors and anchor[1:] not in kept_anchors[source_docs_path]:
            return f"{prefix}{site_url(source_docs_path, anchor)}{suffix}"
        return match.group(0)

    return ANCHOR_RE.sub(anchor_repl, LINK_RE.sub(repl, text))


def render(docs_dir: Path, out_dir: Path, skills=SKILLS):
    for skill_name, files in skills.items():
        copied_set = {entry[0]: entry[1] for entry in files}
        texts, kept_anchors = {}, {}
        for entry in files:
            src = entry[0]
            source_path = docs_dir / src
            if not source_path.is_file():
                raise SystemExit(f"missing source doc: {source_path}")
            text = source_path.read_text(encoding="utf-8")
            if len(entry) == 3:
                text = extract_section(text, entry[2])
                kept_anchors[src] = section_anchors(text)
            texts[src] = text
        skill_out = out_dir / skill_name
        for entry in files:
            src, dest = entry[0], entry[1]
            rewritten = rewrite_links(texts[src], src, copied_set, kept_anchors)
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
