#!/usr/bin/env python3
"""
Tests for update_calendar.py script.
"""

import datetime
from unittest.mock import Mock, mock_open, patch
import sys
import os

# Add scripts directory to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import update_calendar


class TestScrapeDates:
    """Tests for scrape_dates function."""

    def test_scrape_dates_success(self, mocker):
        """Test successful scraping of dates from website."""
        # Mock HTML response matching actual isitbandcampfriday.com format
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm"
                class="pane"
                data-fundraisers="[{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;},{&quot;date&quot;:&quot;Fri, 07 Nov 2025 08:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;November 7th, 2025&quot;},{&quot;date&quot;:&quot;Fri, 05 Dec 2025 08:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;December 5th, 2025&quot;}]"
                data-is-dev="false">
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        assert len(dates) == 3
        assert '20251003' in dates
        assert '20251107' in dates
        assert '20251205' in dates
        assert dates == sorted(dates)  # Should be sorted

    def test_scrape_dates_html_encoded(self, mocker):
        """Test handling of HTML-encoded JSON data."""
        # Mock HTML with HTML-encoded JSON matching real format
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm"
                data-fundraisers="[{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;}]">
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        assert len(dates) == 1
        assert '20251003' in dates

    def test_scrape_dates_duplicate_removal(self, mocker):
        """Test that duplicate dates are removed."""
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm"
                data-fundraisers="[{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;},{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;}]">
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        assert len(dates) == 1
        assert '20251003' in dates

    def test_scrape_dates_missing_attribute(self, mocker):
        """Test handling when data-fundraisers attribute is missing."""
        mock_html = '<html><body>No data here</body></html>'

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        assert dates == []

    def test_scrape_dates_invalid_json(self, mocker):
        """Test handling of invalid JSON data."""
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm" data-fundraisers='invalid json'>
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        assert dates == []

    def test_scrape_dates_network_error(self, mocker):
        """Test handling of network errors."""
        mocker.patch('update_calendar.requests.get', side_effect=Exception("Network error"))

        dates = update_calendar.scrape_dates()

        assert dates == []

    def test_scrape_dates_invalid_date_format(self, mocker):
        """Test handling of invalid date formats."""
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm"
                data-fundraisers="[{&quot;date&quot;:&quot;Invalid date format&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;Invalid&quot;},{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;}]">
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        dates = update_calendar.scrape_dates()

        # Should skip invalid date but process valid one
        assert len(dates) == 1
        assert '20251003' in dates


class TestReadExistingIcs:
    """Tests for read_existing_ics function."""

    def test_read_existing_ics_with_events(self, mocker):
        """Test reading ICS file with existing events."""
        mock_ics_content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:bandcamp-friday-20250103@github.com
DTSTART:20250103
END:VEVENT
BEGIN:VEVENT
UID:bandcamp-friday-20250207@github.com
DTSTART:20250207
END:VEVENT
END:VCALENDAR"""

        mocker.patch('builtins.open', mock_open(read_data=mock_ics_content))

        content, uids = update_calendar.read_existing_ics()

        assert content == mock_ics_content
        assert len(uids) == 2
        assert 'bandcamp-friday-20250103@github.com' in uids
        assert 'bandcamp-friday-20250207@github.com' in uids

    def test_read_existing_ics_no_events(self, mocker):
        """Test reading ICS file with no events."""
        mock_ics_content = """BEGIN:VCALENDAR
VERSION:2.0
END:VCALENDAR"""

        mocker.patch('builtins.open', mock_open(read_data=mock_ics_content))

        content, uids = update_calendar.read_existing_ics()

        assert content == mock_ics_content
        assert uids == []

    def test_read_existing_ics_file_not_found(self, mocker):
        """Test handling when ICS file doesn't exist."""
        mocker.patch('builtins.open', side_effect=FileNotFoundError)

        content, uids = update_calendar.read_existing_ics()

        assert content is None
        assert uids == []


class TestGenerateVevent:
    """Tests for generate_vevent function."""

    def test_generate_vevent_format(self, mocker):
        """Test that VEVENT is generated with correct format."""
        # Mock datetime.now to make test deterministic
        mock_datetime = mocker.MagicMock()
        mock_datetime.now.return_value = datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
        mock_datetime.strptime = datetime.datetime.strptime
        mocker.patch('update_calendar.datetime.datetime', mock_datetime)

        vevent = update_calendar.generate_vevent('20251003')

        assert 'BEGIN:VEVENT\r\n' in vevent
        assert 'END:VEVENT' in vevent
        assert 'UID:bandcamp-friday-20251003@github.com\r\n' in vevent
        assert 'DTSTAMP:20250101T120000Z\r\n' in vevent
        assert 'DTSTART;TZID=America/Los_Angeles:20251003T000000\r\n' in vevent
        assert 'DTEND;TZID=America/Los_Angeles:20251003T235959\r\n' in vevent
        assert 'SUMMARY:Bandcamp Friday\r\n' in vevent
        assert 'URL:https://isitbandcampfriday.com/\r\n' in vevent
        assert 'STATUS:CONFIRMED\r\n' in vevent

    def test_generate_vevent_description_folding(self):
        """Test that DESCRIPTION field is properly folded per RFC 5545."""
        vevent = update_calendar.generate_vevent('20251003')

        # Check description is present and properly formatted with line folding
        assert 'DESCRIPTION:Bandcamp waives its revenue share on this day. Support artists\r\n' in vevent
        assert '  directly!' in vevent  # Continuation line with single space

    def test_generate_vevent_unique_uid(self):
        """Test that different dates generate unique UIDs."""
        vevent1 = update_calendar.generate_vevent('20251003')
        vevent2 = update_calendar.generate_vevent('20251107')

        assert 'UID:bandcamp-friday-20251003@github.com' in vevent1
        assert 'UID:bandcamp-friday-20251107@github.com' in vevent2


class TestUpdateIcsFile:
    """Tests for update_ics_file function."""

    def test_update_ics_file_new_dates(self, mocker):
        """Test adding new dates to existing ICS file."""
        existing_ics = """BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VTIMEZONE\r
TZID:America/Los_Angeles\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250103@github.com\r
DTSTART:20250103\r
END:VEVENT\r
END:VCALENDAR\r
"""

        mock_file = mock_open(read_data=existing_ics)
        mocker.patch('builtins.open', mock_file)
        mocker.patch('update_calendar.generate_vevent', return_value='MOCK_EVENT')

        update_calendar.update_ics_file(['20250103', '20250207'])

        # Check that file was written
        handle = mock_file()
        handle.write.assert_called_once()
        written_content = handle.write.call_args[0][0]

        # Should contain normalized line endings
        assert '\r\n' in written_content
        assert written_content.endswith('\r\n')

    def test_update_ics_file_no_new_dates(self, mocker, capsys):
        """Test when no new dates need to be added."""
        existing_ics = """BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250103@github.com\r
END:VEVENT\r
END:VCALENDAR\r
"""

        mock_file = mock_open(read_data=existing_ics)
        mocker.patch('builtins.open', mock_file)

        update_calendar.update_ics_file(['20250103'])

        captured = capsys.readouterr()
        assert 'No new dates to add' in captured.out

    def test_update_ics_file_create_new(self, mocker):
        """Test creating new ICS file from scratch."""
        mocker.patch('builtins.open', side_effect=[
            FileNotFoundError,  # First call (read) fails
            mock_open()()  # Second call (write) succeeds
        ])
        mocker.patch('update_calendar.generate_vevent', return_value='MOCK_EVENT')

        mock_write = mock_open()
        with patch('builtins.open', mock_write):
            # Need to handle FileNotFoundError on read
            with patch('update_calendar.read_existing_ics', return_value=(None, [])):
                update_calendar.update_ics_file(['20250103'])

        # Verify write was called
        mock_write.assert_called()

    def test_update_ics_file_sorts_events(self, mocker):
        """Test that events are sorted chronologically."""
        existing_ics = """BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VTIMEZONE\r
TZID:America/Los_Angeles\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250207@github.com\r
END:VEVENT\r
END:VCALENDAR\r
"""

        mock_file = mock_open(read_data=existing_ics)
        generated_events = []

        def mock_generate(date):
            event = f'EVENT_{date}'
            generated_events.append(date)
            return event

        mocker.patch('builtins.open', mock_file)
        mocker.patch('update_calendar.generate_vevent', side_effect=mock_generate)

        # Add a date that should come before existing date
        update_calendar.update_ics_file(['20250103', '20250207'])

        # Events should be generated in sorted order
        assert generated_events == ['20250103', '20250207']

    def test_update_ics_file_reorder_existing(self, mocker):
        """Test reordering existing events when they're out of order."""
        # Existing file with events out of order
        existing_ics = """BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VTIMEZONE\r
TZID:America/Los_Angeles\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250207@github.com\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250103@github.com\r
END:VEVENT\r
END:VCALENDAR\r
"""

        mock_file = mock_open(read_data=existing_ics)
        mocker.patch('builtins.open', mock_file)

        generated_dates = []
        def track_generate(date):
            generated_dates.append(date)
            return f'EVENT_{date}'

        mocker.patch('update_calendar.generate_vevent', side_effect=track_generate)

        # Pass same dates, should trigger reordering
        update_calendar.update_ics_file(['20250103', '20250207'])

        # Events should be generated in sorted order
        assert generated_dates == ['20250103', '20250207']
        # File should have been written
        mock_file().write.assert_called_once()

    def test_update_ics_file_preserves_header(self, mocker):
        """Test that calendar header and timezone info is preserved."""
        existing_ics = """BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Custom Producer//EN\r
BEGIN:VTIMEZONE\r
TZID:America/Los_Angeles\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:bandcamp-friday-20250103@github.com\r
END:VEVENT\r
END:VCALENDAR\r
"""

        mock_file = mock_open(read_data=existing_ics)
        mocker.patch('builtins.open', mock_file)
        mocker.patch('update_calendar.generate_vevent', return_value='MOCK_EVENT')

        update_calendar.update_ics_file(['20250103', '20250207'])

        handle = mock_file()
        written_content = handle.write.call_args[0][0]

        # Check header elements are preserved
        assert 'BEGIN:VCALENDAR\r\n' in written_content
        assert 'VERSION:2.0\r\n' in written_content
        assert 'PRODID:-//Custom Producer//EN\r\n' in written_content
        assert 'BEGIN:VTIMEZONE\r\n' in written_content


class TestLineEndingNormalization:
    """Tests for line ending handling."""

    def test_normalizes_mixed_line_endings(self, mocker):
        """Test that mixed line endings are normalized to CRLF."""
        # File with mixed line endings and out-of-order events
        # Note: Using \r\n consistently in UIDs to ensure regex matches properly
        existing_ics = "BEGIN:VCALENDAR\nVERSION:2.0\r\nBEGIN:VTIMEZONE\r\nTZID:America/Los_Angeles\r\nEND:VTIMEZONE\r\nBEGIN:VEVENT\r\nUID:bandcamp-friday-20250207@github.com\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:bandcamp-friday-20250103@github.com\r\nEND:VEVENT\r\nEND:VCALENDAR\n"

        mock_file = mock_open(read_data=existing_ics)
        mocker.patch('builtins.open', mock_file)
        mocker.patch('update_calendar.generate_vevent', return_value='MOCK_EVENT')

        # Pass dates in sorted order to trigger reordering
        update_calendar.update_ics_file(['20250103', '20250207'])

        handle = mock_file()
        written_content = handle.write.call_args[0][0]

        # Should be normalized to CRLF
        assert '\r\n' in written_content
        # Most content should use CRLF (allow some tolerance for the mock event)
        crlf_count = written_content.count('\r\n')
        assert crlf_count >= 5  # At least header lines should be CRLF


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow_with_mock_data(self, mocker):
        """Test complete workflow from scraping to file update."""
        # Mock the scrape to return dates using real format
        mock_html = '''
        <html>
            <div id="bandcamp-friday-vm"
                class="pane"
                data-fundraisers="[{&quot;date&quot;:&quot;Fri, 03 Oct 2025 07:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;October 3rd, 2025&quot;},{&quot;date&quot;:&quot;Fri, 07 Nov 2025 08:00:00 -0000&quot;,&quot;url&quot;:&quot;https://daily.bandcamp.com/features/bandcamp-fridays&quot;,&quot;zero_revshare&quot;:true,&quot;display&quot;:&quot;November 7th, 2025&quot;}]"
                data-is-dev="false">
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode()
        mock_response.raise_for_status = Mock()

        mocker.patch('update_calendar.requests.get', return_value=mock_response)

        # Mock file operations
        mock_file = mock_open(read_data='')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('update_calendar.read_existing_ics', return_value=(None, []))

        # Mock datetime for deterministic timestamps
        mock_datetime = mocker.MagicMock()
        mock_datetime.now.return_value = datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
        mock_datetime.strptime = datetime.datetime.strptime
        mocker.patch('update_calendar.datetime.datetime', mock_datetime)

        # Run the scrape
        dates = update_calendar.scrape_dates()

        assert len(dates) == 2
        assert '20251003' in dates
        assert '20251107' in dates

        # Update the ICS file
        update_calendar.update_ics_file(dates)

        # Verify write was called
        mock_file.assert_called()
