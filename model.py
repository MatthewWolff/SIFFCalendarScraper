from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


# the string value must match the one used in the URL
class Theatre(StrEnum):
    SIFF_CINEMA_EGYPTIAN = "siff-cinema-egyptian"
    SIFF_CINEMA_DOWNTOWN = "siff-cinema-downtown"
    SIFF_CINEMA_UPTOWN = "siff-cinema-uptown"
    SIFF_FILM_CENTER = "siff-film-center"


@dataclass
class ShowTime:
    start_time: datetime
    end_time: datetime


@dataclass
class HashableMovieEvent:
    title: str
    year: str
    location: str
    showtime: ShowTime

    def __make_id_string(self):
        return f"{self.title} {self.year} {self.showtime.start_time.isoformat(timespec="seconds")} {self.location}"

    def __eq__(self, other):
        return other and self.__make_id_string() == other.__make_id_string()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__make_id_string())


@dataclass
class MovieShowing(HashableMovieEvent):
    title: str
    director: str
    country: str
    year: str
    description: str
    link: str
    location: str
    duration_minutes: int
    showtime: ShowTime

    __hash__ = HashableMovieEvent.__hash__
    __eq__ = HashableMovieEvent.__eq__
    __ne__ = HashableMovieEvent.__ne__
