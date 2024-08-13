import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from siff_scraper import scrape_showings
from model import MovieShowing, ShowTime, Theatre
from util import parse_int, get_logger

credentials_file = 'credentials.json'
token_file = 'token.json'
calendar_id = 'd9ad77d20a018d11c20560b1ceb55b92c5b64ee10b322ac2c7da39e178aa17fc@group.calendar.google.com'

# Scopes required by the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

logger = get_logger(__name__)


def _get_credentials():
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
        # If there are no (valid) credentials available, let the user log in.

    if not (credentials and credentials.valid):
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(credentials.to_json())
    return credentials


def _extract_movie(calendar_event) -> MovieShowing:
    title = calendar_event["summary"].lstrip("Movie: ")[:-len("(YEAR)")].strip()
    year = str(parse_int(calendar_event["summary"][-len("(YEAR)"):]))
    showtime = datetime.fromisoformat(calendar_event["start"]["dateTime"])
    # create a minimal movie showing with only the attributes used in the hash function
    return MovieShowing(title=title,
                        year=year,
                        showtime=ShowTime(showtime, showtime),
                        director=str(), description=str(), location=str(), link=str(), duration_minutes=-1)


def _create_event(movie: MovieShowing):
    return {
        "summary": f"Movie: {movie.title} ({movie.year})",
        "location": movie.location,
        "description": f"Director: {movie.director}\n{movie.description}\n---\n{movie.link}",
        "start": {"dateTime": movie.showtime.start_time.isoformat(timespec="seconds"),
                  'timeZone': 'America/Los_Angeles'},
        "end": {"dateTime": movie.showtime.end_time.isoformat(timespec="seconds"),
                'timeZone': 'America/Los_Angeles'}
    }


def update_calendar(theatre: Theatre = Theatre.SIFF_CINEMA_EGYPTIAN):
    api_credentials = _get_credentials()
    service = build('calendar', 'v3', credentials=api_credentials)

    events = service.events().list(calendarId=calendar_id).execute()
    current_showings = {_extract_movie(e) for e in events["items"]}
    for showing in scrape_showings(theatre):
        if showing not in current_showings:
            event = _create_event(showing)
            service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created: {event['summary']}, {event['start']['dateTime']}")


if __name__ == '__main__':
    update_calendar()
