import random
from datetime import timedelta
from typing import Union

from PIL import Image, ImageFont
from PIL import ImageDraw
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, Message
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from core import MEMBER_PERMISSIONS, CALLBACK_DIVIDER, CAPTCHA_CALLBACK_PREFIX, CAPTCHA_PREFIX, MARKDOWN_V2
from core.captcha.challenge import Challenge
from core.db import MongoConn
from core.utils.utils import build_menu, send_image, send_message, wraps_log
from core.samaritable import Samaritable

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

MAX_ATTEMPTS = 4


class Challenger(Samaritable):

    def __init__(self,
                 db: MongoConn,
                 current_captchas: dict):
        self.db = db
        self.current_captchas = current_captchas
        super().__init__()

    @wraps_log
    def captcha_deeplink(self, up: Update, ctx: CallbackContext) -> None:
        """Entrance handle callback for captcha deeplinks. Generates new challenge,
        presents it to the user, and saves the sent msg in current_captchas to retrieve the id
        later when checking for answer.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext for bot
        :return: None
        """
        payload = ctx.args[0].split(CALLBACK_DIVIDER)
        chat_id = payload[1]
        user_id = payload[2]
        pub_msg = self.current_captchas[user_id]['pub_msg']
        self.log.debug('Captcha deeplink:{ chat_id: %s, user_id: %s, pub_msg_id: %s }',
                       str(chat_id),
                       str(user_id),
                       str(pub_msg.message_id))

        if not self.current_captchas.get(user_id).get('priv_msg'):
            ch = Challenge()
            img, reply_markup = self.challenge_to_reply_markup(up, ctx, ch, ctx.args[0])
            msg = send_image(
                up,
                ctx,
                img=img,
                caption=self.extend_captcha_caption(user_id),
                parse_mode=MARKDOWN_V2,
                reply_markup=reply_markup,
                reply=False)
            self.current_captchas[user_id].update(
                priv_msg=msg,
                ch=ch,
                attempts=0)
            self.db.set_captcha_status(user_id, False)
            self.kick_if_incomplete(up, ctx,
                                    chat_id=chat_id,
                                    private_chat_id=msg.chat_id,
                                    user_id=user_id,
                                    pub_msg=pub_msg,
                                    priv_msg=msg)
        else:
            ch = self.current_captchas[user_id]['ch']

    @wraps_log
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
        self.log.debug('Captcha callback:{ user_id: %s answer: %s }', str(user_id), str(ans))

        print(f'payload_callback: {str(payload)}')

        for element in self.current_captchas.items():
            print(str(element))
        print(f'answer: {ans} == {self.current_captchas[str(user_id)]["ch"].ans()} is '
              f'{int(ans) == self.current_captchas[str(user_id)]["ch"].ans()}')
        if int(ans) == -1:
            self.captcha_refresh(up, ctx, payload)
        elif int(ans) == self.current_captchas[str(user_id)]['ch'].ans():
            self.captcha_completed(up, ctx, payload)
        else:
            self.captcha_failed(up, ctx, payload)

    @wraps_log
    def captcha_refresh(self, up: Update, ctx: CallbackContext, payload) -> None:
        """Handles captcha refreshes. Displays a new captcha without incrementing the
        user's attempts.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext from bot
        :param payload: passed on data from CallbackQuery
        :return: None
        """
        chat_id = payload[1]
        user_id = payload[2]
        priv_msg = self._get_priv_msg(user_id)
        new_ch = Challenge()

        img, reply_markup = self.challenge_to_reply_markup(
            up, ctx, new_ch, self.gen_captcha_callback(chat_id, user_id))

        msg = ctx.bot.edit_message_media(
            chat_id=priv_msg.chat_id,
            message_id=priv_msg.message_id,
            media=InputMediaPhoto(
                media=img,
                caption=self.extend_captcha_caption(user_id),
                parse_mode=MARKDOWN_V2),
            reply_markup=reply_markup,
        )
        self.current_captchas[user_id]['msg'] = msg
        self.current_captchas[user_id]['ch'] = new_ch

    @wraps_log
    def captcha_failed(self, up: Update, ctx: CallbackContext, payload) -> None:
        """Handles incorrect captcha responses. The captcha image and KeyboardMarkup is
        replaced with a new challenge's.

        :param up: Incoming telegram.Update
        :param ctx: CallbackContext from bot
        :param payload: passed on data from CallbackQuery
        :return: None
        """
        chat_id = payload[1]
        user_id = payload[2]
        priv_msg = self._get_priv_msg(user_id)
        pub_msg = self._get_public_msg(user_id)
        new_ch = Challenge()
        self.log.debug('Captcha failed:{ chat_id: %s, user_id: %s, pub_msg_id: %s, priv_msg_id: %s}',
                       str(chat_id),
                       str(user_id),
                       str(pub_msg.message_id),
                       str(priv_msg.message_id))

        self.current_captchas[user_id]['attempts'] += 1
        img, reply_markup = self.challenge_to_reply_markup(
            up, ctx, new_ch, self.gen_captcha_callback(chat_id, user_id))

        up.callback_query.answer(self.db.get_text_by_handler('captcha_failed'))
        try:
            msg = ctx.bot.edit_message_media(
                chat_id=priv_msg.chat_id,
                message_id=priv_msg.message_id,
                media=InputMediaPhoto(
                    media=img,
                    caption=self.extend_captcha_caption(user_id),
                    parse_mode=MARKDOWN_V2),
                reply_markup=reply_markup,
            )
            self.current_captchas[user_id]['priv_msg'] = msg
            self.current_captchas[user_id]['ch'] = new_ch
        except BadRequest as e:
            self.log.exception(e)

    @wraps_log
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
        priv_msg = self._get_priv_msg(user_id)
        pub_msg = self._get_public_msg(user_id)
        self.log.debug('Payload: %s', payload)
        ctx.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=MEMBER_PERMISSIONS)
        ctx.bot.delete_message(
            chat_id=up.effective_chat.id,
            message_id=priv_msg.message_id)
        try:
            ctx.bot.delete_message(
                chat_id=chat_id,
                message_id=pub_msg.message_id
            )
        except BadRequest:
            self.log.debug(f'Message %s not found in %s with id: %s',
                           str(priv_msg.message_id),
                           ctx.bot.get_chat(chat_id).full_name,
                           str(chat_id))

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
        self.db.set_captcha_status(user_id, True)
        self.current_captchas.pop(str(user_id), None)

    @wraps_log
    def challenge_to_reply_markup(
            self,
            up: Update,
            ctx: CallbackContext,
            ch: Challenge,
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
        img_file = self.gen_captcha_img(ch)
        img = send_image(up, ctx, chat_id=-1001330154006, img=img_file, reply=False).photo[0]
        buttons = [InlineKeyboardButton(
            text=str(c),
            callback_data=callback + CALLBACK_DIVIDER + str(c)) for c in ch.choices()]
        reply_markup = InlineKeyboardMarkup(build_menu(
            buttons=buttons,
            n_cols=3,
            header_buttons=[InlineKeyboardButton(
                text='Refresh captcha',
                callback_data=callback + CALLBACK_DIVIDER + str(-1))]
        ))
        return img, reply_markup

    @wraps_log
    def kick_if_incomplete(self,
                           up: Update,
                           ctx: CallbackContext,
                           chat_id: Union[str, int],
                           private_chat_id: Union[str, int],
                           user_id: Union[str, int],
                           priv_msg: Message,
                           pub_msg: Message) -> None:
        def once(ctx: CallbackContext):
            if not self.db.get_captcha_status(user_id):
                for element in [chat_id, private_chat_id, user_id, private_chat_id, user_id, priv_msg.message_id, pub_msg.message_id]:
                    if isinstance(element, int):
                        element = str(element)
                self.log.debug('Kicking %s from %s, and deleting %s from %s and %s from %s',
                               user_id, chat_id, pub_msg.message_id, chat_id, priv_msg.message_id, private_chat_id)
                ctx.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
                ctx.bot.delete_message(chat_id=chat_id, message_id=pub_msg.message_id)
                ctx.bot.delete_message(chat_id=private_chat_id, message_id=priv_msg.message_id)
                self.db.remove_ref(user_id)
                self.db.set_captcha_status(user_id, False)
                ctx.job_queue.run_once(callback=unban, when=timedelta(seconds=10))
                self.current_captchas.pop(user_id)

        def unban(ctx: CallbackContext):
            ctx.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
            self.db.set_captcha_status(user_id, False)

        ctx.job_queue.run_once(callback=once, when=timedelta(seconds=10))

    @staticmethod
    def gen_captcha_img(ch: Challenge) -> Image:
        """Generates captcha image with random lines and points using pillow.

        :param ch: Challenge to draw
        :return: captcha image
        """
        def get_it():
            return random.randrange(5, get_it_max_pixels[0]), random.randrange(5, get_it_max_pixels[1])

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

    def extend_captcha_caption(self, user_id):
        caption = str(self.db.get_text_by_handler('captcha_challenge'))
        current_user = self.current_captchas.get(user_id, None)
        if not current_user:
            attempts_left = MAX_ATTEMPTS
        else:
            attempts_left = MAX_ATTEMPTS - current_user.get('attempts', 0)
        return caption + f"\n\n             \\>\\>\\> *__{attempts_left}__* *_ATTEMPTS LEFT_* \\<\\<\\<"

    @staticmethod
    def gen_captcha_callback(chat_id, user_id):
        return CAPTCHA_CALLBACK_PREFIX + CALLBACK_DIVIDER +\
               chat_id + CALLBACK_DIVIDER + \
               user_id

    def _get_priv_msg(self, user_id: Union[str, int]) -> Message:
        return self.current_captchas.get(str(user_id), None).get('priv_msg')

    def _get_public_msg(self, user_id: Union[str, int]) -> Message:
        return self.current_captchas.get(str(user_id), None).get('pub_msg')
