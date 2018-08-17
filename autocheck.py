import argparse
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.by import By
from time import sleep
from sys import exit

parser = argparse.ArgumentParser(description="Automatically check-in for southwest flight")
parser.add_argument("-c", "--conf_num", help="confirmation number for the booking", required=True)
parser.add_argument("-f", "--first_name", help="first name for the booking", required=True)
parser.add_argument("-l", "--last_name", help="last name for the booking", required=True)
parser.add_argument('-t', '--time', help='time to check in for the flight in the format: %%Y-%%m-%%dT%%H:%%M', required=True)
parser.add_argument('-e', '--email', help='email address for receiving the boarding pass')
parser.add_argument('-s', '--show', help='set to visualize check in via chrome', action='store_true')

args = parser.parse_args()

def generate_url(conf_num, first_name, last_name):
    check_in_url = 'https://www.southwest.com/air/check-in/review.html'
    query_string = '?confirmationNumber=%s&passengerFirstName=%s&passengerLastName=%s'
    return check_in_url + query_string % (conf_num, first_name, last_name)

# Use headless mode if 'show' arg is not set
chrome_options = Options()
if not args.show:
    chrome_options.add_argument('--headless')

# Parse time and wait until check in is available
check_time = datetime.strptime(args.time, '%Y-%m-%dT%H:%M') + timedelta(seconds=1)
two_minute_buffer = check_time - timedelta(minutes=2)
five_second_buffer = check_time - timedelta(seconds=7) # Two seconds added to ensure driver startup
print('Sleeping until', str(check_time))
cur_time = datetime.now()

# Two minute intervals to ensure time isn't missed
while two_minute_buffer > cur_time:
    sleep(60 * 2)
    cur_time = datetime.now()

# Five second intervals for last two minutes
while five_second_buffer > cur_time:
    sleep(5)
    cur_time = datetime.now()

# Open driver at least 2 seconds before check in
driver = webdriver.Chrome(chrome_options=chrome_options)

# Wait until exact time
while check_time > cur_time:
    cur_time = datetime.now()
    sleep(0.1)

print("Checking in")

# Set auto-waiting for page loads
driver.implicitly_wait(5)
driver.get(generate_url(args.conf_num, args.first_name, args.last_name))

try:
    # Find check in button and click
    check_in_button = driver.find_element_by_class_name('air-check-in-review-results--check-in-button')
    check_in_button.click()

    if args.email:
        # Select option to send boarding pass via email
        use_email_button = driver.find_element_by_class_name('boarding-pass-options--button-email')
        use_email_button.click()

        # Fill email address and click send
        email_box = driver.find_element_by_id('emailBoardingPass')
        email_send_button = driver.find_element_by_id('form-mixin--submit-button')
        email_box.send_keys(args.email)
        email_send_button.click()

except NoSuchElementException:
    print("Check in failed, view browser to complete manually")
    if not args.show:
        # Launch visual browser if one doesn't exist
        driver.close()
        driver = webdriver.Chrome()
        driver.get(generate_url(args.conf_num, args.first_name, args.last_name))
    exit(-1)


print("Checked in successfully")
if args.show:
    print("Close tab to end script")
else:
    driver.close()
