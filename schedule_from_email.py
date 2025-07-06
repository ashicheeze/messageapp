import os
import base64
import openai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def build_gmail_service():
    """Create a Gmail API service using an OAuth token file."""
    token_file = os.environ.get('GMAIL_TOKEN_JSON')
    if not token_file:
        raise RuntimeError('GMAIL_TOKEN_JSON environment variable is required')
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    return build('gmail', 'v1', credentials=creds)


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
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is required')

    suggestions = []
    for data in emails:
        prompt = f"""You are an assistant that extracts meeting or event details from emails and proposes schedule summaries.\nEmail subject: {data['subject']}\nEmail body:\n{data['body']}\nReturn a brief bullet point summary of any relevant dates or times mentioned."""
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": prompt}]
            )
            suggestions.append(response.choices[0].message['content'])
        except Exception as exc:
            suggestions.append(f"Error from LLM: {exc}")
    return suggestions


def main():
    emails = fetch_seen_emails()
    if not emails:
        print('No read emails found.')
        return
    schedules = analyze_emails_with_llm(emails)
    print('\n--- Schedule Suggestions ---')
    for idx, sch in enumerate(schedules, 1):
        print(f"\nEmail {idx}:")
        print(sch)


if __name__ == '__main__':
    main()
