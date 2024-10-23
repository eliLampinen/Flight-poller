# flight_price_monitor.py

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import json
import os
import time
import random
from datetime import datetime, date
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

import csv
from datetime import datetime

# Constants
URL_TEMPLATE = "https://www.tui.fi/lms/all?start=0&airport={airport}&date=&destination={destination}&resort=&duration={duration}&location=&selection=flightonly&pagesize=100&sorting=date"
DATA_FILE = 'previous_flights.json'
ERROR_LOG_FILE = 'error_log.json'
CSV_FILE = 'flight_prices_log.csv'

def has_future_dates():
    today = datetime.now().date()
    for date_str in dates_to_track:
        # Extract the date part before '·'
        date_part = date_str.split('·')[0].strip()
        try:
            flight_date = datetime.strptime(date_part, '%d-%m-%Y').date()
            if flight_date >= today:
                return True
        except ValueError:
            # Handle incorrect date format
            continue
    return False

def fetch_flight_data():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'fi-FI,fi;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Upgrade-Insecure-Requests': '1',
    }

    url = URL_TEMPLATE.format(airport=airport, destination=destination, duration=duration)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            handle_api_error(response.status_code)
            return None
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        handle_api_error(str(e))
        return None

def handle_api_error(error_message):
    # Check if an error email was sent today
    error_logged_today = False
    today_str = datetime.now().strftime('%Y-%m-%d')

    if os.path.exists(ERROR_LOG_FILE):
        with open(ERROR_LOG_FILE, 'r') as f:
            error_log = json.load(f)
            last_error_date = error_log.get('last_error_date')
            if last_error_date == today_str:
                error_logged_today = True
    else:
        error_log = {}

    if not error_logged_today:
        # Send error email
        send_error_email(error_message)
        # Update error log
        error_log['last_error_date'] = today_str
        with open(ERROR_LOG_FILE, 'w') as f:
            json.dump(error_log, f)

def send_error_email(error_message):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = ', '.join(email_receivers)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = "Flight Monitor Error Alert"

    body = f"""
    An error occurred while fetching flight data:

    Error: {error_message}

    This is a notification to inform you of the issue. The script will attempt to run again in the next scheduled interval.
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receivers, msg.as_string())
        server.quit()
        print("Error email sent.")
    except Exception as e:
        print(f"Failed to send error email: {e}")

def parse_flight_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    flight_rows = soup.select('a.lms-row')
    flights = []

    for row in flight_rows:
        date_info = row.select_one('div.departy p:nth-of-type(2)').text.strip()
        destination_info = row.select_one('div.destiny p:nth-of-type(2)').text.strip()
        price_info = row.select_one('div.pricey p.current-price').text.strip()

        # Extract the 'hurry' element if present
        hurry_element = row.select_one('div.hurry p')
        hurry_text = hurry_element.text.strip() if hurry_element else None

        # Clean and parse the data
        price = int(price_info.split(' ')[0])
        flight = {
            'date_info': date_info,
            'destination_info': destination_info,
            'price': price,
            'link': row['href'],
            'hurry_text': hurry_text
        }
        flights.append(flight)
    return flights

def load_previous_flights():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_current_flights(flights_data):
    with open(DATA_FILE, 'w') as f:
        json.dump(flights_data, f)

def send_email(alerts):
    if not alerts:
        return  # No alerts to send

    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = ', '.join(email_receivers)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = "Flight Alerts"

    body = ""

    for alert in alerts:
        if alert['type'] == 'price_drop':
            body += f"""
            Price Drop Alert:
            Flight Date: {alert['flight']['date_info']}
            New Price: {alert['flight']['price']} euros
            Destination: {alert['flight']['destination_info']}
            Booking Link: {alert['flight']['link']}
            ----------------------------------------
            """
        elif alert['type'] == 'hurry':
            body += f"""
            Hurry Alert:
            Limited Seats for Flight on {alert['flight']['date_info']}
            Seats Left: {alert['flight']['hurry_text']}
            Price: {alert['flight']['price']} euros
            Destination: {alert['flight']['destination_info']}
            Booking Link: {alert['flight']['link']}
            ----------------------------------------
            """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receivers, msg.as_string())
        server.quit()
        print("Email sent with all alerts.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to log flight prices into a CSV file
def log_flight_price(flight_date, flight_time, destination, price):
    current_time = datetime.now()
    log_date = current_time.strftime("%Y-%m-%d")
    log_time = current_time.strftime("%H:%M:%S")

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['log_date', 'log_time', 'flight_date', 'flight_time', 'destination', 'price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header only if the file is empty (first time logging)
        if csvfile.tell() == 0:
            writer.writeheader()

        # Log the current price with a timestamp
        writer.writerow({
            'log_date': log_date,
            'log_time': log_time,
            'flight_date': flight_date,
            'flight_time': flight_time,
            'destination': destination,
            'price': price
        })

def main():
    # Sleep for a random duration between 1 and 3 seconds
    time.sleep(random.uniform(123, 1231))

    # Check if there are any future dates to track
    if not has_future_dates():
        print("No future dates to track. Exiting script.")
        return

    html_content = fetch_flight_data()
    if html_content is None:
        # Error handled in fetch_flight_data()
        return

    flights = parse_flight_data(html_content)
    previous_flights = load_previous_flights()
    current_flights = {}

    alerts = []

    for flight in flights:
        date_info = flight['date_info']
        flight_date, flight_time = date_info.split(' · ')
        price = flight['price']
        hurry_text = flight['hurry_text']
        flight_key = date_info  # Use date_info as a unique key
    
        destination_info = flight['destination_info']
        log_flight_price(flight_date, flight_time, destination_info, price)

        # Initialize current flight data
        current_flights[flight_key] = {
            'price': price,
            'hurry_alert_sent': False
        }

        # Get previous flight data
        prev_flight_data = previous_flights.get(flight_key, {})
        prev_price = prev_flight_data.get('price')
        hurry_alert_sent = prev_flight_data.get('hurry_alert_sent', False)

        # Check for 'hurry' alert
        if hurry_text and not hurry_alert_sent:
            # Add to alerts list
            alerts.append({'type': 'hurry', 'flight': flight})
            # Mark that we've sent a 'hurry' alert for this flight
            current_flights[flight_key]['hurry_alert_sent'] = True
        else:
            current_flights[flight_key]['hurry_alert_sent'] = hurry_alert_sent

        # Check for price drop and within threshold
        if date_info in dates_to_track and price <= price_threshold:
            current_flights[flight_key]['price'] = price

            if prev_price is None or price < prev_price:
                # Add to alerts list
                alerts.append({'type': 'price_drop', 'flight': flight})

    # Send email if there are any alerts
    send_email(alerts)

    # Save the current flight data
    save_current_flights(current_flights)

if __name__ == "__main__":
    main()
