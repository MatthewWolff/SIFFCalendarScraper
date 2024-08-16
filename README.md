# SIFFCalendarScraper

A little web scraping project for populating subscribable Google Calendars with weekly SIFF movie screenings! (not
affiliated with SIFF)

## Join one of the calendars - [linktr.ee/SIFFCalendars](https://linktr.ee/SIFFCalendars)

### Getting Started

1. Getting API Credentials
    * In order to run this code, you'll need to get set up with the Google calendars
      API: https://developers.google.com/calendar/api/quickstart/python
2. Update the workspace + constants
    * Once you have your API credentials, create a file in the workspace root called `credentials.json`
    * You'll then need to update the [`constants.py`](./constants.py) so that the `GoogleCalendar` enum points at your
      calendar(s)
      You can then run the following comma
3. Install dependencies
    ```bash
    make install
    ```
   Alternatively, you can set up a virtual environment to avoid polluting your global pip environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run it! It will print logs to standard out as well as to a log file
   ```bash
   ./runner  # note: if you're using a venv, you'll need to update the runner's shebang
   ```
5. Set up a crontab with `crontab -e`. I added this line so that it runs twice a day: 
   ```cronexp
   0 8,17 * * * /home/matthew/SIFFCalendarScraper/runner >> calendar.error.log 2>&1
   ```
   Because I'm running this on a raspberry-pi, I created a separate branch for pi-specific changes. Here's the diff: [raspberry-pi](https://github.com/MatthewWolff/SIFFCalendarScraper/compare/main...raspberry-pi) 