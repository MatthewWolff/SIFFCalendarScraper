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
class MovieShowing:
    title: str
    director: str
    year: str
    description: str
    link: str
    location: str
    duration_minutes: int
    showtime: ShowTime

    # define hashing
    def __eq__(self, other):
        return (other and
                f"{self.title} ({self.year})" == f"{other.title} ({other.year})" and
                self.showtime.start_time.isoformat(timespec="seconds") ==
                other.showtime.start_time.isoformat(timespec="seconds"))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((f"{self.title} ({self.year})", self.showtime.start_time.isoformat(timespec="seconds")))
