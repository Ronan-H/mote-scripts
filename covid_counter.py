# displays covid case stats

import requests
from mote import Mote
from time import sleep

# time to sleep after checking the API
sleep_time = 5 * 60


def new_cases_today_bin():
    data_retrieved = False

    while not data_retrieved:
        try:
            data = requests.get('https://api.covid19api.com/country/ireland/status/confirmed/live').json()
            data_retrieved = True
        except:
            print('Error on request, sleeping for 30 seconds...')
            sleep(30)
    tot_cases_today = int(data[-1]['Cases'])
    tot_cases_yesterday = int(data[-2]['Cases'])
    new_cases_today = tot_cases_today - tot_cases_yesterday
    print('Updated new cases today:', new_cases_today)
    return str(bin(new_cases_today))[2:]


mote = Mote()

mote.configure_channel(1, 16, False)
last_case_str = None

mote.clear()

while True:
    cases_bin = new_cases_today_bin()

    if (not last_case_str) or cases_bin != last_case_str:
        print('Cases changed, updating display...')

        for i, v in enumerate(cases_bin):
            if v == '1':
                mote.set_pixel(1, i, 255, 255, 255, 0.02)
            else:
                mote.set_pixel(1, i, 0, 0, 0, 0)
            mote.show()
    else:
        print('Cases unchanged.')

    print('Sleeping for {} seconds...'.format(sleep_time))
    sleep(sleep_time)
