import os.path
import re
from datetime import datetime
from typing import Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.constants import SIFFTheatre, GoogleCalendar
from src.model import MovieShowing, ShowTime, HashableMovieEvent
from src.siff_scraper import scrape_showings
from src.util import get_logger, get_calendar_name

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
MOVIE_TITLE_PREFIX = "[Movie] "
FORMATTED_YEAR_REGEX = r"\(\d{4}\*?\)"

# Scopes required by the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

logger = get_logger(__name__)


def _get_credentials() -> Credentials:
    logger.debug("Retrieving credentials")
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        logger.debug("Found existing token file")
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # If there are no (valid) credentials available, let the user log in.

    if not (credentials and credentials.valid):
        if credentials and credentials.expired and credentials.refresh_token:
            logger.warning("Refreshing expired token")
            credentials.refresh(Request())
        else:
            logger.critical("New credentials required")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())
    return credentials


def _extract_movie(calendar_event) -> HashableMovieEvent:
    """
    Extract a MovieEvent from the calendar event
    """

    def extract_formatted_year(year_string: str) -> str:
        """
        Extract the formatted year from a string. Some years have an asterisk, so handle accordingly
        """
        match = re.search(FORMATTED_YEAR_REGEX, year_string)
        if match:
            return match.group()

    formatted_year = extract_formatted_year(calendar_event["summary"])
    title = calendar_event["summary"][len(MOVIE_TITLE_PREFIX):][:-len(formatted_year)].strip()
    year = formatted_year.strip("()")
    showtime = datetime.fromisoformat(calendar_event["start"]["dateTime"])
    location = calendar_event["location"]
    return HashableMovieEvent(title=title, year=year, showtime=ShowTime(showtime, None), location=location)


def _create_event(movie: MovieShowing) -> Dict:
    return {
        "summary": f"{MOVIE_TITLE_PREFIX}{movie.title} ({movie.year})",
        "location": movie.location,
        "description": f"Director: {movie.director} - {movie.country}\n{movie.description}\n---\n{movie.link}" +
                       ("\n\n* = year was unspecified, assuming this year" if "*" in movie.year else ""),
        "start": {"dateTime": movie.showtime.start_time.isoformat(timespec="seconds"),
                  'timeZone': 'America/Los_Angeles'},
        "end": {"dateTime": movie.showtime.end_time.isoformat(timespec="seconds"),
                'timeZone': 'America/Los_Angeles'},
        "visibility": "public",
        "transparency": "transparent",  # non-blocking on calendar
        "reminders": {"useDefault": False}  # don't send reminders
    }


def get_calendar_events(service, calendar_id: GoogleCalendar, future_only=False) -> list:
    logger.debug(f"Retrieving existing events from Google Calendar - {get_calendar_name(calendar_id)}")
    events = service.events().list(calendarId=calendar_id).execute().get('items', list())
    logger.info(f"Found {len(events)} existing events on calendar - {get_calendar_name(calendar_id)}")
    logger.debug(f"Filtering calendar events for future: {future_only}")

    # assume no showings are from before January 1st, 1970
    filter_date = (datetime.today() if future_only else datetime.fromtimestamp(int())).date()
    filter_datetime = datetime(filter_date.year, filter_date.month, filter_date.day).isoformat(timespec="seconds")
    filtered_events = [event for event in events if event["start"]["dateTime"] > filter_datetime]
    if future_only:
        logger.info(f"Found {len(filtered_events)} future events on calendar - {get_calendar_name(calendar_id)}")
    return filtered_events


def update_calendar(calendar_id: GoogleCalendar, theatre: SIFFTheatre):
    api_credentials = _get_credentials()
    service = build('calendar', 'v3', credentials=api_credentials)

    current_showings = {_extract_movie(e) for e in get_calendar_events(service, calendar_id, future_only=True)}
    for showing in scrape_showings(theatre):
        if showing not in current_showings:
            event = _create_event(showing)
            response = service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created at {theatre} - {event['summary']}, {event['start']['dateTime']}"
                        f"- {response.get('htmlLink')}")

    deactivate_reminders(calendar_id, service)


def deactivate_reminders(calendar_id: GoogleCalendar, service=None):
    """
    The API can mess up sometimes and add reminders. Iterate through events to flag them and remove reminders
    """
    if not service:
        service = build('calendar', 'v3', credentials=_get_credentials())
    for event in get_calendar_events(service, calendar_id, future_only=True):
        if event['reminders'].get("overrides", list()):
            event_info = f"{get_calendar_name(calendar_id)} - {event['start']['dateTime']} - {event['summary']}"
            logger.warning(f"Deactivate event with reminders: {event_info}")
            event['reminders'] = {"useDefault": False}
            service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()


def wipe_calendar(calendar_id: GoogleCalendar, future_only=False):
    api_credentials = _get_credentials()
    service = build('calendar', 'v3', credentials=api_credentials)

    for event in get_calendar_events(service, calendar_id, future_only=future_only):
        service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
        logger.info(f"Deleted: {get_calendar_name(calendar_id)} - {event['summary']}, {event['start']['dateTime']}")


if __name__ == '__main__':
    # wipe_events(GoogleCalendar.SIFF_CINEMA_UPTOWN, SIFFTheatre.UPTOWN)
    update_calendar(GoogleCalendar.SIFF_CINEMA_UPTOWN, SIFFTheatre.UPTOWN)
