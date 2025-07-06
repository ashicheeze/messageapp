import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
import requests
import openai


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def build_gmail_service():
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


def fetch_latest_email(query=None):
    """Fetch the most recent email matching the given query using the Gmail API."""
    service = build_gmail_service()
    q = query or os.environ.get('GMAIL_QUERY', 'label:inbox is:read')
    result = service.users().messages().list(userId='me', q=q, maxResults=1).execute()
    messages = result.get('messages', [])
    if not messages:
        return None
    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
    headers = msg.get('payload', {}).get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    body = _extract_body(msg.get('payload', {}))
    return {'subject': subject, 'body': body}


def get_gpt_summary(text, model='gpt-3.5-turbo'):
    """Summarize the provided text using OpenAI's API."""
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is required')
    prompt = f'Summarize the following email in Japanese:\n{text}'
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message['content']


def send_line_message(date_str, summary):
    """Send the summary to LINE Notify."""
    token = os.environ.get('LINE_NOTIFY_TOKEN')
    if not token:
        raise RuntimeError('LINE_NOTIFY_TOKEN environment variable is required')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'message': f'{date_str}\n{summary}'
    }
    response = requests.post('https://notify-api.line.me/api/notify', headers=headers, data=data)
    if response.status_code >= 400:
        raise RuntimeError(f'Failed to send LINE message: {response.text}')


def main():
    email_data = fetch_latest_email()
    if not email_data:
        print('No email found.')
        return
    trimmed = email_data['body'][:4000]
    model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    summary = get_gpt_summary(trimmed, model)
    date_str = datetime.now().strftime('%Y-%m-%d')
    send_line_message(date_str, summary)
    print('Summary sent to LINE.')


if __name__ == '__main__':
    main()
