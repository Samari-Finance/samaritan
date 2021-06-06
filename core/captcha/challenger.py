import random
from typing import Any

from PIL import Image, ImageFont
from PIL import ImageDraw
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from core import MEMBER_PERMISSIONS, CALLBACK_DIVIDER, PAYLOAD_CUID_INDEX, PAYLOAD_UUID_INDEX, PAYLOAD_ANS_INDEX, \
    CAPTCHA_CALLBACK_PREFIX
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

    def captcha_deeplink(self, up: Update, ctx: CallbackContext):
        payload = up.callback_query.data.split(CALLBACK_DIVIDER)
        chat_id = payload[PAYLOAD_CUID_INDEX]
        ch = Challenge()
        img, reply_markup = self.challenge_to_reply_markup(ch, CAPTCHA_CALLBACK_PREFIX+CALLBACK_DIVIDER+chat_id)

        msg = send_image(
            up,
            ctx,
            img=img,
            caption=self.db.get_text_by_handler('captcha_challenge'),
            reply_markup=reply_markup,
            reply=False)
        print(f'sent msg: {msg.to_json()}')
        print(f'current user: {up.effective_user.id}')
        self.current_captchas[up.effective_user.id] = {
            'msg': msg,
            'ch': ch
        }
        for element in self.current_captchas:
            pp_json(str(element))

    def captcha_callback(self, up: Update, ctx: CallbackContext):
        payload = up.callback_query.data.split(CALLBACK_DIVIDER)
        chat_id = payload[PAYLOAD_CUID_INDEX]
        user_id = payload[PAYLOAD_UUID_INDEX]
        ans = payload[PAYLOAD_ANS_INDEX]
        print(f'payload: {payload}')

        for element in self.current_captchas:
            pp_json(f'callback element: {str(element)}')

        if ans == self.current_captchas[user_id]['ch'].ans:
            ctx.bot.restrict_chat_member(chat_id=chat_id,
                                         user_id=up.effective_user.id,
                                         permissions=MEMBER_PERMISSIONS)
            send_message(up, ctx, self.db.get_text_by_handler('captcha_completed'))
        else:
            new_ch = Challenge()
            img, reply_markup = self.challenge_to_reply_markup(new_ch, CAPTCHA_CALLBACK_PREFIX+CALLBACK_DIVIDER+chat_id)
            up.callback_query.answer(self.db.get_text_by_handler('captcha_failed'))
            ctx.bot.editMessageMedia(
                chat_id=chat_id,
                message_id=self.current_captchas[user_id]['msg'].message.id,
                media=img,
                reply_markup=reply_markup
            )
            self.current_captchas[up.effective_user.id] = {
                'msg': send_image(up,
                                  ctx,
                                  img=img,
                                  caption=self.db.get_text_by_handler(
                                      'captcha_challenge'),
                                  reply_markup=reply_markup,
                                  reply=False),
                'ch': new_ch
            }

    def challenge_to_reply_markup(self, ch: Challenge, callback: str):
        img = self.gen_captcha_img(ch)
        buttons = [InlineKeyboardButton(
            text=str(c),
            callback_data=callback+CALLBACK_DIVIDER+str(c)) for c in ch.choices()]
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
