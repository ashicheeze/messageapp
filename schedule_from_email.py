import os
import base64
import openai
import json
import re
from datetime import datetime, timedelta
from dateutil import parser
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]


def build_gmail_service():
    """Create a Gmail API service using an OAuth token file."""
    token_file = os.environ.get('GMAIL_TOKEN_JSON')
    if not token_file:
        raise RuntimeError('GMAIL_TOKEN_JSON environment variable is required')
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    return build('gmail', 'v1', credentials=creds)


def build_calendar_service():
    """Create a Google Calendar API service using an OAuth token file."""
    token_file = os.environ.get('GMAIL_TOKEN_JSON')
    if not token_file:
        raise RuntimeError('GMAIL_TOKEN_JSON environment variable is required')
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    return build('calendar', 'v3', credentials=creds)


def _extract_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return ''
    data = payload.get('body', {}).get('data')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ''


def fetch_seen_emails(max_count=10, query=None):
    """Fetch already read emails using the Gmail API."""
    service = build_gmail_service()
    q = query or os.environ.get('GMAIL_QUERY', 'label:inbox is:read')
    result = service.users().messages().list(userId='me', q=q, maxResults=max_count).execute()
    messages = result.get('messages', [])
    emails = []
    for msg_meta in messages:
        msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        body = _extract_body(msg.get('payload', {}))
        emails.append({'subject': subject, 'body': body})
    return emails


def analyze_emails_with_llm(emails):
    """Use OpenAI API to analyze emails and suggest schedules."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is required')
    
    client = openai.OpenAI(api_key=api_key)
    suggestions = []
    for data in emails:
        prompt = f"""You are an assistant that extracts meeting or event details from emails and proposes schedule summaries.\nEmail subject: {data['subject']}\nEmail body:\n{data['body']}\nReturn a brief bullet point summary of any relevant dates or times mentioned."""
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": prompt}]
            )
            suggestions.append(response.choices[0].message.content)
        except Exception as exc:
            suggestions.append(f"Error from LLM: {exc}")
    return suggestions


def extract_structured_events(emails):
    """Use OpenAI API to extract structured event information from emails."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is required')
    
    client = openai.OpenAI(api_key=api_key)
    events = []
    
    for data in emails:
        prompt = f"""You are an assistant that extracts meeting or event details from emails and converts them to structured calendar events.

Email subject: {data['subject']}
Email body: {data['body']}

Extract event information and return a JSON object with the following structure:
{{
    "title": "Event title",
    "description": "Event description",
    "start_date": "YYYY-MM-DD",
    "start_time": "HH:MM" (if specified, otherwise null),
    "end_date": "YYYY-MM-DD" (if different from start_date),
    "end_time": "HH:MM" (if specified, otherwise null),
    "location": "Event location" (if specified, otherwise null),
    "all_day": true/false,
    "has_event": true/false (whether this email contains an actual event/meeting)
}}

Only extract clear, specific events with dates. If no clear event is found, set "has_event" to false.
Return only the JSON object, no other text."""

        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Try to parse JSON response
            try:
                event_data = json.loads(response.choices[0].message.content)
                if event_data.get('has_event', False):
                    event_data['email_subject'] = data['subject']
                    events.append(event_data)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON for email: {data['subject']}")
                continue
                
        except Exception as exc:
            print(f"Error processing email '{data['subject']}': {exc}")
            continue
    
    return events


def create_calendar_events(events, dry_run=True):
    """Create events in Google Calendar."""
    if not events:
        if not dry_run:
            return []
        print("No events to create.")
        return
    
    if dry_run:
        print("\n--- Calendar Event Proposals ---")
        for i, event in enumerate(events, 1):
            print(f"\nEvent {i}:")
            print(f"  Title: {event['title']}")
            print(f"  Date: {event['start_date']}")
            if event.get('start_time'):
                print(f"  Time: {event['start_time']}")
                if event.get('end_time'):
                    print(f"  End Time: {event['end_time']}")
            if event.get('location'):
                print(f"  Location: {event['location']}")
            print(f"  Description: {event['description']}")
            print(f"  Source Email: {event['email_subject']}")
        
        # Ask user if they want to actually create the events
        response = input("\nDo you want to create these events in Google Calendar? (y/n): ")
        if response.lower() != 'y':
            print("Events not created.")
            return
    
    # Create events in Google Calendar
    service = build_calendar_service()
    created_events = []
    
    for event in events:
        try:
            # Parse dates and times
            start_datetime = event['start_date']
            end_datetime = event.get('end_date', event['start_date'])
            
            if event.get('start_time') and not event.get('all_day', False):
                start_datetime = f"{event['start_date']}T{event['start_time']}:00"
                if event.get('end_time'):
                    end_datetime = f"{event.get('end_date', event['start_date'])}T{event['end_time']}:00"
                else:
                    # Default to 1 hour duration
                    start_dt = parser.parse(start_datetime)
                    end_dt = start_dt + timedelta(hours=1)
                    end_datetime = end_dt.isoformat()
                
                calendar_event = {
                    'summary': event['title'],
                    'description': event['description'] + f"\n\nSource: {event['email_subject']}",
                    'start': {
                        'dateTime': start_datetime,
                        'timeZone': 'Asia/Tokyo',
                    },
                    'end': {
                        'dateTime': end_datetime,
                        'timeZone': 'Asia/Tokyo',
                    },
                }
            else:
                # All-day event
                calendar_event = {
                    'summary': event['title'],
                    'description': event['description'] + f"\n\nSource: {event['email_subject']}",
                    'start': {
                        'date': event['start_date'],
                    },
                    'end': {
                        'date': event.get('end_date', event['start_date']),
                    },
                }
            
            if event.get('location'):
                calendar_event['location'] = event['location']
            
            # Create the event
            created_event = service.events().insert(calendarId='primary', body=calendar_event).execute()
            created_events.append(created_event)
            if not dry_run:
                print(f"Created event: {event['title']} - {created_event.get('htmlLink')}")
            
        except Exception as e:
            if not dry_run:
                print(f"Failed to create event '{event['title']}': {e}")
    
    if not dry_run:
        print(f"\nSuccessfully created {len(created_events)} events in Google Calendar!")
    return created_events


def main():
    print("Fetching emails from Gmail...")
    emails = fetch_seen_emails()
    if not emails:
        print('No read emails found.')
        return
    
    print(f"Found {len(emails)} emails. Analyzing for schedule information...")
    
    # Get basic schedule suggestions
    schedules = analyze_emails_with_llm(emails)
    print('\n--- Schedule Suggestions ---')
    for idx, sch in enumerate(schedules, 1):
        print(f"\nEmail {idx}:")
        print(sch)
    
    print("\n" + "="*50)
    print("GOOGLE CALENDAR INTEGRATION")
    print("="*50)
    
    # Extract structured events for calendar creation
    print("Extracting structured event information...")
    events = extract_structured_events(emails)
    
    if events:
        print(f"Found {len(events)} potential calendar events.")
        create_calendar_events(events, dry_run=True)
    else:
        print("No clear calendar events found in the emails.")


if __name__ == '__main__':
    main()
