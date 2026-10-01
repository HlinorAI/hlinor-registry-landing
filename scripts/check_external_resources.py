#!/usr/bin/env python3
"""Guard: fail if a landing page loads any external subresource.

The page must have no third-party runtime dependency: styles and scripts are
vendored inline. Navigation links (<a href="https://...">) are fine — only
loaded resources are checked: script/link/img/iframe/source/video/audio via
src/href.

Exclusion: a genuine canonical link (<link rel="canonical">). Nothing else
carrying rel=canonical is exempt. Inline code, data: URIs and relative paths
are allowed.

Scope note: this is a deterministic guard for the tag/attribute set above, not
an exhaustive detector of all network activity (CSS @import inside inline
styles, fetch/XHR in inline JS, etc. are out of scope).

Usage:
    check_external_resources.py FILE [FILE ...]   # exit 1 on any finding
    check_external_resources.py --self-test       # run built-in probes
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser

CHECKED_TAGS = frozenset(
    {"script", "link", "img", "iframe", "source", "video", "audio"}
)


def is_external_url(value: str | None) -> bool:
    """Judge a raw attribute value the way a browser would load it.

    WHATWG URL parsing removes ASCII tab/newline characters anywhere and
    strips leading/trailing C0 controls and spaces, then treats "\\" like "/"
    in special URLs and collapses "https:/host" to "https://host". A guard
    that skips this normalization can be bypassed with "/\\host" or
    "https:/host".
    """
    if value is None:
        return False
    candidate = re.sub(r"[\x00-\x1f\x7f\s]", "", value)
    candidate = candidate.replace("\\", "/").lower()
    if candidate.startswith("//"):
        return True
    return bool(re.match(r"^https?:", candidate))


class ExternalResourceFinder(HTMLParser):
    """Collect external subresource references with line numbers."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.findings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in CHECKED_TAGS:
            return
        attrs = [(k.lower(), v) for k, v in attrs]
        # Exempt only a genuine canonical link: rel must be exactly the one
        # token "canonical". rel="canonical stylesheet" still loads a
        # resource and must be flagged.
        is_canonical_link = tag.lower() == "link" and any(
            k == "rel" and v is not None and {t.lower() for t in v.split()} == {"canonical"}
            for k, v in attrs
        )
        if is_canonical_link:
            return
        for name, value in attrs:
            if name not in ("src", "href"):
                continue
            if is_external_url(value):
                self.findings.append(
                    f"line {self.getpos()[0]}: <{tag.lower()}> {name}={value!r}"
                )


def check_html(text: str) -> list[str]:
    finder = ExternalResourceFinder()
    finder.feed(text)
    finder.close()
    return finder.findings


# (html, must_flag, label)
PROBES: list[tuple[str, bool, str]] = [
    # Claude's original three probes
    ('<script defer src="https://cdn.example.com/x.js"></script>', True, "defer+https script"),
    ('<img src="//cdn.example.com/pixel.png" alt="x">', True, "protocol-relative img"),
    ("<link rel='stylesheet' href='https://cdn.example.com/s.css'/>", True, "single-quoted https link"),
    # Additional variations the old grep guard missed or mis-scoped
    ('<script src="//cdn.example.com/y.js"></script>', True, "protocol-relative script"),
    ('<script type="text/javascript" async src="https://cdn.example.com/z.js"></script>', True, "reordered attributes"),
    ('<script\n  defer\n  src="https://cdn.example.com/m.js"></script>', True, "multiline tag"),
    ('<iframe src="https://cdn.example.com/frame"></iframe>', True, "iframe"),
    ('<source src="https://cdn.example.com/movie.mp4" type="video/mp4">', True, "source"),
    ('<video src="https://cdn.example.com/v.mp4"></video>', True, "video"),
    ('<audio src="https://cdn.example.com/a.mp3"></audio>', True, "audio"),
    ('<script rel="canonical" src="https://cdn.example.com/evil.js"></script>', True, "rel=canonical on non-link must NOT be exempt"),
    ('<IMG SRC="https://cdn.example.com/BIG.PNG" ALT="x">', True, "uppercase tag/attribute"),
    # R3a/R3b bypass probes (review round 2)
    ('<link rel="canonical stylesheet" href="https://cdn.example.com/x.css">', True, 'rel="canonical stylesheet" must NOT be exempt'),
    ('<img src="/\\cdn.example.com/pixel.png" alt="x">', True, "backslash protocol-relative img"),
    ('<script src="https:/cdn.example.com/y.js"></script>', True, "single-slash https URL"),
    ('<script src="HTTPS://cdn.example.com/z.js"></script>', True, "uppercase scheme"),
    # Negative cases: must stay allowed
    ('<link rel="canonical" href="https://registry.hlinor.com/" />', False, "genuine canonical link"),
    ('<link rel="icon" href="data:image/svg+xml,%3Csvg%3E%3C/svg%3E" />', False, "data: URI favicon"),
    ("<script>var inline = 1;</script>", False, "inline script"),
    ('<a href="https://github.com/HlinorAI/hlinor-agent-registry">GitHub</a>', False, "navigation link"),
    ('<script src="local.js"></script>', False, "relative path"),
]


def run_self_test() -> int:
    failures: list[str] = []
    for html, must_flag, label in PROBES:
        flagged = bool(check_html(html))
        if flagged != must_flag:
            failures.append(
                f"probe {label!r}: expected {'finding' if must_flag else 'clean'}, "
                f"got {'finding' if flagged else 'clean'}"
            )
    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 2
    print(f"self-test OK: {len(PROBES)} probes behave as expected")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if argv[0] == "--self-test":
        return run_self_test()
    total = 0
    for path in argv:
        with open(path, encoding="utf-8") as fh:
            findings = check_html(fh.read())
        if findings:
            print(f"{path}: external subresource(s) found:")
            for f in findings:
                print(f"  - {f}")
            total += 1
        else:
            print(f"{path}: no external subresources")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
