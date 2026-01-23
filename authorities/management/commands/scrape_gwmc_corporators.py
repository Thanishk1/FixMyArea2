"""
Scrape GWMC corporator contact details from the contact page.

Target page:
  https://gwmc.gov.in/Contactus_new.aspx?status=98

Usage:
  python manage.py scrape_gwmc_corporators --out corporators.csv
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


GWMC_CONTACT_URL = "https://gwmc.gov.in/Contactus_new.aspx?status=98"


@dataclass
class CorporatorRow:
    name: str
    ward: str
    phone: str
    email: str
    address: str
    other_info: str


def extract_corporator_data(soup: BeautifulSoup) -> List[CorporatorRow]:
    """Extract corporator data from the page."""
    corporators = []
    
    # Find the main table with corporator data
    # Look for table with class containing "border" or "contact"
    tables = soup.find_all("table", class_=re.compile(r"border|contact|grid", re.I))
    if not tables:
        # Fallback: find any table
        tables = soup.find_all("table")
    
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:  # Need at least header + data rows
            continue
        
        # Skip header row
        data_rows = rows[1:] if rows else []
        
        for row in data_rows:
            cells = row.find_all(["td"])
            if len(cells) < 3:  # Need at least ward, name, phone
                continue
            
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Typical structure: Ward | Name | Designation | Address | Phone | Party | Email | Photo
            ward = cell_texts[0] if len(cell_texts) > 0 else ""
            name = cell_texts[1] if len(cell_texts) > 1 else ""
            designation = cell_texts[2] if len(cell_texts) > 2 else ""
            address = cell_texts[3] if len(cell_texts) > 3 else ""
            phone = cell_texts[4] if len(cell_texts) > 4 else ""
            party = cell_texts[5] if len(cell_texts) > 5 else ""
            email = cell_texts[6] if len(cell_texts) > 6 else ""
            
            # Clean up ward (remove non-numeric)
            ward = re.sub(r"[^\d]", "", ward) if ward else ""
            
            # Clean up phone (keep only digits)
            if phone:
                phone = re.sub(r"[^\d]", "", phone)
                # Validate phone length (should be 10 digits)
                if len(phone) != 10:
                    phone = ""
            
            # Validate name (should be substantial text, not just numbers or labels)
            if name:
                if len(name) < 3 or re.match(r"^\d+$", name) or re.search(r"^(ward|name|designation|address|phone|party|email|photo|corporator|mayor)$", name, re.I):
                    name = ""
            
            # Only add if we have at least ward and name
            if ward and name:
                corporators.append(
                    CorporatorRow(
                        name=name,
                        ward=ward,
                        phone=phone,
                        email=email,
                        address=address if address and address.upper() != "NA" else "",
                        other_info=f"Designation: {designation} | Party: {party}" if designation or party else ""
                    )
                )
    
    # If no structured table found, try parsing from text patterns
    if not corporators:
        text = soup.get_text("\n", strip=True)
        # Look for patterns like "1 | Varanganti Aruna Kumari | Corporator | NA | 7032170085 | BJP"
        pattern = r"(\d+)\s*\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d{10})\s*\|\s*([A-Z]+)"
        matches = re.findall(pattern, text)
        for match in matches:
            ward, name, designation, address, phone, party = match
            corporators.append(
                CorporatorRow(
                    name=name.strip(),
                    ward=ward.strip(),
                    phone=phone.strip(),
                    email="",
                    address=address.strip() if address.strip().upper() != "NA" else "",
                    other_info=f"Designation: {designation.strip()} | Party: {party.strip()}"
                )
            )
    
    return corporators


class Command(BaseCommand):
    help = "Scrape GWMC corporator contact details from Contactus_new.aspx"

    def add_arguments(self, parser):
        parser.add_argument("--out", type=str, default="gwmc_corporators.csv", help="Output file path")
        parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Output format")
        parser.add_argument("--use-selenium", action="store_true", help="Use Selenium (if page requires JavaScript)")
        parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (Selenium only)")

    def handle(self, *args, **options):
        out_path: str = options["out"]
        out_format: str = options["format"]
        use_selenium: bool = options["use_selenium"]
        headless: bool = options["headless"]

        if use_selenium and not SELENIUM_AVAILABLE:
            raise CommandError("Selenium is not installed. Install it with: pip install selenium webdriver-manager")

        # Try requests first (faster)
        if not use_selenium:
            try:
                self.stdout.write("Fetching page with requests...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(GWMC_CONTACT_URL, headers=headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
                
                # Save HTML for debugging
                with open("debug_contact_page.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                self.stdout.write("Saved page HTML to debug_contact_page.html")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Requests failed: {e}. Trying Selenium..."))
                use_selenium = True

        # Use Selenium if requested or if requests failed
        if use_selenium:
            chrome_options = webdriver.ChromeOptions()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                raise CommandError(f"Failed to setup Chrome driver: {e}")

            try:
                self.stdout.write("Loading page with Selenium...")
                driver.get(GWMC_CONTACT_URL)
                import time
                time.sleep(3)  # Wait for page to load
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "lxml")
                
                # Save HTML for debugging
                with open("debug_contact_page.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                self.stdout.write("Saved page HTML to debug_contact_page.html")
                
            finally:
                driver.quit()

        # Extract corporator data
        self.stdout.write("Extracting corporator data...")
        corporators = extract_corporator_data(soup)
        
        if not corporators:
            self.stdout.write(self.style.WARNING("No corporator data found. Check debug_contact_page.html for page structure."))
            self.stdout.write("You may need to adjust the extraction logic based on the actual HTML structure.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Found {len(corporators)} corporator entries"))

        # Export data
        if out_format == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([asdict(c) for c in corporators], f, ensure_ascii=False, indent=2)
        else:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["name", "ward", "phone", "email", "address", "other_info"])
                for corp in corporators:
                    w.writerow([corp.name, corp.ward, corp.phone, corp.email, corp.address, corp.other_info])

        self.stdout.write(self.style.SUCCESS(f"Exported {len(corporators)} corporators to {out_path}"))
