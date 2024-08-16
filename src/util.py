import logging
import os
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from src.constants import GoogleCalendar, PACIFIC_TIMEZONE, MILLISEC_PER_SEC
from src.model import ShowTime


def get_logger(filename, level=logging.INFO):
    logger = logging.getLogger(filename)
    logging.basicConfig(encoding='utf-8',
                        level=level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logger


def parse_int(text):
    nums = re.findall(r'\d+', text)
    if nums:
        return int(nums[0])
    else:
        raise ValueError(f"No integers found in string: {text}")


def get_date_delta(days_from_now: int) -> str:
    date = datetime.now(PACIFIC_TIMEZONE) + timedelta(days=days_from_now)
    return date.strftime("%Y-%m-%d")


def get_datetime_from_milliseconds(data_time):
    epoch_seconds = parse_int(data_time) / MILLISEC_PER_SEC
    return datetime.fromtimestamp(epoch_seconds, tz=PACIFIC_TIMEZONE)


def is_parseable_as_int(string) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False


def get_calendar_name(calendar: GoogleCalendar) -> str:
    return next(name for name, value in vars(GoogleCalendar).items() if value == calendar.value)


def read_html_files(directory):
    html_files = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                directory_path, _ = os.path.split(relative_path)

                if directory_path not in html_files:
                    html_files[directory_path] = {}

                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = BeautifulSoup(f.read(), 'html.parser')
                    html_files[directory_path][file] = html_content

    return html_files


def assert_equal_showtime(t1: ShowTime, t2: ShowTime) -> bool:
    return (t1.start_time.replace(tzinfo=None) == t2.start_time.replace(tzinfo=None) and
            t1.end_time.replace(tzinfo=None) == t2.end_time.replace(tzinfo=None))
