import random
from typing import Any, Tuple, Type

import PIL
from PIL import Image, ImageFont
from PIL import ImageDraw
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import CallbackContext
from telegram.utils import types
from telegram.utils.helpers import DEFAULT_NONE

from core import MEMBER_PERMISSIONS, CALLBACK_DIVIDER, CAPTCHA_CALLBACK_PREFIX, CAPTCHA_PREFIX
from core.captcha.challenge import Challenge
from core.db import MongoConn
from core.utils import build_menu, send_image, send_message, pp_json

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


class Challenger:

    def __init__(self,
                 db: MongoConn,
                 ) -> None:
        self.db = db
        self.current_captchas = {}

    def captcha_deeplink(self, up: Update, ctx: CallbackContext) -> None:
        """Entrance handle callback for captcha deeplinks. Generates new challenge,
        presents it to the user, and saves the sent msg in current_callbacks to retrieve the id
        later when checking for answer.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext for bot
        :return: None
        """
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        user_id = payload[2]
        ch = Challenge()
        img, reply_markup = self.challenge_to_reply_markup(ch, ctx.args[0])

        msg = send_image(
            up,
            ctx,
            img=img,
            caption=self.db.get_text_by_handler('captcha_challenge'),
            reply_markup=reply_markup,
            reply=False)
        print(f'user_id: {user_id}')
        self.current_captchas[user_id] = {
            "msg": msg,
            "ch": ch
        }
        for element in self.current_captchas.items():
            str(element)

    def captcha_callback(self, up: Update, ctx: CallbackContext) -> None:
        """Determines if answer to captcha is correct or not,
        and calls the respective outcome's method.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext from bot
        :return: None
        """
        payload = up.callback_query.data.split(CALLBACK_DIVIDER)
        user_id = payload[2]
        ans = payload[-1]
        print(f'payload_callback: {payload}')

        for element in self.current_captchas.items():
            print(str(element))
        print(f'answer: {ans} == {self.current_captchas[str(user_id)]["ch"].ans()} is {ans == self.current_captchas[str(user_id)]["ch"].ans()}')
        if int(ans) == self.current_captchas[str(user_id)]['ch'].ans():
            self.captcha_completed(up, ctx, payload)
        else:
            self.captcha_failed(up, ctx, payload)

    def captcha_failed(self, up: Update, ctx: CallbackContext, payload) -> None:
        """Handles incorrect captcha responses. The captcha image and KeyboardMarkup is
        replaced with a new challenge's.

        :param up: Incoming Telegram.Update
        :param ctx: CallbackContext from bot
        :param payload: passed on data from CallbackQuery
        :return: None
        """
        chat_id = payload[1]
        user_id = payload[2]
        new_ch = Challenge()
        img, reply_markup = self.challenge_to_reply_markup(
            new_ch,
            CAPTCHA_CALLBACK_PREFIX + CALLBACK_DIVIDER + chat_id)
        img.parse_mode = DEFAULT_NONE

        up.callback_query.answer(self.db.get_text_by_handler('captcha_failed'))
        msg = ctx.bot.editMessageMedia(
            chat_id=self.current_captchas[user_id]['msg'].chat_id,
            message_id=self.current_captchas[user_id]['msg'].message_id,
            media=types.FileInput(img.tobytes()),
            reply_markup=reply_markup
        )
        self.current_captchas[up.effective_user.id] = {
            "msg": msg,
            "ch": new_ch
        }

    def captcha_completed(self, up: Update, ctx: CallbackContext, payload) -> None:
        """Handles a correct captcha, gives user back their rights, and replaces captcha with
        informational message.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext from bot
        :param payload: passed on data from CallbackQuery
        :return: None
        """
        chat_id = payload[1]
        user_id = payload[2]
        ctx.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=MEMBER_PERMISSIONS)
        ctx.bot.delete_message(
            chat_id=up.effective_chat.id,
            message_id=self.current_captchas[str(user_id)]['msg'].message_id)
        kb_markup = InlineKeyboardMarkup([[InlineKeyboardButton(
            text='Return to Samari.finance',
            url='https://t.me/samaritantestt')]])
        send_message(
            up,
            ctx,
            self.db.get_text_by_handler('captcha_complete'),
            reply_markup=kb_markup,
            disable_web_page_preview=True,
        )
        self.current_captchas.pop(str(user_id))

    def challenge_to_reply_markup(
            self,
            ch: Challenge,
            callback: str):
        """Creates a tuple of captcha image and KeyBoardMarkup based on a challenge

        :param ch: Challenge to draw
        :param callback: CallbackContext from bot
        :return: Tuple of image and KeyboardMarkup
        """
        callback = callback.replace(CAPTCHA_PREFIX, CAPTCHA_CALLBACK_PREFIX)
        img = self.gen_captcha_img(ch)
        buttons = [InlineKeyboardButton(
            text=str(c),
            callback_data=callback + CALLBACK_DIVIDER + str(c)) for c in ch.choices()]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=3))
        return img, reply_markup

    @staticmethod
    def gen_captcha_img(ch: Challenge) -> Image:
        """Generates captcha image with random lines and points using pillow.

        :param ch: Challenge to draw.
        :return: captcha image
        """
        get_it = lambda: (random.randrange(5, get_it_max_pixels[0]), random.randrange(5, get_it_max_pixels[1]))

        # create a img object
        img = Image.new('RGB', image_pixels, color="white")
        draw = ImageDraw.Draw(img)

        # get challenge string
        captcha_str = ch.qus()

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
