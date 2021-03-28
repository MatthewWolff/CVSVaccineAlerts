#!/usr/bin/env python3

import logging
from os import path, system, chdir
from time import sleep
from typing import Dict, List

from requests import get, status_codes

# create a file that contains a dictionary called "credentials" with email and postmark credentials
from emailing import credentials

STATE = "PA"
CITIES = {"PITTSBURGH", "WASHINGTON", "CARNEGIE", "AMBRIDGE", "BUTLER", "ELLWOOD CITY", "GIBSONIA", "HOMESTEAD",
          "MASONTOWN", "MONACA", "NEW KENSINGTON", "NORTH HUNTINGTON", "SWISSVALE", "WHITEHALL", "WILKINSBURG"}
QUERY_INTERVAL = 5 * 60  # seconds
LOG_INTERVAL = 12 * 5  # query intervals
REFRACTORY_INTERVAL = 12 * 2  # query intervals (to avoid constant reminders)

# only remind again after the refractory interval
LOCATION_REFRACTORIES = dict()

# no touch
FULL = "Fully Booked"
if path.dirname(__file__) != "":
    chdir(path.dirname(__file__))
logging.basicConfig(filename='vaccineQuerying.log',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')

if not path.exists("emailing.py"):
    exit("Missing email credentials (emailing.py). make a free account with postmarkapp.com "
         "(automated emailing from python with gmail tends to get stopped by Google account security)\n"
         "You can then add your credentials to emailing.py as a dictionary")


def send_email(text) -> None:
    smtp = {
        "Server": "smtp.postmarkapp.com",
        "Ports": "25, 2525, or 587",
        "Username": credentials["Username"],
        "Password": credentials["Password"],
        "Authentication": "Plain text, CRAM-MD5, or TLS",
        "Email": credentials["Email"],
    }
    string = f"""
    curl "https://api.postmarkapp.com/email" \
      --silent \
      -X POST \
      -H "Accept: application/json" \
      -H "Content-Type: application/json" \
      -H "X-Postmark-Server-Token: {smtp["Username"]}" \
      -d '{{
            "From": "{smtp["Email"]}",
            "To": "{smtp["Email"]}",
            "Subject": "COVID Vaccine Booking Availability",
            "HtmlBody": "{text}. Appointment link: https://www.cvs.com/vaccine/intake/store/cvd-schedule?icid=coronavirus-lp-vaccine-pa-statetool "
          }}'"""
    system(string)
    print()  # flush buffer


def query_vaccine_info(state: str = "PA") -> Dict:
    url = f"https://www.cvs.com/immunizations/covid-19-vaccine.vaccine-status.{state}.json?vaccineinfo"
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.cvs.com/immunizations/covid-19-vaccine?icid=cvs-home-hero1-link2-coronavirus-vaccine',
        'Cookie': 'pe=p1'  # might be unnecessary
    }
    r = get(url, headers=headers)
    if r.status_code == status_codes.codes.ok:
        resp = r.json()
    else:
        logging.error(r.text)
        raise Exception(f"Unable to complete query, status code was {r.status_code}.\n{r.text}")

    return resp


def available_locations(vaccine_info: List[Dict]) -> List[str]:
    return [loc["city"] for loc in vaccine_info if loc["city"] in CITIES and loc["status"] != FULL]


def check_refractories(locations: List[str]) -> List[str]:
    return [c for c in locations if c not in LOCATION_REFRACTORIES]


def decrement_refractories():
    for key in list(LOCATION_REFRACTORIES.keys()):
        LOCATION_REFRACTORIES[key] -= 1
        if LOCATION_REFRACTORIES[key] == 0:
            del LOCATION_REFRACTORIES[key]


def set_refractories(remindable_locations):
    for loc in remindable_locations:
        LOCATION_REFRACTORIES[loc] = REFRACTORY_INTERVAL


if __name__ == "__main__":
    logging.info("Beginning vaccine query loop")
    counter = 0
    while True:
        response = query_vaccine_info(STATE)
        location_data = response["responsePayloadData"]["data"]

        # check what's available, also check we haven't reminded recently
        availabilities = check_refractories(available_locations(location_data[STATE]))
        if availabilities:
            set_refractories(availabilities)
            send_email(f"There is a vaccine appointment available in {', '.join(availabilities)}")
            logging.info(f"sending email! ({', '.join(availabilities)})")

        # log when active for a certain length of time
        counter += 1
        if counter % LOG_INTERVAL == 0:
            logging.info(f"active for {counter * QUERY_INTERVAL / 60 / 60} hours")

        # decrement reminder timers
        decrement_refractories()
        sleep(QUERY_INTERVAL)
