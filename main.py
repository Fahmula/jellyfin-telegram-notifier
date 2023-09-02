import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
import os
import json
import requests
from requests.exceptions import HTTPError
from flask import Flask, request
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

# Set up logging
log_filename = 'jellyfin_telegram-notifier.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a handler for rotating log files daily
rotating_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)
rotating_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add the rotating handler to the logger
logging.getLogger().addHandler(rotating_handler)

# Constants
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
JELLYFIN_BASE_URL = os.environ["JELLYFIN_BASE_URL"]
JELLYFIN_API_KEY = os.environ["JELLYFIN_API_KEY"]
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
EPISODE_PREMIERED_WITHIN_X_DAYS = int(os.environ["EPISODE_PREMIERED_WITHIN_X_DAYS"])
SEASON_ADDED_WITHIN_X_DAYS = int(os.environ["SEASON_ADDED_WITHIN_X_DAYS"])


def send_telegram_photo(photo_id, caption):
    base_photo_url = f"{JELLYFIN_BASE_URL}/Items/{photo_id}/Images"
    primary_photo_url = f"{base_photo_url}/Primary"

    # Download the image from the jellyfin
    image_response = requests.get(primary_photo_url)

    # Upload the image to the Telegram bot
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
        "parse_mode": "Markdown"
    }

    files = {'photo': ('photo.jpg', image_response.content, 'image/jpeg')}
    response = requests.post(url, data=data, files=files)
    return response


def get_item_details(item_id):
    headers = {'accept': 'application/json', }
    params = {'api_key': JELLYFIN_API_KEY, }
    url = f"{JELLYFIN_BASE_URL}/emby/Items?Recursive=true&Fields=DateCreated, Overview&Ids={item_id}"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Check if request was successful
    return response.json()


def is_within_last_x_days(date_str, x):
    days_ago = datetime.now() - timedelta(days=x)
    return date_str >= days_ago.isoformat()


def is_not_within_last_x_days(date_str, x):
    days_ago = datetime.now() - timedelta(days=x)
    return date_str < days_ago.isoformat()


def get_youtube_trailer_url(query):
    base_search_url = "https://www.googleapis.com/youtube/v3/search"
    if not YOUTUBE_API_KEY:
        return None
    api_key = YOUTUBE_API_KEY

    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': api_key
    }

    response = requests.get(base_search_url, params=params)
    response.raise_for_status()  # Check for HTTP errors before processing the data
    response_data = response.json()
    video_id = response_data.get("items", [{}])[0].get('id', {}).get('videoId')

    return f"https://www.youtube.com/watch?v={video_id}" if video_id else "Video not found!"


@app.route("/webhook", methods=["POST"])
def announce_new_releases_from_jellyfin():
    try:
        payload = json.loads(request.data)

        if payload.get("ItemType") == "Movie":

            movie_name = payload.get("Name")
            movie_id = payload.get("ItemId")
            release_year = payload.get("Year")
            overview = payload.get("Overview")
            runtime = payload.get("RunTime")
            # Remove release_year from movie_name if present
            movie_name_cleaned = movie_name.replace(f" ({release_year})", "").strip()

            trailer_url = get_youtube_trailer_url(f"{movie_name_cleaned} Trailer {release_year}")

            notification_message = (
                f"*🍿New Movie Added🍿*\n\n*{movie_name_cleaned}* *({release_year})*\n\n{overview}\n\n"
                f"Runtime\n{runtime}")

            if trailer_url:
                notification_message += f"\n\n[🎥]({trailer_url})[Trailer]({trailer_url})"

            send_telegram_photo(movie_id, notification_message)
            logging.info(f"(Movie) {movie_name} {release_year} "
                         f"notification was sent to telegram.")
            return "Movie notification was sent to telegram"

        if payload.get("ItemType") == "Season":

            series_name = payload.get("SeriesName")
            season_id = payload.get("ItemId")
            season = payload.get("Name")
            release_year = payload.get("Year")
            season_details = get_item_details(season_id)
            series_id = season_details["Items"][0].get("SeriesId")
            series_details = get_item_details(series_id)
            # Remove release_year from series_name if present
            series_name_cleaned = series_name.replace(f" ({release_year})", "").strip()

            # Get series overview if season overview is empty
            overview_to_use = payload.get("Overview") if payload.get("Overview") else series_details["Items"][0].get(
                "Overview")

            notification_message = (
                f"*New Season Added*\n\n*{series_name_cleaned}* *({release_year})*\n\n"
                f"*{season}*\n\n{overview_to_use}\n\n")

            response = send_telegram_photo(season_id, notification_message)

            if response.status_code == 200:
                logging.info(f"(Season) {series_name_cleaned} {season} "
                             f"notification was sent to telegram.")
                return "Season notification was sent to telegram"
            else:
                send_telegram_photo(series_id, notification_message)
                logging.warning(f"{series_name_cleaned} {season} image does not exists, falling back to series image")
                logging.info(f"(Season) {series_name_cleaned} {season} notification was sent to telegram")
                return "Season notification was sent to telegram"

        if payload.get("ItemType") == "Episode":

            item_id = payload.get("ItemId")
            file_details = get_item_details(item_id)
            season_id = file_details["Items"][0].get("SeasonId")
            episode_premiere_date = file_details["Items"][0].get("PremiereDate", "0000-00-00T").split("T")[0]
            season_details = get_item_details(season_id)
            series_id = season_details["Items"][0].get("SeriesId")
            season_date_created = season_details["Items"][0].get("DateCreated", "0000-00-00T").split("T")[0]
            item_name = payload.get("SeriesName")
            epi_name = payload.get("Name")
            season_num = payload.get("SeasonNumber00")
            season_epi = payload.get("EpisodeNumber00")
            overview = payload.get("Overview")

            if not is_not_within_last_x_days(season_date_created, SEASON_ADDED_WITHIN_X_DAYS):
                logging.info(f"(Episode) {item_name} Season {season_num} "
                             f"was added within the last 3 days. Not sending notification.")
                return "Season was added within the last 3 days. Not sending notification."

            if episode_premiere_date and is_within_last_x_days(episode_premiere_date,
                                                               EPISODE_PREMIERED_WITHIN_X_DAYS):

                notification_message = (
                    f"*New Episode Added*\n\n*Release Date*: {episode_premiere_date}\n\n*Series*: {item_name} *S*"
                    f"{season_num}*E*{season_epi}\n*Episode Title*: {epi_name}\n\n{overview}\n\n"
                )
                response = send_telegram_photo(season_id, notification_message)

                if response.status_code == 200:
                    logging.info(f"(Episode) {item_name} S{season_num}E{season_epi} notification sent to Telegram!")
                    return "Notification sent to Telegram!"
                else:
                    send_telegram_photo(series_id, notification_message)
                    logging.warning(f"(Episode) {item_name} season image does not exists, falling back to series image")
                    logging.info(f"(Episode) {item_name} S{season_num}E{season_epi} notification sent to Telegram!")
                    return "Notification sent to Telegram!"

            else:
                logging.info(f"(Episode) {item_name} S{season_num}E{season_epi} "
                             f"was premiered more than {EPISODE_PREMIERED_WITHIN_X_DAYS} "
                             f"days ago. Not sending notification.")
                return (f"Episode was added more than {EPISODE_PREMIERED_WITHIN_X_DAYS} "
                        f"days ago. Not sending notification.")
        logging.error('Item Type Not Supported')
        return "Item type not supported."

    # Handle specific HTTP errors
    except HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        return str(http_err)

    # Handle generic exceptions
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
