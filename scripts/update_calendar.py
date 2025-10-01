#!/usr/bin/env python3
"""
Scrape Bandcamp Friday dates from isitbandcampfriday.com and update the ICS file.
Keeps all previous events intact.
"""

import re
import json
import html
import datetime
import requests
from bs4 import BeautifulSoup
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
                dt = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
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
        uid_pattern = r'UID:(bandcamp-friday-\d{8}@github\.com)'
        existing_uids = re.findall(uid_pattern, content)

        return content, existing_uids
    except FileNotFoundError:
        return None, []

def generate_vevent(date_str: str) -> str:
    """Generate a VEVENT block for a given date in Pacific time."""
    dt = datetime.datetime.strptime(date_str, '%Y%m%d')

    uid = f"bandcamp-friday-{date_str}@github.com"
    dtstamp = datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')
    dtstart = dt.strftime('%Y%m%dT000000')
    dtend = dt.strftime('%Y%m%dT235959')

    return f"""BEGIN:VEVENT\r
UID:{uid}\r
DTSTAMP:{dtstamp}\r
DTSTART;TZID=America/Los_Angeles:{dtstart}\r
DTEND;TZID=America/Los_Angeles:{dtend}\r
SUMMARY:Bandcamp Friday\r
DESCRIPTION:Bandcamp waives its revenue share on this day. Support artists\r
 directly!\\n\\nhttps://isitbandcampfriday.com/\r
URL:https://isitbandcampfriday.com/\r
STATUS:CONFIRMED\r
TRANSP:TRANSPARENT\r
END:VEVENT"""

def update_ics_file(new_dates: List[str]):
    """Update the ICS file with new dates while preserving existing events."""
    content, existing_uids = read_existing_ics()

    # Extract existing dates from UIDs
    existing_dates = set()
    for uid in existing_uids:
        match = re.search(r'bandcamp-friday-(\d{8})', uid)
        if match:
            existing_dates.add(match.group(1))

    # Find new dates to add
    dates_to_add = [d for d in new_dates if d not in existing_dates]

    if not dates_to_add:
        print("No new dates to add.")
        return

    print(f"Adding {len(dates_to_add)} new dates: {dates_to_add}")

    # If we have existing content, insert new events before END:VCALENDAR
    if content:
        events = '\r\n'.join(generate_vevent(d) for d in dates_to_add)
        new_content = content.replace('END:VCALENDAR', f'\r\n{events}\r\nEND:VCALENDAR')
    else:
        # Create new ICS from scratch
        header = """BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Bandcamp Friday Calendar//EN\r
CALSCALE:GREGORIAN\r
METHOD:PUBLISH\r
X-WR-CALNAME:Bandcamp Friday\r
X-WR-TIMEZONE:America/Los_Angeles\r
X-WR-CALDESC:Bandcamp Friday - when Bandcamp waives its revenue share\r
BEGIN:VTIMEZONE\r
TZID:America/Los_Angeles\r
BEGIN:DAYLIGHT\r
TZOFFSETFROM:-0800\r
TZOFFSETTO:-0700\r
DTSTART:19700308T020000\r
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU\r
TZNAME:PDT\r
END:DAYLIGHT\r
BEGIN:STANDARD\r
TZOFFSETFROM:-0700\r
TZOFFSETTO:-0800\r
DTSTART:19701101T020000\r
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU\r
TZNAME:PST\r
END:STANDARD\r
END:VTIMEZONE\r
"""
        events = '\r\n'.join(generate_vevent(d) for d in new_dates)
        new_content = f"{header}{events}\r\nEND:VCALENDAR\r\n"

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
