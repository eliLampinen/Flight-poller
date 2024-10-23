
# Flight Price Monitor

This script monitors flight prices from the TUI website and sends email alerts when:

- The price drops for specified flights.
- There are limited seats available ("hurry" alerts).
- The script encounters errors fetching data (once per day).
  
It helps you keep track of flight prices and availability for specific dates and destinations.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Cron Job Setup](#cron-job-setup)
- [Data Files](#data-files)
- [Troubleshooting](#troubleshooting)
- [Ethical Considerations](#ethical-considerations)
- [License](#license)

## Features

- **Price Monitoring**: Tracks specified flights and alerts when prices drop below a threshold.
- **Limited Seats Alert**: Notifies when flights have limited seats available.
- **Error Notification**: Sends an email if the script fails to fetch data, but only once per day.
- **Future Date Check**: Only runs if there are future flights to monitor.
- **Single Email Alerts**: Consolidates all alerts into one email per script run.
- **Duplicate Alert Prevention**: Prevents sending multiple alerts for the same flight's "hurry" status.

## Requirements

- Python 3.x
- Libraries:
  - `requests`
  - `beautifulsoup4`

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/flight-price-monitor.git
   cd flight-price-monitor
   ```

2. **Install Required Libraries**

   Install the necessary Python libraries using `pip`:

   ```bash
   pip install requests beautifulsoup4
   ```

## Configuration

Create a configuration file named `configFile.py` in the project directory. This file contains all the configurable parameters for the script.

### Example `configFile.py`

```python
# configFile.py

# Email configuration
email_sender = 'your_email@gmail.com'
email_password = 'your_email_password'
email_receivers = ["recipient1@example.com", "recipient2@example.com"]

# Flight tracking configuration
dates_to_track = [
    "17-11-2024 · 16:45",
    "10-11-2024 · 17:50"
]  # Dates and times to track (format must match the website's format)

price_threshold = 500  # Maximum price in euros you're willing to pay
destination = 'LPA'     # Destination airport code (default: LPA for Gran Canaria)
duration = 7            # Trip duration in days (default: 7)
airport = 'OUL'         # Departure airport code (default: OUL)
```

### Configuration Parameters

- **Email Settings**
  - `email_sender`: The email address that will send the alerts. (Requires SMTP access)
  - `email_password`: The password or app-specific password for the sender email.
  - `email_receivers`: A list of email addresses to receive the alerts.

- **Flight Tracking Settings**
  - `dates_to_track`: A list of date strings in the format `"dd-mm-yyyy · hh:mm"` that you want to monitor.
  - `price_threshold`: The maximum price you're willing to pay for the flights.
  - `destination`: The destination airport code (e.g., `'LPA'` for Gran Canaria).
  - `duration`: The trip duration in days.
  - `airport`: The departure airport code (e.g., `'OUL'`).

### Important Notes

- **Email Security**: Be cautious with storing email credentials. It's recommended to use environment variables or a secure method to handle sensitive information.
- **Date Format**: Ensure that the dates in `dates_to_track` match the format used on the TUI website (`"dd-mm-yyyy · hh:mm"`).

## Usage

### Running the Script Manually

You can run the script manually using:

```bash
python flight_price_monitor.py
```

### Script Workflow

1. **Delay**: The script waits for a random duration between 1 and 3 seconds to mimic human behavior.
2. **Future Date Check**: It checks if there are any future dates in `dates_to_track`. If not, the script exits.
3. **Fetch Flight Data**: It attempts to fetch flight data from the TUI website.
   - If it encounters an error (e.g., network issues, non-200 HTTP status), it sends an error email (once per day) and exits.
4. **Parse Flight Data**: Parses the HTML content to extract flight details.
5. **Compare Prices and Alerts**:
   - Checks for price drops and adds to the alerts list if conditions are met.
   - Checks for "hurry" alerts (limited seats) and adds to the alerts list, ensuring no duplicate alerts for the same flight.
6. **Send Email**: If there are any alerts, it sends a single email containing all the alerts.
7. **Data Persistence**: Saves the current flight data to `previous_flights.json` for future comparisons.

## Cron Job Setup

To automate the script to run at regular intervals (e.g., every hour), set up a cron job.

1. **Open the Crontab Editor**

   ```bash
   crontab -e
   ```

2. **Add the Cron Job**

   Add the following line to schedule the script hourly:

   ```cron
   0 * * * * /usr/bin/python /path/to/flight-price-monitor/flight_price_monitor.py
   ```

   - Replace `/usr/bin/python` with the path to your Python interpreter.
   - Replace `/path/to/flight-price-monitor/flight_price_monitor.py` with the actual path to the script.

3. **Save and Exit**

   Save the crontab file and exit the editor.

## Data Files

- **`previous_flights.json`**: Stores flight data between runs to track price changes and "hurry" alerts.
- **`error_log.json`**: Logs the date when the last error email was sent to prevent multiple emails in a single day.

**Note**: Ensure the script has read and write permissions for these files.

## Troubleshooting

### Common Issues

- **No Emails Received**:
  - Check your email configuration in `configFile.py`.
  - Verify that the sender email account allows SMTP access and less secure apps (if applicable).
  - Check spam or junk folders.

- **Script Exits Without Running**:
  - Ensure that `dates_to_track` contains future dates in the correct format.
  - Check the console output for messages like "No future dates to track. Exiting script."

- **Errors Fetching Data**:
  - The script will send an error email if it cannot fetch data.
  - Check your internet connection.
  - Ensure that the TUI website is accessible and hasn't changed its structure.

### Logging

- **Console Output**: The script prints messages to the console, indicating its progress and any issues encountered.
- **Error Emails**: You will receive an email if the script fails to fetch data, but only once per day.

## Ethical Considerations

- **Compliance**: Ensure you comply with the TUI website's terms of service and `robots.txt` rules.
- **Data Usage**: Use the data responsibly and for personal purposes.
- **Request Frequency**: Avoid setting the script to run too frequently to prevent overloading the server.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: This script is intended for personal use to monitor flight prices. The developer is not responsible for any misuse of the script or issues arising from changes to the TUI website structure or policies.
