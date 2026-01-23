"""
Scrape GWMC ward-wise corporator profile data and export as CSV/JSON.

Target page (ASP.NET WebForms):
  https://gwmc.gov.in/wardwise_profile.aspx

This command:
- Fetches the page
- Detects the ward dropdown <select>
- Iterates all ward options
- Posts back like WebForms to load ward details
- Extracts corporator name + localities (best-effort heuristics)

Usage:
  python manage.py scrape_gwmc_wards --out wards.csv
  python manage.py scrape_gwmc_wards --out wards.json --format json
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError


GWMC_WARDWISE_URL = "https://gwmc.gov.in/wardwise_profile.aspx"


@dataclass
class WardRow:
    ward_value: str
    ward_label: str
    corporator_name: str
    localities: List[str]


def _get_hidden_fields(soup: BeautifulSoup) -> Dict[str, str]:
    payload: Dict[str, str] = {}
    for inp in soup.select("input[type='hidden'][name]"):
        name = inp.get("name")
        if not name:
            continue
        payload[name] = inp.get("value", "")
    return payload


def _find_ward_select(soup: BeautifulSoup) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Returns (select_name, options[(value,label)]).
    Uses heuristics to find the ward dropdown.
    """
    candidates = soup.select("select")
    if not candidates:
        raise CommandError("No <select> elements found; page structure may have changed.")

    def score(sel) -> int:
        attrs = " ".join(
            [
                sel.get("id", ""),
                sel.get("name", ""),
                (sel.get("aria-label") or ""),
            ]
        ).lower()
        s = 0
        if "ward" in attrs:
            s += 5
        if "ddl" in attrs or "drop" in attrs:
            s += 1
        # Prefer selects with many numeric options
        opts = sel.select("option")
        nums = 0
        for o in opts:
            txt = (o.get_text() or "").strip()
            if re.fullmatch(r"\d{1,3}", txt):
                nums += 1
        s += min(nums, 10)
        return s

    ward_select = max(candidates, key=score)
    select_name = ward_select.get("name") or ward_select.get("id")
    if not select_name:
        raise CommandError("Ward dropdown found but has no name/id.")

    options: List[Tuple[str, str]] = []
    for opt in ward_select.select("option"):
        value = (opt.get("value") or "").strip()
        label = (opt.get_text() or "").strip()
        if not value or not label:
            continue
        # Skip placeholders
        if "select" in label.lower():
            continue
        options.append((value, label))

    if not options:
        raise CommandError("Ward dropdown found but no usable <option> items were parsed.")

    return select_name, options


def _extract_localities_and_corporator(soup: BeautifulSoup) -> Tuple[str, List[str]]:
    """
    Best-effort extraction based on common label patterns.
    If the site changes, this may need tuning.
    """
    text = soup.get_text("\n", strip=True)

    corporator = ""
    
    # Try to find corporator in table cells or labels
    # Look for labels/td elements that might contain the name
    for label in soup.find_all(["label", "td", "span", "div"]):
        label_text = label.get_text(strip=True)
        if not label_text:
            continue
        # Check if this looks like a corporator name field
        if re.search(r"corporator", label_text, re.IGNORECASE):
            # Get the next sibling or parent's next element
            next_elem = label.find_next(["td", "span", "div", "label"])
            if next_elem:
                name_text = next_elem.get_text(strip=True)
                if name_text and len(name_text) > 2 and len(name_text) < 100:
                    corporator = name_text
                    break
            # Or check parent's children
            parent = label.parent
            if parent:
                for child in parent.find_all(["td", "span", "div"]):
                    child_text = child.get_text(strip=True)
                    if child_text and child_text != label_text and len(child_text) > 2 and len(child_text) < 100:
                        if not re.search(r"(corporator|name|ward|localit)", child_text, re.IGNORECASE):
                            corporator = child_text
                            break
                if corporator:
                    break
    
    # Fallback: Common patterns: "Corporator Name : XYZ", "Name of Corporator: XYZ"
    if not corporator:
        corp_patterns = [
            r"Corporator\s*Name\s*[:\-]\s*(.+)",
            r"Name\s*of\s*Corporator\s*[:\-]\s*(.+)",
            r"Corporator\s*[:\-]\s*(.+)",
        ]
        for pat in corp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                corporator = m.group(1).strip()
                # trim at next label-like line
                corporator = corporator.split("\n")[0].strip()
                break

    # Localities often appear as a block/list/table; grab lines around "Localit"
    localities: List[str] = []
    loc_block = ""
    mloc = re.search(r"(Localit(?:y|ies).*)", text, re.IGNORECASE)
    if mloc:
        loc_block = mloc.group(1)

    # Fallback: look for <ul>/<ol> near any label containing Localit
    if not loc_block:
        label_el = None
        for el in soup.find_all(string=re.compile(r"Localit", re.IGNORECASE)):
            label_el = el
            break
        if label_el:
            parent = label_el.parent
            ul = parent.find_next(["ul", "ol"])
            if ul:
                for li in ul.select("li"):
                    t = li.get_text(" ", strip=True)
                    if t:
                        localities.append(t)

    # If still empty, parse from text block: split lines after "Localities"
    if not localities and loc_block:
        # Take the next ~30 lines after the match
        idx = text.lower().find(loc_block.lower())
        snippet = text[idx : idx + 4000]
        lines = [ln.strip(" :-\t") for ln in snippet.split("\n") if ln.strip()]
        # Remove the header line(s)
        cleaned = []
        for ln in lines:
            if re.search(r"localit", ln, re.IGNORECASE):
                continue
            cleaned.append(ln)
        # Heuristic: stop when we hit another section label
        stop_words = ["contact", "mobile", "phone", "address", "email", "ward", "division"]
        for ln in cleaned:
            low = ln.lower()
            if any(w in low for w in stop_words):
                break
            # split comma-separated
            parts = [p.strip() for p in re.split(r",|;|•|\u2022", ln) if p.strip()]
            for p in parts:
                if len(p) >= 2 and p not in localities:
                    localities.append(p)

    # De-dupe while preserving order
    seen = set()
    localities2: List[str] = []
    for l in localities:
        key = l.lower()
        if key in seen:
            continue
        seen.add(key)
        localities2.append(l)

    return corporator, localities2


class Command(BaseCommand):
    help = "Scrape GWMC wardwise_profile.aspx for all wards and export corporator/localities."

    def add_arguments(self, parser):
        parser.add_argument("--out", type=str, default="gwmc_wards.csv", help="Output file path")
        parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Output format")
        parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")

    def handle(self, *args, **options):
        out_path: str = options["out"]
        out_format: str = options["format"]
        timeout: int = options["timeout"]

        sess = requests.Session()
        sess.headers.update(
            {
                "User-Agent": "FixMyAreaBot/1.0 (+https://example.local)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        r = sess.get(GWMC_WARDWISE_URL, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        select_name, ward_options = _find_ward_select(soup)
        self.stdout.write(f"Detected ward dropdown: {select_name} with {len(ward_options)} options")

        rows: List[WardRow] = []

        # Base payload includes hidden fields
        base_payload = _get_hidden_fields(soup)

        # Some WebForms require __EVENTTARGET for the dropdown to trigger postback.
        event_target = select_name

        for i, (ward_value, ward_label) in enumerate(ward_options, start=1):
            payload = dict(base_payload)
            payload[event_target] = ward_value
            payload["__EVENTTARGET"] = event_target
            payload["__EVENTARGUMENT"] = ""
            # For UpdatePanel, we might need ScriptManager
            if "__ScriptManager" not in payload:
                # Try to find ScriptManager in the page
                script_mgr = soup.find("input", {"name": re.compile(r"ScriptManager", re.I)})
                if script_mgr:
                    payload[script_mgr.get("name")] = script_mgr.get("value", "")

            try:
                # ASP.NET UpdatePanel requires specific headers
                headers = {
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }
                pr = sess.post(GWMC_WARDWISE_URL, data=payload, headers=headers, timeout=timeout)
                pr.raise_for_status()
                
                # Check if response is UpdatePanel format (starts with numbers and pipes)
                response_text = pr.text
                if response_text.startswith(("1|", "0|")) and "|" in response_text[:10]:
                    # This is an UpdatePanel response - parse it
                    # Format: length|type|id|content|...
                    parts = response_text.split("|")
                    if len(parts) >= 4:
                        # Try to extract HTML from the UpdatePanel response
                        # The actual content might be in later parts
                        html_content = "|".join(parts[4:]) if len(parts) > 4 else response_text
                        # Sometimes UpdatePanel returns pageRedirect - need to handle that
                        if "pageRedirect" in response_text.lower():
                            # The page might require a different approach - try getting the page again after redirect
                            self.stdout.write(self.style.WARNING(f"Ward {ward_label}: UpdatePanel redirect detected"))
                            corporator, localities = "", []
                        else:
                            ward_soup = BeautifulSoup(html_content, "lxml")
                            corporator, localities = _extract_localities_and_corporator(ward_soup)
                    else:
                        ward_soup = BeautifulSoup(response_text, "lxml")
                        corporator, localities = _extract_localities_and_corporator(ward_soup)
                else:
                    # Regular HTML response
                    ward_soup = BeautifulSoup(response_text, "lxml")
                    corporator, localities = _extract_localities_and_corporator(ward_soup)
                
                # Debug: save first few pages to inspect structure
                if i <= 3:
                    with open(f"debug_ward_{ward_label}.html", "w", encoding="utf-8") as f:
                        f.write(response_text)
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing ward {ward_label}: {e}"))
                corporator, localities = "", []
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing ward {ward_label}: {e}"))
                corporator, localities = "", []

            rows.append(
                WardRow(
                    ward_value=ward_value,
                    ward_label=ward_label,
                    corporator_name=corporator,
                    localities=localities,
                )
            )

            # Update hidden fields for next postback (WebForms viewstate changes)
            base_payload = _get_hidden_fields(ward_soup)

            self.stdout.write(f"[{i}/{len(ward_options)}] {ward_label}: corporator='{corporator}' localities={len(localities)}")

        if out_format == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in rows], f, ensure_ascii=False, indent=2)
        else:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ward_value", "ward_label", "corporator_name", "localities"])
                for row in rows:
                    w.writerow([row.ward_value, row.ward_label, row.corporator_name, " | ".join(row.localities)])

        self.stdout.write(self.style.SUCCESS(f"Exported {len(rows)} wards to {out_path}"))

