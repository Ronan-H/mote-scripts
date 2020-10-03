import requests
from mote import Mote
from time import sleep
from PIL import Image


def new_cases_today():
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
    num_cases_today = tot_cases_today - tot_cases_yesterday
    return num_cases_today


def gen_char_mappings():
    char_mapping = '0123456789CASETODY '
    char_img = Image.open('char-mapping.png', 'r')
    img_width = 4
    img_height = 5
    pixels_per_char = img_width * img_height
    pixels = [x for sets in list(char_img.getdata()) for x in sets][3::4]
    mapping = dict()
    for i, char in enumerate(char_mapping):
        on_indexes = [[] for _ in range(img_height)]
        index = i * pixels_per_char
        for j in range(img_height):
            for k in range(img_width):
                on_indexes[j].append(pixels[index] == 255)
                index += 1
        mapping[char] = on_indexes
    return mapping


char_mappings = gen_char_mappings()

mote = Mote()

for channel in range(1, 5):
    mote.configure_channel(channel, 16, False)

last_new_cases = None

mote.clear()

scrolls_until_refresh = 25
scrolls_left = -1
scroll_y = 0
scroll_sleep = 0.08
spacing = 1

colour_cycle = ((0, 255, 0), (255, 255, 255), (255, 100, 0))
colour_index = -1

display_text = None

while True:
    if display_text is None or scroll_y > len(display_text) * 5 * 1.5:  # TODO work out when scroll has reached end
        scrolls_left -= 1
        scroll_y = -17
        colour_index = (colour_index + 1) % len(colour_cycle)
        if scrolls_left <= 0:
            print('Retrieving today\'s new cases from API...')
            new_cases = new_cases_today()
            display_text = "CASES TODAY {}".format(new_cases)
            if (not last_new_cases) or new_cases != last_new_cases:
                print('Updated scroll text:', display_text)
            scrolls_left = scrolls_until_refresh

    y = scroll_y
    mote.clear()
    for ci, c in enumerate(display_text):
        pixels = char_mappings[c]

        for py, row in enumerate(pixels):
            for px, pixel_on in enumerate(row):
                y_loc = y - py + 16
                if 0 <= y_loc <= 15:
                    if pixel_on:
                        mote.set_pixel(px + 1, y_loc, *colour_cycle[(colour_index + ci) % 3], 0.05)
        y -= len(pixels) + spacing
    mote.show()
    scroll_y += 1
    sleep(scroll_sleep)
