#!/usr/bin/env python3

import logging
from os import path, system, chdir
from time import sleep
from typing import Dict, List

from requests import get, status_codes

# create a file that contains a dictionary called "credentials" with email and postmark credentials
from emailing import credentials

STATE = "PA"
CITY = "PITTSBURGH"
QUERY_INTERVAL = 5 * 60  # seconds

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
      -X POST \
      -H "Accept: application/json" \
      -H "Content-Type: application/json" \
      -H "X-Postmark-Server-Token: {smtp["Username"]}" \
      -d '{{
            "From": "{smtp["Email"]}",
            "To": "{smtp["Email"]}",
            "Subject": "COVID Vaccine Booking Availability",
            "HtmlBody": "{text}"
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


def is_available(vaccine_info: List[Dict], city: str) -> bool:
    for loc in vaccine_info:
        if loc["city"] == city:
            return loc["status"] != FULL
    return False


if __name__ == "__main__":
    logging.info("Beginning vaccine query loop")
    while True:
        response = query_vaccine_info(STATE)
        location_data = response["responsePayloadData"]["data"]

        if is_available(location_data[STATE], CITY):
            send_email(f"There's a vaccine appointment available in {CITY}")
            logging.info("sending email!")

        sleep(QUERY_INTERVAL)
