# Message App

This project demonstrates how to use an LLM to propose schedule summaries based on read emails.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Export the following environment variables:

- `GMAIL_TOKEN_JSON` – OAuth token file for the Gmail API
- `OPENAI_API_KEY` – API key for OpenAI
- `LINE_NOTIFY_TOKEN` – token for [LINE Notify](https://notify-bot.line.me/)
- `GMAIL_QUERY` – optional search query for Gmail (defaults to `label:inbox is:read`)

You can place these variables in a `.env` file and `python-dotenv` will load them automatically.

## Usage

Run the script to fetch the last few read emails and request schedule suggestions from the LLM:

```bash
python schedule_from_email.py
```

The program prints schedule proposals extracted from each email using the OpenAI ChatGPT model.

Alternatively, you can send a summary of the most recent email directly to LINE Notify:

```bash
python line_notify_summary.py
```
