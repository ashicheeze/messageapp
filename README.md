# Email Schedule Manager

This project demonstrates how to use AI to automatically extract schedule information from emails and add them to Google Calendar with a beautiful web interface.

## Features

- 📧 **Gmail Integration**: Fetch emails using Gmail API
- 🤖 **AI-Powered Extraction**: Use OpenAI to extract schedule information from emails
- 📅 **Google Calendar Integration**: Automatically create calendar events
- 🌐 **Web Interface**: Beautiful, modern web app for selecting and managing events
- ✅ **Selective Sync**: Choose which events to add to your calendar

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up Google Cloud Project:
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API and Google Calendar API
   - Create OAuth 2.0 credentials and download `credentials.json`
   - Place `credentials.json` in the project directory

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your configuration:
     - `EMAIL_USER` – your Gmail address
     - `EMAIL_PASS` – your Gmail app password
     - `OPENAI_API_KEY` – your OpenAI API key

4. Authenticate with Google APIs:

```bash
python authenticate.py
```

This will create a `token.json` file with your authentication tokens.

## Usage

### Web Application (Recommended)

1. Start the web server:

```bash
python app.py
```

2. Open your browser and go to `http://localhost:5000`

3. Use the web interface to:
   - 📧 **Fetch emails** and extract events
   - ✅ **Select events** you want to add to calendar
   - 📅 **Create calendar events** with one click

### Command Line

Run the command-line version to see all extracted events:

```bash
python schedule_from_email.py
```

## Configuration Options

- `GMAIL_QUERY`: Filter emails (default: `label:inbox is:read`)
  - `label:inbox is:unread` - Only unread emails
  - `label:inbox newer_than:7d` - Last 7 days
  - `from:example@gmail.com` - From specific sender

## Technologies Used

- **Flask** - Web framework
- **Gmail API** - Email access
- **Google Calendar API** - Calendar integration
- **OpenAI API** - AI-powered text analysis
- **OAuth 2.0** - Secure authentication

## Screenshots

The web application features:
- Modern, responsive design
- Tab-based navigation
- Event selection interface
- Real-time status updates
- Beautiful card-based event display

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
