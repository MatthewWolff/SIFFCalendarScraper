# SIFFCalendarScraper
A little web scraping project for creating a calendar that will be populated with SIFF movies, specifically the Egyptian

Join the calendar: https://calendar.google.com/calendar/u/0?cid=ZDlhZDc3ZDIwYTAxOGQxMWMyMDU2MGIxY2ViNTViOTJjNWI2NGVlMTBiMzIyYWMyYzdkYTM5ZTE3OGFhMTdmY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t

This script can be configured to scrape events from any of the SIFF theatres—this can be done
by updating the `theatre` parameter with any of the available enum values
## Set up
Per https://developers.google.com/calendar/api/quickstart/python
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
or just simply 
```bash
pip3 install -r requirements.txt
```

Then, create a project API key that allows for scope with Google Calendar API. Download the credential file as `credentials.json`

Run the runner 
```bash
./runner
```