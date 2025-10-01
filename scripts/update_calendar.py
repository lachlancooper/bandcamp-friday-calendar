#!/usr/bin/env python3
"""
Scrape Bandcamp Friday dates from isitbandcampfriday.com and update the ICS file.
Keeps all previous events intact.
"""

import re
import json
import html
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

        # Find the div with data-fundraisers attribute
        bandcamp_vm = soup.find('div', id='bandcamp-friday-vm')
        if not bandcamp_vm or not bandcamp_vm.get('data-fundraisers'):
            print("Could not find data-fundraisers attribute")
            return []

        # Parse the JSON data (it's HTML-encoded)
        fundraisers_json = html.unescape(bandcamp_vm['data-fundraisers'])
        fundraisers = json.loads(fundraisers_json)

        # Extract dates from the fundraiser objects
        dates = []
        for fundraiser in fundraisers:
            try:
                # Parse date string like "Fri, 03 Oct 2025 07:00:00 -0000"
                date_str = fundraiser['date']
                dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                date_formatted = dt.strftime('%Y%m%d')
                if date_formatted not in dates:
                    dates.append(date_formatted)
            except Exception as e:
                print(f"Error parsing date {fundraiser.get('date')}: {e}")
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
    """Generate a VEVENT block for a given date in Pacific time."""
    dt = datetime.strptime(date_str, '%Y%m%d')

    uid = f"bandcamp-friday-{date_str}@github.com"
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dtstart = dt.strftime('%Y%m%dT000000')
    dtend = dt.strftime('%Y%m%dT235959')

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART;TZID=America/Los_Angeles:{dtstart}
DTEND;TZID=America/Los_Angeles:{dtend}
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
X-WR-TIMEZONE:America/Los_Angeles
X-WR-CALDESC:Bandcamp Friday - when Bandcamp waives its revenue share

BEGIN:VTIMEZONE
TZID:America/Los_Angeles
BEGIN:DAYLIGHT
TZOFFSETFROM:-0800
TZOFFSETTO:-0700
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
TZNAME:PDT
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0700
TZOFFSETTO:-0800
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
TZNAME:PST
END:STANDARD
END:VTIMEZONE
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
