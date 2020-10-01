import requests
from mote import Mote
from time import sleep
from PIL import Image

# time to sleep after checking the API
sleep_time = 5 * 60


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
    print('Updated new cases today:', num_cases_today)
    return num_cases_today


def gen_char_mappings():
    char_mapping = '0123456789CASETODY '
    char_img = Image.open('char-mapping.png', 'r')
    img_width = 4
    img_height = 5
    pixels_per_char = img_width * img_height
    pixels = [x for sets in list(char_img.getdata()) for x in sets][3::4]
    mapping = dict()
    print(pixels)
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
print(char_mappings)

mote = Mote()

mote.configure_channel(1, 16, False)
last_new_cases = None

mote.clear()

while True:
    new_cases = new_cases_today()

    if (not last_new_cases) or new_cases != last_new_cases:
        print('Cases changed, updating display...')

        

        # for i, v in enumerate(new_cases):
        #     if v == '1':
        #         mote.set_pixel(1, i, 255, 255, 255, 0.02)
        #     else:
        #         mote.set_pixel(1, i, 0, 0, 0, 0)
        #     mote.show()
    else:
        print('Cases unchanged.')

    print('Sleeping for {} seconds...'.format(sleep_time))
    sleep(sleep_time)
