import logging
import re
from datetime import datetime, timedelta

import pytz

MILLISEC_PER_SEC = 1000
PACIFIC_TIMEZONE = pytz.timezone('America/Los_Angeles')


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
