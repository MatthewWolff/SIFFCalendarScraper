import json
from functools import cache
from typing import List

import requests
from bs4 import BeautifulSoup

from constants import SIFFTheatre
from model import ShowTime, MovieShowing
from util import *

SIFF_ROOT = "https://siff.net"

logger = get_logger(__name__)


def scrape_showings(theatre: SIFFTheatre = SIFFTheatre.EGYPTIAN, interval_days=7) -> List[MovieShowing]:
    assert theatre in SIFFTheatre
    assert interval_days > 0

    movies = list()
    for i in range(interval_days):
        dated_url = f"{SIFF_ROOT}/cinema/cinema-venues/{theatre}?day={i}"
        showings = scrape_page_calendar(dated_url)
        if not showings:
            logger.warning(f"No movie listing found for provided date ({get_date_delta(i)}) at {theatre}")
        movies.extend(showings)

    movies_playing = ", ".join(set(f"{m.title} ({m.year})" for m in movies))
    logger.info(f"Found {len(movies)} showings for the week of {get_date_delta(0)} for {theatre}")
    logger.info(f"Movies currently playing at {theatre}: {movies_playing}")
    return movies


def scrape_page_calendar(url) -> List[MovieShowing]:
    logger.debug(f"Scraping {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    logger.debug("Successfully retrieved soup content")

    all_daily_showings = list()
    movie_listings = soup.find('div', class_='listing')
    if not movie_listings:
        logger.debug("No valid screenings found")
        return all_daily_showings

    for movie in movie_listings.find_all("div", class_="item"):
        logger.debug(f"Movie element: {movie}")
        title_element = movie.find('h3')
        daily_showings = _extract_showings(movie)
        locations = _extract_locations(movie)
        meta = _get_metadata(meta_source=movie.find('div', class_='small-copy'),
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


def _get_metadata(meta_source, reference_showing) -> List[str]:
    """
    Some movies have partial metadata, so we correct it here
    :param meta_source: the element containing metadata
    :param reference_showing: an extract showing to reference for duration
    :return: a list of metadata
    """
    meta = [m.strip() for m in meta_source.find('p', class_='meta').text.split("|")]
    logger.debug(f"Extracted metadata: {meta}")
    if len(meta) != 4:
        logger.warning(f"Attempting to correct incomplete metadata ({meta})")
        fallback_year = f"{reference_showing.start_time.year}*"
        if len(meta) == 1:
            logger.warning(f"Missing most of metadata...")
            if "min." in meta[0]:
                logger.warning("Assuming duration, filling other fields with unknown")
                meta = ["Unknown Country", fallback_year, meta[0], "Unknown Director"]
            elif is_parseable_as_int(meta[0]):
                logger.warning("Detected year - filling other fields with unknown")
                meta = ["Unknown Country", meta[0], "Unknown Duration", "Unknown Director"]
            else:
                meta = ["Unknown Country", fallback_year, "Unknown Duration", "Unknown Director"]
        elif len(meta) == 3:
            if is_parseable_as_int(meta[0]):
                logger.warning("Detected missing country - filling with unknown")
                meta = ["Unknown Country"] + meta
            else:
                logger.warning("Assuming missing duration...")
                meta = [meta[0],  # country
                        meta[1],  # year
                        str((reference_showing.end_time - reference_showing.start_time).seconds // 60) + " min.",
                        meta[2]]  # director
        else:
            logger.warning("... Missing too much of metadata")
            meta = ["Unknown Country", fallback_year, "Unknown Duration", "Unknown Director"]
        logger.warning(f"Corrected metadata: {meta}")
    return meta


def _get_movie_link(title_element) -> str:
    return SIFF_ROOT + title_element.find('a').get('href')


@cache
def _get_description(title_page_url) -> str:
    """
    Extracts the movie description by following the link to the movie page. Cached to avoid repeated requests
    """
    logger.debug(f"Retrieving description from {title_page_url}")
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
    print(*scrape_showings(SIFFTheatre.EGYPTIAN, interval_days=7), sep="\n")
