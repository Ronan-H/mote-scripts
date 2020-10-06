import requests
from mote import Mote
from time import sleep
from PIL import Image
import time
import config


def retry_until_success(api_func, func_name, retry_wait, *args):
    data_retrieved = False
    data = {}

    while not data_retrieved:
        try:
            data = api_func(*args)
            data_retrieved = True
        except:
            print('Error on {} request, sleeping for {} seconds...'.format(
                func_name, retry_wait)
            )
            sleep(retry_wait)
    return data


def retrieve_covid_stats():
    return {
        'cases': requests.get('https://covid19.shanehastings.eu/api/daily/cases/').json(),
        'deaths': requests.get('https://covid19.shanehastings.eu/api/daily/deaths/').json()
    }


def retrieve_weather_info():
    data = requests.get(
        'https://api.openweathermap.org/data/2.5/weather?q=Galway&appid={}'.format(config.openweather_token)
    ).json()

    return {
        'temp': round(data['main']['temp'] - 273.15), 'wind': round(data['wind']['speed'] * 60 * 60 / 1000),
        'desc': data['weather'][0]['description'].upper()
    }


def retrieve_stock_value(ticker):
    return str(requests.get(
        'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}'.format(
            ticker, config.alphavantage_token
        )
    ).json()['Global Quote']['05. price'])[:5]


def gen_char_mappings(c_width, c_height):
    # using $ for a downward arrow
    char_mapping = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+=\\/%"\'!?-><.,*:;$° '
    char_img = Image.open('char-mapping.png', 'r')
    pixels_per_char = c_width * c_height
    pixels = [x for sets in list(char_img.getdata()) for x in sets][3::4]
    mapping = dict()
    for i, char in enumerate(char_mapping):
        on_indexes = [[] for _ in range(c_height)]
        index = i * pixels_per_char
        for j in range(c_height):
            for k in range(c_width):
                on_indexes[j].append(pixels[index] == 255)
                index += 1
        mapping[char] = on_indexes
    return mapping


def open_mote():
    m = Mote()

    for channel in range(1, 5):
        m.configure_channel(channel, 16, False)

    return m


char_width = 4
char_height = 5
# retrieve API stats every n scrolls
api_refresh_rate = 3
api_retry_wait = 15

scroll_y = -1
scroll_end = -1
scrolls_left = -1
scroll_sleep = 0.03
char_spacing = 2

text_colour = (255, 0, 0)
text_brightness = 0.06

# time of last stock check
last_stock_check = 0
max_stock_checks_per_day = 500
# minimum time between stock checks
stock_check_wait = (60 * 60 * 24) / (max_stock_checks_per_day - 50)
stock_ticker = 'CSCO'

display_text = None

char_mappings = gen_char_mappings(char_width, char_height)
mote = open_mote()

while True:
    if display_text is None or scroll_y >= scroll_end:
        scrolls_left -= 1
        scroll_y = -17
        if scrolls_left <= 0:
            print('Retrieving today\'s new cases from API...')
            new_stats = retry_until_success(retrieve_covid_stats, 'covid stats', api_retry_wait)
            cur_weather = retry_until_success(retrieve_weather_info, 'weather info', api_retry_wait)
            print('Updated covid stats: {} cases, {} deaths'.format(new_stats['cases'], new_stats['deaths']))
            print('Updated weather info: desc "{}", {}°C, wind {}kmph'.format(
                cur_weather['desc'], cur_weather['temp'], cur_weather['wind']))

            if time.time() > last_stock_check + stock_check_wait:
                # update stock price
                stock_price = retry_until_success(retrieve_stock_value, 'stock value', api_retry_wait, stock_ticker)
                last_stock_check = time.time()

                print('Updated stock price for {}, new price: {}'.format(stock_ticker, stock_price))

            display_text = "COVID$   {} CASE{}   {} DEATH{}   -   " \
                           "WEATHER$   {}   TEMP {}C   WIND {}KM   -   " \
                           "{} PRICE {} USD   ===   " \
                .format(new_stats['cases'], '' if new_stats['cases'] == 1 else 'S',
                        new_stats['deaths'], '' if new_stats['deaths'] == 1 else 'S',
                        cur_weather['desc'], cur_weather['temp'], cur_weather['wind'],
                        stock_ticker, stock_price)
            scroll_end = len(display_text) * (char_height + char_spacing) * 1 - char_spacing
            scrolls_left = api_refresh_rate

    y = scroll_y
    mote.clear()
    for ci, c in enumerate(display_text):
        pixels = char_mappings[c]

        for py, row in enumerate(pixels):
            for px, pixel_on in enumerate(row):
                y_loc = y - py + 16
                if 0 <= y_loc <= 15:
                    if pixel_on:
                        mote.set_pixel(px + 1, y_loc, *text_colour, text_brightness)

        y -= len(pixels) + char_spacing
    mote.show()
    scroll_y += 1
    sleep(scroll_sleep)
