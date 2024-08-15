# Variables
PACKAGE_NAME = SIFFCalendarScraper

# Commands
.PHONY: test clean install

test:
	pytest

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

install:
	pip install -r requirements.txt