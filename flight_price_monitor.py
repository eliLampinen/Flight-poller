# flight_price_monitor.py

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import json
import os
from datetime import datetime
from configFile import (
    email_sender,
    email_password,
    email_receivers,
    dates_to_track,
    price_threshold,
    destination,
    duration,
    airport
)

# Constants
URL_TEMPLATE = "https://www.tui.fi/lms/all?start=0&airport={airport}&date=&destination={destination}&resort=&duration={duration}&location=&selection=flightonly&pagesize=100&sorting=date"
DATA_FILE = 'previous_prices.json'

def fetch_flight_data():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'fi-FI,fi;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.tui.fi',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Upgrade-Insecure-Requests': '1',
    }

    url = URL_TEMPLATE.format(airport=airport, destination=destination, duration=duration)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_flight_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    flight_rows = soup.select('a.lms-row')
    flights = []

    for row in flight_rows:
        date_info = row.select_one('div.departy p:nth-of-type(2)').text.strip()
        destination_info = row.select_one('div.destiny p:nth-of-type(2)').text.strip()
        price_info = row.select_one('div.pricey p.current-price').text.strip()

        # Clean and parse the data
        price = int(price_info.split(' ')[0])
        flight = {
            'date_info': date_info,
            'destination_info': destination_info,
            'price': price,
            'link': row['href']
        }
        flights.append(flight)
    return flights

def load_previous_prices():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_current_prices(prices):
    with open(DATA_FILE, 'w') as f:
        json.dump(prices, f)

def send_email(flight):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = ', '.join(email_receivers)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = f"Price Drop Alert: Flight on {flight['date_info']}"

    body = f"""
    The price for the flight on {flight['date_info']} has dropped to {flight['price']} euros.
    Destination: {flight['destination_info']}
    Booking Link: {flight['link']}
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receivers, msg.as_string())
        server.quit()
        print(f"Email sent for flight on {flight['date_info']}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    html_content = fetch_flight_data()
    flights = parse_flight_data(html_content)
    previous_prices = load_previous_prices()
    current_prices = {}

    for flight in flights:
        date_info = flight['date_info']
        price = flight['price']

        if date_info in dates_to_track and price <= price_threshold:
            prev_price = previous_prices.get(date_info, None)
            current_prices[date_info] = price

            if prev_price is None or price < prev_price:
                send_email(flight)
        else:
            current_prices[date_info] = price

    save_current_prices(current_prices)

if __name__ == "__main__":
    main()
