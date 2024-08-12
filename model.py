from dataclasses import dataclass
from datetime import datetime


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
    duration_minutes: int
    showtime: ShowTime
