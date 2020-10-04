import requests
from mote import Mote
from time import sleep
from PIL import Image


def new_stats_today():
    data_retrieved = False
    stats = {}

    while not data_retrieved:
        try:
            stats['cases'] = requests.get('https://covid19.shanehastings.eu/api/daily/cases/').json()
            stats['deaths'] = requests.get('https://covid19.shanehastings.eu/api/daily/deaths/').json()
            data_retrieved = True
        except:
            print('Error on request, sleeping for 15 seconds...')
            sleep(15)
    return stats


char_width = 4
char_height = 5


def gen_char_mappings():
    # using $ for a downward arrow
    char_mapping = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+=\\/%"\'!?-><.,*:;$ '
    char_img = Image.open('char-mapping.png', 'r')
    pixels_per_char = char_width * char_height
    pixels = [x for sets in list(char_img.getdata()) for x in sets][3::4]
    mapping = dict()
    for i, char in enumerate(char_mapping):
        on_indexes = [[] for _ in range(char_height)]
        index = i * pixels_per_char
        for j in range(char_height):
            for k in range(char_width):
                on_indexes[j].append(pixels[index] == 255)
                index += 1
        mapping[char] = on_indexes
    return mapping


char_mappings = gen_char_mappings()

mote = Mote()

for channel in range(1, 5):
    mote.configure_channel(channel, 16, False)

mote.clear()

scrolls_until_refresh = 10
scrolls_left = -1
scroll_y = 0
scroll_sleep = 0.04
spacing = 2
scroll_end = -1
text_colour = (255, 0, 0)
text_brightness = 0.06

display_text = None

while True:
    if display_text is None or scroll_y >= scroll_end:  # TODO work out when scroll has reached end
        scrolls_left -= 1
        scroll_y = -17
        if scrolls_left <= 0:
            print('Retrieving today\'s new cases from API...')
            new_stats = new_stats_today()
            print('Updated stats: {} cases, {} deaths'.format(new_stats['cases'], new_stats['deaths']))
            display_text = "IRISH COVID STATS TODAY +{} CASES +{} DEATHS === " \
                .format(new_stats['cases'], new_stats['deaths'])
            scroll_end = len(display_text) * (char_height + spacing) * 1 - spacing
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
                        mote.set_pixel(px + 1, y_loc, *text_colour, text_brightness)

        y -= len(pixels) + spacing
    mote.show()
    scroll_y += 1
    sleep(scroll_sleep)
