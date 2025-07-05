# Message App

This project demonstrates how to use an LLM to propose schedule summaries based on read emails.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Export the following environment variables:

- `EMAIL_USER` – your IMAP account (e.g., Gmail address)
- `EMAIL_PASS` – password or app password for the account
- `EMAIL_SERVER` – optional IMAP server (defaults to `imap.gmail.com`)
- `OPENAI_API_KEY` – API key for OpenAI

You can place these variables in a `.env` file and `python-dotenv` will load them automatically.

## Usage

Run the script to fetch the last few read emails and request schedule suggestions from the LLM:

```bash
python schedule_from_email.py
```

The program prints schedule proposals extracted from each email using the OpenAI ChatGPT model.
