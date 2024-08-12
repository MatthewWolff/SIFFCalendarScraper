import json
from typing import List

import requests
from bs4 import BeautifulSoup

from model import ShowTime, MovieShowing
from util import *

SIFF_ROOT = "https://siff.net"

logger = get_logger(__name__)


def scrape_showings(interval_days=7) -> List[MovieShowing]:
    movies = list()
    for i in range(interval_days):
        dated_url = f"{SIFF_ROOT}/cinema/cinema-venues/siff-cinema-egyptian?day={i}"
        showings = scrape_page_calendar(dated_url)
        if not showings:
            logger.warning(f"No movie listing found for provided date ({get_date_delta(i)})")
        movies.extend(showings)

    movies_playing = ", ".join(set(f"{m.title} ({m.year})" for m in movies))
    logger.info(f"Found {len(movies)} showings for the week of {get_date_delta(0)}")
    logger.info(f"Movies currently playing are: {movies_playing}")
    return movies


def scrape_page_calendar(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    all_daily_showings = list()
    movie_listings = soup.find('div', class_='listing')
    if not movie_listings:
        return all_daily_showings

    for movie in movie_listings.find_all("div", class_="item"):
        meta = [m.strip() for m in movie.find('p', class_='meta').text.split("|")]
        title_element = movie.find('h3')
        daily_showings = _extract_showings(movie)

        for showing in daily_showings:
            all_daily_showings.append(MovieShowing(
                title=title_element.text.strip(),
                year=meta[1],
                director=meta[3],
                description=_get_description(title_element),
                link=_get_movie_link(title_element),
                location=_extract_location(movie)[0],  # all showings will be at same location per movie
                duration_minutes=parse_int(meta[2]),
                showtime=showing
            ))

    return all_daily_showings


def _get_movie_link(title_element) -> str:
    return SIFF_ROOT + title_element.find('a').get('href')


def _get_description(title_element) -> str:
    response = requests.get(_get_movie_link(title_element))
    soup = BeautifulSoup(response.content, 'html.parser')
    description_element = soup.find("div", class_="body-copy").find("p")
    description = "".join(description_element.strings)  # ignore HTML formatting elements
    return description


def __extract_metadata(metadata_function, movie) -> List:
    metadata = list()
    for screening_time in movie.find('div', class_='button-group').find_all('a'):
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

    return __extract_metadata(extract_showing, movie)


def _extract_location(movie) -> List[str]:
    def extract_location(data) -> str:
        return (f"{data['VenueName']}, {data['VenueAddress1']}, "
                f"{data['VenueCity']}, {data['VenueState']} {data['VenueZipCode']}")

    return __extract_metadata(extract_location, movie)


if __name__ == '__main__':
    print(*scrape_showings(7), sep="\n")
