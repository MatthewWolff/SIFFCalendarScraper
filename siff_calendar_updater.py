import logging
import os.path
from datetime import datetime
from typing import Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from model import MovieShowing, ShowTime, Theatre, HashableMovieEvent
from siff_scraper import scrape_showings
from util import parse_int, get_logger

credentials_file = 'credentials.json'
token_file = 'token.json'

# Scopes required by the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

logger = get_logger(__name__)


def _get_credentials() -> Credentials:
    logging.debug("Retrieving credentials")
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        logging.debug("Found existing token file")
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
        # If there are no (valid) credentials available, let the user log in.

    if not (credentials and credentials.valid):
        if credentials and credentials.expired and credentials.refresh_token:
            logging.debug("Refreshing expired token")
            credentials.refresh(Request())
        else:
            logging.warning("New credentials required")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(credentials.to_json())
    return credentials


def _extract_movie(calendar_event) -> HashableMovieEvent:
    """
    Extract a MovieEvent from the calendar event
    """
    title = calendar_event["summary"].lstrip("Movie: ")[:-len("(YEAR)")].strip()
    year = str(parse_int(calendar_event["summary"][-len("(YEAR)"):]))
    showtime = datetime.fromisoformat(calendar_event["start"]["dateTime"])
    location = calendar_event["location"]
    return HashableMovieEvent(title=title, year=year, showtime=ShowTime(showtime, None), location=location)


def _create_event(movie: MovieShowing) -> Dict:
    return {
        "summary": f"Movie: {movie.title} ({movie.year})",
        "location": movie.location,
        "description": f"Director: {movie.director} - {movie.country}\n{movie.description}\n---\n{movie.link}",
        "start": {"dateTime": movie.showtime.start_time.isoformat(timespec="seconds"),
                  'timeZone': 'America/Los_Angeles'},
        "end": {"dateTime": movie.showtime.end_time.isoformat(timespec="seconds"),
                'timeZone': 'America/Los_Angeles'},
        "visibility": "public",
        "transparency": "transparent",  # non-blocking on calendar
        "reminders": {"useDefault": False}  # don't send reminders
    }


def update_calendar(calendar_id, theatre: Theatre = Theatre.SIFF_CINEMA_EGYPTIAN):
    api_credentials = _get_credentials()
    service = build('calendar', 'v3', credentials=api_credentials)

    logger.debug("Retrieving existing events from Google Calendar")
    events = service.events().list(calendarId=calendar_id).execute()
    logger.info(f"Found {len(events['items'])} existing events on calendar")
    current_showings = {_extract_movie(e) for e in events["items"]}
    for showing in scrape_showings(theatre):
        if showing not in current_showings:
            event = _create_event(showing)
            response = service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created: {event['summary']}, {event['start']['dateTime']} - {response.get('htmlLink')}")


if __name__ == '__main__':
    cid = 'd9ad77d20a018d11c20560b1ceb55b92c5b64ee10b322ac2c7da39e178aa17fc@group.calendar.google.com'
    update_calendar(cid)
