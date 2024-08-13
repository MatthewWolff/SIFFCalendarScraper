import json
from functools import cache
from typing import List

import requests
from bs4 import BeautifulSoup

from model import ShowTime, MovieShowing, Theatre
from util import *

SIFF_ROOT = "https://siff.net"

logger = get_logger(__name__)


def scrape_showings(theatre: Theatre = Theatre.SIFF_CINEMA_EGYPTIAN, interval_days=7) -> List[MovieShowing]:
    assert theatre in Theatre
    assert interval_days > 0

    movies = list()
    for i in range(interval_days):
        dated_url = f"{SIFF_ROOT}/cinema/cinema-venues/{theatre.value}?day={i}"
        showings = scrape_page_calendar(dated_url)
        if not showings:
            logger.warning(f"No movie listing found for provided date ({get_date_delta(i)}) at {theatre.value}")
        movies.extend(showings)

    movies_playing = ", ".join(set(f"{m.title} ({m.year})" for m in movies))
    logger.info(f"Found {len(movies)} showings for the week of {get_date_delta(0)}")
    logger.info(f"Movies currently playing are: {movies_playing}")
    return movies


def scrape_page_calendar(url):
    logging.debug(f"Scraping {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    logging.debug("Successfully retrieved soup content")

    all_daily_showings = list()
    movie_listings = soup.find('div', class_='listing')
    if not movie_listings:
        logging.debug("No valid screenings found")
        return all_daily_showings

    for movie in movie_listings.find_all("div", class_="item"):
        logging.debug(f"Movie element: {movie}")
        title_element = movie.find('h3')
        daily_showings = _extract_showings(movie)
        locations = _extract_locations(movie)
        meta = get_metadata(meta_source=movie.find('div', class_='small-copy'),
                            reference_showing=daily_showings[0] if daily_showings else None)

        for showing, location in zip(daily_showings, locations):
            movie_link = _get_movie_link(title_element)
            all_daily_showings.append(MovieShowing(
                title=title_element.text.strip(),
                year=meta[1],
                director=meta[3],
                country=meta[0],
                description=_get_description(movie_link),
                link=movie_link,
                location=location,
                duration_minutes=parse_int(meta[2]),
                showtime=showing
            ))

    return all_daily_showings


def get_metadata(meta_source, reference_showing):
    """
    Some movies have partial metadata (missing duration), so we correct it here
    :param meta_source: the element containing metadata
    :param reference_showing: an extract showing to reference for duration
    :return: a list of metadata
    """
    meta = [m.strip() for m in meta_source.find('p', class_='meta').text.split("|")]
    logging.debug(f"Extracted metadata: {meta}")
    if len(meta) == 3 and reference_showing:
        logging.warning(f"Correcting incomplete metadata ({meta})")
        meta = [meta[0],  # country
                meta[1],  # year
                str((reference_showing.end_time - reference_showing.start_time).seconds // 60),  # duration
                meta[2]]  # director
        logging.warning(f"Corrected metadata: {meta}")
    return meta


def _get_movie_link(title_element) -> str:
    return SIFF_ROOT + title_element.find('a').get('href')


@cache
def _get_description(title_page_url) -> str:
    """
    Extracts the movie description by following the link to the movie page. Cached to avoid repeated requests
    """
    logging.debug(f"Retrieving description from {title_page_url}")
    response = requests.get(title_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    description_element = soup.find("div", class_="body-copy").find("p")
    description = "".join(description_element.strings)  # ignore HTML formatting elements
    return description


def __extract_screening_data(metadata_function, movie) -> List:
    """
    Extracts the JSON object containing screening data and parses it with the provided function
    """
    metadata = list()
    for screening_time in movie.find('div', class_='times').find_all('a'):
        data_screening = screening_time.get('data-screening')
        if data_screening:
            data = json.loads(data_screening)
            metadata.append(metadata_function(data))
    return metadata


def _extract_showings(movie) -> List[ShowTime]:
    def extract_showing(screening_data) -> ShowTime:
        start_time = get_datetime_from_milliseconds(screening_data["Showtime"])
        end_time = get_datetime_from_milliseconds(screening_data["ShowtimeEnd"])
        return ShowTime(start_time, end_time)

    return __extract_screening_data(extract_showing, movie)


def _extract_locations(movie) -> List[str]:
    def extract_location(data) -> str:
        return (f"{data['VenueName']}, {data['VenueAddress1']}, "
                f"{data['VenueCity']}, {data['VenueState']} {data['VenueZipCode']}")

    return __extract_screening_data(extract_location, movie)


if __name__ == '__main__':
    print(*scrape_showings(Theatre.SIFF_CINEMA_UPTOWN, interval_days=7), sep="\n")
