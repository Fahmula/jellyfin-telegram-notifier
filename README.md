# Jellyfin Notification System

A simple Flask application that sends notifications to Telegram whenever new content (movies, series, seasons, episodes) is added to Jellyfin.

---

## Features

- Sends Telegram notifications with media images whenever a new movie, series, season, or episode is added to Jellyfin.
- Integrates with the Jellyfin webhook plugin.
- Provides a filter to notify only for recent episodes or newly added seasons.

## Prerequisites

- A Jellyfin server with the Webhook plugin installed.
- A Telegram bot token and chat ID (see the section on setting up a Telegram bot below).
- Docker (optional, for Docker installation).

## Installation

### Traditional Installation

1. Clone the repository.
2. Install the requirements using `pip install -r requirements.txt`.
3. Set up your environment variables. (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, JELLYFIN_BASE_URL, JELLYFIN_API_KEY, YOUTUBE_API_KEY, EPISODE_PREMIERED_WITHIN_X_DAYS, SEASON_ADDED_WITHIN_X_DAYS).
4. Run the application using `python3 main.py`.

### Docker Installation

If you have Docker and Docker Compose installed, you can use the provided `docker-compose.yml`

1. Set up your environment variables in a `.env` file.
2. Run `docker-compose up`.

## Setting Up a Telegram Bot

1. Start a Chat with BotFather on Telegram.
2. Send `/newbot` command.
3. Name your bot.
4. Choose a unique username for your bot; it must end in `bot`.
5. Retrieve your HTTP API token.
6. Get your chat ID by starting a chat with your bot, sending a message, then visiting `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates` to find the chat ID in the returned JSON.
7. Input the Bot Token and Chat ID into the application's environment variables.

## Usage

### Setting up Jellyfin Webhook

1. Go to Jellyfin dashboard.
2. Navigate to `Plugins`.
3. Choose `Webhook` and add a new webhook.
4. Set the server to the Flask application's endpoint (e.g., `http://localhost:5000/webhook`).
5. For `Notification Type`, select `Item Added`.
6. For `Item Type`, select `Movie, Episode, Season`.
7. Make sure to enable the `Send All Properties (ignores template)` option.

#### Environment Variables Explanation:

- **`EPISODE_PREMIERED_WITHIN_X_DAYS`**:
  Determines how recent an episode's premiere date must be for a notification to be sent. For example, setting it to `7` means only episodes that premiered within the last 7 days will trigger a notification.

- **`SEASON_ADDED_WITHIN_X_DAYS`**:
  Dictates the threshold for sending notifications based on when a season was added to Jellyfin. If set to `3`, then if a season was added within the last 3 days, episode notifications will not be sent to avoid potential spam from adding an entire season at once.

### Setting Up YouTube API Key (Optional)

If you want to fetch YouTube trailer URLs for movies, you can set up a YouTube API key:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or use an existing one.
3. Enable the "YouTube Data API v3" for your project.
4. Create credentials for your project:
   - Go to the "Credentials" tab.
   - Click on "Create Credentials" and select "API Key".
5. Copy the generated API key.
6. Set the `YOUTUBE_API_KEY` environment variable in your `.env` file to the copied API key.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for new features, bug fixes, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
