#!/usr/bin/env python3
"""Validate the static client demo without adding third-party dependencies."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo/ambiguous-payment"
REQUIRED_FILES = [
    DEMO / "index.html",
    DEMO / "styles.css",
    DEMO / "app.js",
    DEMO / "demo-data.json",
    DEMO / "README.md",
    DEMO / ".nojekyll",
]

REQUIRED_COPY = [
    "Did the payment fail",
    "or did only the response fail?",
    "ACCEPT_EXISTING_EFFECT",
    "Request a bounded test-mode verification",
    "deterministic provider-neutral demonstration",
    "does not prove external exactly-once behavior",
    "External companies are validation cases",
]

REQUIRED_EXTERNAL_LINKS = {
    "https://github.com/safal207/DI",
    "https://github.com/safal207/DI/blob/main/docs/case-study-ambiguous-payment-recovery.md",
    "https://github.com/safal207/DI/tree/main/evidence/ambiguous-payment-sandbox",
    "https://github.com/safal207/DI/blob/main/docs/commercial/paid-pilot-one-pager.md",
}


class DemoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.ids: set[str] = set()
        self.buttons: list[dict[str, str]] = []
        self.meta_names: set[str] = set()
        self.has_charset = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if "id" in data:
            self.ids.add(data["id"])
        if tag == "a":
            self.links.append(data)
        elif tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        elif tag == "link" and data.get("rel") == "stylesheet":
            self.stylesheets.append(data.get("href", ""))
        elif tag == "button":
            self.buttons.append(data)
        elif tag == "meta":
            if data.get("charset"):
                self.has_charset = True
            if data.get("name"):
                self.meta_names.add(data["name"])


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    html = (DEMO / "index.html").read_text(encoding="utf-8")
    css = (DEMO / "styles.css").read_text(encoding="utf-8")
    js = (DEMO / "app.js").read_text(encoding="utf-8")
    data = load_json(DEMO / "demo-data.json")
    summary = load_json(ROOT / "evidence/ambiguous-payment-sandbox/summary.json")
    mutation = load_json(ROOT / "evidence/ambiguous-payment-sandbox/mutation-report.json")

    parser = DemoHTMLParser()
    parser.feed(html)

    for fragment in REQUIRED_COPY:
        if fragment.lower() not in html.lower():
            errors.append(f"required copy missing: {fragment!r}")

    if not parser.has_charset:
        errors.append("HTML must declare a charset")
    if "viewport" not in parser.meta_names:
        errors.append("HTML must include a viewport meta tag")
    if parser.stylesheets != ["styles.css"]:
        errors.append(f"unexpected stylesheet dependencies: {parser.stylesheets!r}")
    if parser.scripts != ["app.js"]:
        errors.append(f"unexpected script dependencies: {parser.scripts!r}")

    expected_ids = {
        "demo",
        "path-safe",
        "path-risk",
        "timeline",
        "metrics",
        "replay-path",
        "evidence",
        "pilot",
    }
    missing_ids = sorted(expected_ids - parser.ids)
    if missing_ids:
        errors.append(f"missing interactive IDs: {missing_ids}")

    if any(button.get("type") != "button" for button in parser.buttons):
        errors.append("every button must use type=button")

    external_hrefs = {link.get("href", "") for link in parser.links if link.get("href", "").startswith("https://")}
    missing_links = sorted(REQUIRED_EXTERNAL_LINKS - external_hrefs)
    if missing_links:
        errors.append(f"missing evidence links: {missing_links}")

    for link in parser.links:
        href = link.get("href", "")
        if href.startswith("https://") and (link.get("target") != "_blank" or "noopener" not in link.get("rel", "")):
            errors.append(f"external link must use target=_blank and rel=noopener: {href}")
        if href.startswith("http://"):
            errors.append(f"insecure external link: {href}")

    mailto_links = [link.get("href", "") for link in parser.links if link.get("href", "").startswith("mailto:")]
    if not any(link.startswith("mailto:safal0645@gmail.com") for link in mailto_links):
        errors.append("client CTA mailto is missing")

    if "https://" in js or "http://" in js:
        errors.append("app.js must not depend on remote runtime resources")
    if "eval(" in js or "innerHTML = data" in js:
        errors.append("app.js contains a disallowed dynamic execution pattern")
    if "prefers-reduced-motion" not in css:
        errors.append("reduced-motion support is missing")
    if ":focus-visible" not in css:
        errors.append("focus-visible styling is missing")

    safe = data.get("paths", {}).get("safe", {})
    safe_metrics = {item["label"]: item["value"] for item in safe.get("metrics", [])}
    expected_metrics = {
        "Committed effects": str(summary["stored_effect_count"]),
        "Duplicate effects": str(summary["duplicate_effect_count"]),
        "Acknowledgement lost": "YES" if summary["acknowledgement_lost"] else "NO",
        "Authoritative state": str(summary["authoritative_commit_status"]).upper(),
        "Next action": str(summary["selected_next_action"]),
        "Unsafe mutations rejected": f"{mutation['mutations_rejected_as_expected']} / {mutation['mutation_count']}",
    }
    if safe_metrics != expected_metrics:
        errors.append(f"safe metrics drifted from canonical evidence: {safe_metrics!r}")

    if safe.get("verdict") != summary["conformance_status"]:
        errors.append("safe verdict must match canonical conformance status")
    if safe.get("next_action") != summary["selected_next_action"]:
        errors.append("safe next action must match canonical evidence")
    if summary.get("external_provider_used") is not False:
        errors.append("canonical demo source unexpectedly claims an external provider")

    unsafe = data.get("paths", {}).get("unsafe", {})
    if unsafe.get("verdict") != "RISK":
        errors.append("unsafe path must remain an illustrative RISK, not a measured FAIL")

    if re.search(r"\b(testimonial|trusted by|customers? served|partnered with)\b", html, re.IGNORECASE):
        errors.append("demo contains an unsupported social-proof claim")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print("PASS client demo structure, evidence binding, accessibility, and claim boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
