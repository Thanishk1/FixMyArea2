"""
Scrape GWMC ward-wise corporator profile using Selenium (handles JavaScript/UpdatePanel).

This version uses Selenium to properly handle ASP.NET UpdatePanel AJAX calls.

Usage:
  python manage.py scrape_gwmc_wards_selenium --out wards.csv
"""

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


GWMC_WARDWISE_URL = "https://gwmc.gov.in/wardwise_profile.aspx"


@dataclass
class WardRow:
    ward_value: str
    ward_label: str
    corporator_name: str
    localities: List[str]


def _extract_localities_and_corporator(soup: BeautifulSoup) -> Tuple[str, List[str]]:
    """Extract corporator name and localities from the page."""
    text = soup.get_text("\n", strip=True)

    corporator = ""
    localities: List[str] = []

    # Try to find corporator in table cells or labels
    for label in soup.find_all(["label", "td", "span", "div", "p"]):
        label_text = label.get_text(strip=True)
        if not label_text:
            continue
        
        # Check if this looks like a corporator name field
        if re.search(r"corporator", label_text, re.IGNORECASE):
            # Get the next sibling or parent's next element
            next_elem = label.find_next(["td", "span", "div", "label", "p"])
            if next_elem:
                name_text = next_elem.get_text(strip=True)
                if name_text and len(name_text) > 2 and len(name_text) < 100:
                    if not re.search(r"(corporator|name|ward|localit|select)", name_text, re.IGNORECASE):
                        corporator = name_text
                        break
            # Or check parent's children
            parent = label.parent
            if parent:
                for child in parent.find_all(["td", "span", "div", "p"]):
                    child_text = child.get_text(strip=True)
                    if child_text and child_text != label_text and len(child_text) > 2 and len(child_text) < 100:
                        if not re.search(r"(corporator|name|ward|localit|select)", child_text, re.IGNORECASE):
                            corporator = child_text
                            break
                if corporator:
                    break

    # Fallback: regex patterns
    if not corporator:
        corp_patterns = [
            r"Corporator\s*Name\s*[:\-]\s*(.+)",
            r"Name\s*of\s*Corporator\s*[:\-]\s*(.+)",
            r"Corporator\s*[:\-]\s*(.+)",
        ]
        for pat in corp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                corporator = m.group(1).strip().split("\n")[0].strip()
                break

    # Extract localities
    loc_block = ""
    mloc = re.search(r"(Localit(?:y|ies).*)", text, re.IGNORECASE)
    if mloc:
        loc_block = mloc.group(1)

    # Look for lists
    if not loc_block:
        for el in soup.find_all(string=re.compile(r"Localit", re.IGNORECASE)):
            parent = el.parent
            ul = parent.find_next(["ul", "ol", "table"])
            if ul:
                if ul.name in ["ul", "ol"]:
                    for li in ul.select("li"):
                        t = li.get_text(" ", strip=True)
                        if t and len(t) > 2:
                            localities.append(t)
                elif ul.name == "table":
                    for tr in ul.select("tr"):
                        cells = tr.select("td")
                        for cell in cells:
                            t = cell.get_text(strip=True)
                            if t and len(t) > 2 and not re.search(r"localit", t, re.IGNORECASE):
                                localities.append(t)

    # Parse from text block
    if not localities and loc_block:
        idx = text.lower().find(loc_block.lower())
        snippet = text[idx : idx + 4000]
        lines = [ln.strip(" :-\t") for ln in snippet.split("\n") if ln.strip()]
        cleaned = []
        for ln in lines:
            if re.search(r"localit", ln, re.IGNORECASE):
                continue
            cleaned.append(ln)
        stop_words = ["contact", "mobile", "phone", "address", "email", "ward", "division", "corporator"]
        for ln in cleaned:
            low = ln.lower()
            if any(w in low for w in stop_words):
                break
            parts = [p.strip() for p in re.split(r",|;|•|\u2022", ln) if p.strip()]
            for p in parts:
                if len(p) >= 2 and p not in localities:
                    localities.append(p)

    # De-dupe
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
    help = "Scrape GWMC wardwise_profile.aspx using Selenium (handles JavaScript/UpdatePanel)."

    def add_arguments(self, parser):
        parser.add_argument("--out", type=str, default="gwmc_wards.csv", help="Output file path")
        parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Output format")
        parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
        parser.add_argument("--wait", type=int, default=3, help="Wait time after selecting ward (seconds)")

    def handle(self, *args, **options):
        if not SELENIUM_AVAILABLE:
            raise CommandError(
                "Selenium is not installed. Install it with: pip install selenium webdriver-manager"
            )

        out_path: str = options["out"]
        out_format: str = options["format"]
        headless: bool = options["headless"]
        wait_time: int = options["wait"]

        # Setup Chrome driver
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            raise CommandError(f"Failed to setup Chrome driver: {e}")

        try:
            self.stdout.write("Loading GWMC wardwise profile page...")
            driver.get(GWMC_WARDWISE_URL)
            time.sleep(2)  # Wait for page to load

            # Find the ward dropdown
            try:
                wait = WebDriverWait(driver, 10)
                ward_select = wait.until(
                    EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDL_Eleward"))
                )
            except TimeoutException:
                # Try alternative selectors
                try:
                    ward_select = driver.find_element(By.CSS_SELECTOR, "select[name*='ward'], select[name*='DDL']")
                except NoSuchElementException:
                    raise CommandError("Could not find ward dropdown on page")

            select = Select(ward_select)
            options = select.options
            
            # Filter out placeholder option
            ward_options = [(opt.get_attribute("value"), opt.text) for opt in options 
                          if opt.get_attribute("value") and opt.text.strip() 
                          and "select" not in opt.text.lower()]
            
            self.stdout.write(f"Found {len(ward_options)} ward options")

            rows: List[WardRow] = []

            for i, (ward_value, ward_label) in enumerate(ward_options, start=1):
                try:
                    self.stdout.write(f"[{i}/{len(ward_options)}] Processing ward {ward_label}...")
                    
                    # Select the ward
                    select.select_by_value(ward_value)
                    time.sleep(1)  # Brief wait after selection
                    
                    # Click the "Show" button to load ward details
                    try:
                        show_button = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Btn_Submit")
                        show_button.click()
                        time.sleep(wait_time)  # Wait for UpdatePanel to load
                    except NoSuchElementException:
                        # Try alternative selector
                        show_button = driver.find_element(By.CSS_SELECTOR, "input[value='Show']")
                        show_button.click()
                        time.sleep(wait_time)

                    # Get the updated page content
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, "lxml")

                    # Debug: save HTML for first few wards
                    if i <= 3:
                        with open(f"selenium_ward_{ward_label}.html", "w", encoding="utf-8") as f:
                            f.write(page_source)

                    corporator, localities = _extract_localities_and_corporator(soup)

                    rows.append(
                        WardRow(
                            ward_value=ward_value,
                            ward_label=ward_label,
                            corporator_name=corporator,
                            localities=localities,
                        )
                    )

                    self.stdout.write(
                        f"  -> corporator='{corporator}' localities={len(localities)}"
                    )

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error processing ward {ward_label}: {e}"))
                    rows.append(
                        WardRow(
                            ward_value=ward_value,
                            ward_label=ward_label,
                            corporator_name="",
                            localities=[],
                        )
                    )

            # Export data
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

        finally:
            driver.quit()
