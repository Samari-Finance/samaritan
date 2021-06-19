"""Samaritan
Copyright (C) 2021 Samari.finance

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
---------------------------------------------------------------------"""

import random

from PIL import ImageDraw, ImageFont
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from core import CAPTCHA_PREFIX, CAPTCHA_CALLBACK_PREFIX, CALLBACK_DIVIDER
from core.utils.utils import log_curr_captchas, log_entexit, send_image, build_menu

colors = ["black", "red", "blue", "green", (64, 107, 76), (0, 87, 128), (0, 3, 82)]
fill_color = [(64, 107, 76), (0, 87, 128), (0, 3, 82), (191, 0, 255), (72, 189, 0), (189, 107, 0), (189, 41, 0)]

multiplier = 2.9
font_size = int(multiplier * 0.7 * 18)
image_pixels = (int(multiplier * 90), (int(multiplier * 60)))
get_it_max_pixels = image_pixels[0] - 5, image_pixels[1] - 5
text_size = int(20 * multiplier)
text_placement = int(20 * multiplier)
lines_min = int(6 * multiplier)
lines_max = int(11 * multiplier)
points_min = int(11 * multiplier)
points_max = int(50 * multiplier)


class Challenge:
    def __init__(self):
        self._a = 0
        self._b = 0
        self._op = '+'
        self._ans = 0
        self._choices = []
        self.new()

    def __str__(self):
        return '{a}{op}{b}=?'.format(a=self._a, b=self._b, op=self._op)

    def new(self):
        operation = random.choice(['+', '-', '×', '÷'])
        a, b, ans = 0, 0, 0
        if operation in ['+', '-']:
            a, b = random.randint(0, 50), random.randint(0, 50)
            a, b = max(a, b), min(a, b)
            ans = a+b if operation == '+' else a-b
        elif operation == '×':
            a, b = random.randint(0, 9), random.randint(0, 9)
            ans = a*b
        elif operation == '÷':
            a, b = random.randint(0, 9), random.randint(1, 9)
            ans = a
            a = a*b

        cases = 9
        choices = random.sample(range(100), cases)
        if ans not in choices:
            choices[0] = ans
        random.shuffle(choices)
        # Some bots just blindly click the first button
        if choices[0] == ans:
            choices[0], choices[1] = choices[1], choices[0]

        self._a, self._b = a, b
        self._op = operation
        self._ans = ans
        self._choices = choices

    def gen_img(self) -> Image:
        """Generates captcha image with random lines and points using pillow.

        :return: captcha image
        """
        def get_it():
            return random.randrange(5, get_it_max_pixels[0]), random.randrange(5, get_it_max_pixels[1])

        # create a img object
        img = Image.new('RGB', image_pixels, color="white")
        draw = ImageDraw.Draw(img)

        # get challenge string
        captcha_str = self.qus()

        # get the text color
        text_colors = random.choice(colors)
        font_name = "assets/fonts/SansitaSwashed-VariableFont_wght.ttf"
        font = ImageFont.truetype(font_name, random.randint(int(font_size * 0.7), int(font_size * 1.2)))
        draw.text((
            random.randint(int(text_placement * 0.7), int(text_placement * 1.2)),
            int(text_placement * 0.7), int(text_placement * 1.2)),
            captcha_str,
            fill=text_colors,
            font=font)

        # draw random lines
        for i in range(5, random.randrange(lines_min, lines_max)):
            draw.line((get_it(), get_it()), fill=random.choice(fill_color), width=random.randrange(1, 3))

        # draw random points
        for i in range(10, random.randrange(points_min, points_max)):
            draw.point((get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it()),
                       fill=random.choice(colors))

        return img

    def gen_img_markup(
            self,
            up: Update,
            ctx: CallbackContext,
            callback: str,
    ):
        """Returns a tuple of captcha image file_id uploaded to private channel
         and KeyBoardMarkup based on a challenge

        :param up: incoming update
        :param ctx: context for bot
        :param ch: Challenge to draw
        :param callback: CallbackContext from bot
        :return: Tuple of image and KeyboardMarkup
        """
        callback = callback.replace(CAPTCHA_PREFIX, CAPTCHA_CALLBACK_PREFIX)
        img_file = self.gen_img()
        img = send_image(up, ctx, chat_id=-1001330154006, img=img_file, reply=False).photo[0]
        buttons = [InlineKeyboardButton(
            text=str(c),
            callback_data=callback + CALLBACK_DIVIDER + str(c)) for c in self.choices()]
        reply_markup = InlineKeyboardMarkup(build_menu(
            buttons=buttons,
            n_cols=3,
            header_buttons=[InlineKeyboardButton(
                text='Refresh captcha',
                callback_data=callback + CALLBACK_DIVIDER + str(-1))]
        ))
        return img, reply_markup

    def qus(self):
        return self.__str__()

    def ans(self):
        return self._ans

    def choices(self):
        return self._choices
