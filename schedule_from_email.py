import os
import imaplib
import email
import openai
from email.header import decode_header


def fetch_seen_emails(max_count=10):
    """Fetch a limited number of already read emails using IMAP."""
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    if not user or not password:
        raise RuntimeError("EMAIL_USER and EMAIL_PASS environment variables are required")

    imap_server = os.environ.get("EMAIL_SERVER", "imap.gmail.com")
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(user, password)
    imap.select("INBOX")

    status, messages = imap.search(None, 'SEEN')
    if status != 'OK':
        imap.close()
        imap.logout()
        raise RuntimeError('Failed to search mailbox')

    email_ids = messages[0].split()
    emails = []
    for eid in email_ids[-max_count:]:
        status, msg_data = imap.fetch(eid, '(RFC822)')
        if status != 'OK':
            continue
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdisp = str(part.get('Content-Disposition'))
                        if ctype == 'text/plain' and 'attachment' not in cdisp:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body += payload.decode('utf-8', errors='ignore')
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                emails.append({
                    'subject': str(decode_header(msg['subject'])[0][0]),
                    'body': body
                })
    imap.close()
    imap.logout()
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
