import random
from typing import Any

from PIL import Image, ImageFont
from PIL import ImageDraw
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from core.captcha.challenge import Challenge
from core.db import MongoConn
from core.utils import build_menu

colors = ["black", "red", "blue", "green", (64, 107, 76), (0, 87, 128), (0, 3, 82)]
fill_color = [(64, 107, 76), (0, 87, 128), (0, 3, 82), (191, 0, 255), (72, 189, 0), (189, 107, 0), (189, 41, 0)]


multiplier = 2.9
font_size = int(multiplier*0.7*18)
image_pixels = (int(multiplier*90), (int(multiplier*60)))
get_it_max_pixels = image_pixels[0]-5, image_pixels[1]-5
text_size = int(20*multiplier)
text_placement = int(20*multiplier)
lines_min = int(6*multiplier)
lines_max = int(11*multiplier)
points_min = int(11*multiplier)
points_max = int(50*multiplier)


class Challenger:

    def __init__(self,
                 db: MongoConn,
                 ) -> None:
        self.db = db

    def challenge_to_buttons(self):
        ch = Challenge()
        img = self.gen_captcha_img(ch)
        buttons = [InlineKeyboardButton(text=str(c), callback_data=str(c)) for c in ch.choices()]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=3))
        return img, reply_markup

    @staticmethod
    def gen_captcha_img(ch: Challenge):
        get_it = lambda: (random.randrange(5, get_it_max_pixels[0]), random.randrange(5, get_it_max_pixels[1]))

        # create a img object
        img = Image.new('RGB', image_pixels, color="white")
        draw = ImageDraw.Draw(img)

        # get challenge string
        captcha_str = ch.qus()

        # get the text color
        text_colors = random.choice(colors)
        font_name = "assets/fonts/SansitaSwashed-VariableFont_wght.ttf"
        font = ImageFont.truetype(font_name, random.randint(int(font_size*0.7), int(font_size*1.2)))
        draw.text((
            random.randint(int(text_placement*0.7), int(text_placement*1.2)),
            int(text_placement*0.7), int(text_placement*1.2)),
                  captcha_str,
                  fill=text_colors,
                  font=font)

        # draw random lines
        for i in range(5, random.randrange(lines_min, lines_max)):
            draw.line((get_it(), get_it()), fill=random.choice(fill_color), width=random.randrange(1, 3))

        # draw random points
        for i in range(10, random.randrange(points_min, points_max)):
            draw.point((get_it(), get_it(), get_it(), get_it(), get_it(), get_it(), get_it(), get_it(), get_it(), get_it()),
                       fill=random.choice(colors))

        return img

