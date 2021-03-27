# Vaccine Alerts
CVS has an API for querying vaccine appointment availabilities. This takes advantage of that to create an email alert for whichever cities in your state you'd like.

See the CVS Vaccine availability web-page [here](https://www.cvs.com/immunizations/covid-19-vaccine). All I did was extract their API query and use it in my code.

## Requirements
* Python 3.7
* `requests` module (`pip3 install requests`)
* [postmarkapp](https://postmarkapp.com/) trial account (for emailing)

---
# Setup - email
Postmarkapp is something that I found as a replacement for gmail because Google security would randomly block me from emailing myself through SMTP. The *downside* is that it requires a private domain email address, which I'm fortunate enough to have. 

You can just re-write the `send_email(text)` method for whatever your preferred programmatic emailing method is.

## Setting up postmark
* Make a postmark account
* Create a server
* Click "SMTP"
* Grab the username and password
* Create a file called `emailing.py` with those credentials in it as a dictionary

```python
credentials = {
    "Username": "grab-username-2r38r90",
    "Password": "grab-password-2r38r90",
    "Email": "your-email@chi-squared.org"
}
```

## Setting up the script
You can customize it for various states and cities by changing the variables at the top of the script
```python
STATE = "PA"
CITIES = {"PITTSBURGH", "CARNEGIE"}
```

By default, it queries the vaccination appointments every 5 minutes and will not send repeat reminders for a single location until 2 hours has passed (i.e., if you get more than one message in 2 hours, it means two separate cities have availabilities).

## Running the script
```python
python3 vaccine.py
```

---

I run mine on a raspberry pi in the background, 24/7. I have set up my email inbox such that when I receive an email with the Subject line in the script, it will forward the email to an email address that my phone provider uses for my phone. You can set up the same:

* **ATT**: 2625555555@txt.att.net
* **Verizon**: 2625555555@vtext.com
