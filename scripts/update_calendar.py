#!/usr/bin/env python3
"""
Scrape Bandcamp Friday dates from isitbandcampfriday.com and update the ICS file.
Keeps all previous events intact.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Tuple

ICS_FILE = 'bandcamp-friday.ics'
SOURCE_URL = 'https://isitbandcampfriday.com/'

def scrape_dates() -> List[str]:
    """Scrape upcoming Bandcamp Friday dates from the website."""
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for date patterns in the text
        # isitbandcampfriday typically shows dates in various formats
        text = soup.get_text()

        # Try to find dates in format like "October 3, 2025" or "Oct 3, 2025"
        date_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        matches = re.findall(date_pattern, text, re.IGNORECASE)

        # Parse and normalize dates
        dates = []
        for match in matches:
            try:
                # Try multiple date formats
                for fmt in ['%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y']:
                    try:
                        dt = datetime.strptime(match, fmt)
                        date_str = dt.strftime('%Y%m%d')
                        if date_str not in dates:
                            dates.append(date_str)
                        break
                    except ValueError:
                        continue
            except Exception:
                continue

        return sorted(set(dates))
    except Exception as e:
        print(f"Error scraping dates: {e}")
        return []

def read_existing_ics() -> Tuple[str, List[str]]:
    """Read the existing ICS file and extract existing event UIDs."""
    try:
        with open(ICS_FILE, 'r') as f:
            content = f.read()

        # Extract all existing event UIDs
        uid_pattern = r'UID:(bandcamp-friday-\d{4}-\d{2}-\d{2}@github\.com)'
        existing_uids = re.findall(uid_pattern, content)

        return content, existing_uids
    except FileNotFoundError:
        return None, []

def generate_vevent(date_str: str) -> str:
    """Generate a VEVENT block for a given date."""
    dt = datetime.strptime(date_str, '%Y%m%d')
    next_day = dt + timedelta(days=1)

    uid = f"bandcamp-friday-{date_str}@github.com"
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dtstart = dt.strftime('%Y%m%dT000000Z')
    dtend = next_day.strftime('%Y%m%dT000000Z')

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Bandcamp Friday
DESCRIPTION:Bandcamp waives its revenue share on this day. Support artists directly!
URL:https://isitbandcampfriday.com/
STATUS:CONFIRMED
TRANSP:TRANSPARENT
END:VEVENT"""

def update_ics_file(new_dates: List[str]):
    """Update the ICS file with new dates while preserving existing events."""
    content, existing_uids = read_existing_ics()

    # Extract existing dates from UIDs
    existing_dates = set()
    for uid in existing_uids:
        match = re.search(r'bandcamp-friday-(\d{4}-\d{2}-\d{2})', uid)
        if match:
            existing_dates.add(match.group(1).replace('-', ''))

    # Find new dates to add
    dates_to_add = [d for d in new_dates if d not in existing_dates]

    if not dates_to_add:
        print("No new dates to add.")
        return

    print(f"Adding {len(dates_to_add)} new dates: {dates_to_add}")

    # If we have existing content, insert new events before END:VCALENDAR
    if content:
        events = '\n\n'.join(generate_vevent(d) for d in dates_to_add)
        new_content = content.replace('END:VCALENDAR', f'\n{events}\n\nEND:VCALENDAR')
    else:
        # Create new ICS from scratch
        header = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Bandcamp Friday Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Bandcamp Friday
X-WR-TIMEZONE:UTC
X-WR-CALDESC:Bandcamp Friday - when Bandcamp waives its revenue share
"""
        events = '\n\n'.join(generate_vevent(d) for d in new_dates)
        new_content = f"{header}\n{events}\n\nEND:VCALENDAR\n"

    with open(ICS_FILE, 'w') as f:
        f.write(new_content)

    print(f"Updated {ICS_FILE}")

if __name__ == '__main__':
    print(f"Scraping Bandcamp Friday dates from {SOURCE_URL}...")
    dates = scrape_dates()

    if dates:
        print(f"Found {len(dates)} dates: {dates}")
        update_ics_file(dates)
    else:
        print("No dates found. Calendar not updated.")
