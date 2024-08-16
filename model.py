from dataclasses import dataclass
from datetime import datetime


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
        stripped_datetime = self.showtime.start_time.replace(tzinfo=None)
        return f"{self.title} {self.year} {stripped_datetime.isoformat(timespec='seconds')} {self.location}"

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
