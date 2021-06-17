from datetime import timedelta
from typing import Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, Message
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from core import MEMBER_PERMISSIONS, CALLBACK_DIVIDER, CAPTCHA_CALLBACK_PREFIX, MARKDOWN_V2
from core.captcha.challenge import Challenge
from core.db import MongoConn
from core.utils.utils import send_image, send_message, log_curr_captchas, log_entexit, fallback_user_id
from core.samaritable import Samaritable

MAX_ATTEMPTS = 4


class Challenger(Samaritable):

    def __init__(self,
                 db: MongoConn,
                 current_captchas: dict):
        super().__init__()
        self.db = db
        self.current_captchas = current_captchas

    @log_curr_captchas
    @log_entexit
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
        user_id = fallback_user_id(up)
        payload_aggr = ctx.args[0] + CALLBACK_DIVIDER + str(user_id)
        pub_msg = self.get_captcha_by_user(user_id)['pub_msg']
        self.log.debug('Captcha deeplink:{ chat_id: %s, user_id: %s, pub_msg_id: %s }',
                       str(chat_id),
                       str(user_id),
                       str(pub_msg.message_id))

        if not self.get_captcha_by_user(user_id).get('priv_msg'):
            ch = Challenge()
            img, reply_markup = ch.gen_img_markup(up, ctx, payload_aggr)
            msg = send_image(
                up,
                ctx,
                img=img,
                caption=self.extend_captcha_caption(user_id),
                parse_mode=MARKDOWN_V2,
                reply_markup=reply_markup,
                reply=False)
            self.get_captcha_by_user(user_id).update(
                priv_msg=msg,
                ch=ch,
                attempts=0)
            self.db.set_private_chat_id(chat_id, user_id, up.effective_chat.id)
            self.db.set_captcha_status(chat_id, user_id, False)
            self.kick_if_incomplete(up, ctx,
                                    chat_id=chat_id,
                                    priv_chat_id=msg.chat_id,
                                    user_id=user_id,
                                    pub_msg=pub_msg,
                                    priv_msg=msg)
        else:
            ch = self.get_captcha_by_user(user_id)['ch']

    @log_curr_captchas
    @log_entexit
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
        self.log.debug('Captcha callback:{user_id: %s, answer: %s}', str(user_id), str(ans))
        if int(ans) == -1:
            self.captcha_refresh(up, ctx, payload)
        elif int(ans) == self.get_captcha_by_user(user_id)['ch'].ans():
            self.captcha_completed(up, ctx, payload)
        else:
            self.captcha_failed(up, ctx, payload)

    @log_curr_captchas
    @log_entexit
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

        img, reply_markup = new_ch.gen_img_markup(
            up, ctx, self.gen_captcha_callback(chat_id, user_id))

        msg = ctx.bot.edit_message_media(
            chat_id=priv_msg.chat_id,
            message_id=priv_msg.message_id,
            media=InputMediaPhoto(
                media=img,
                caption=self.extend_captcha_caption(user_id),
                parse_mode=MARKDOWN_V2),
            reply_markup=reply_markup,
        )
        self.get_captcha_by_user(user_id)['msg'] = msg
        self.get_captcha_by_user(user_id)['ch'] = new_ch

    @log_curr_captchas
    @log_entexit
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
        priv_chat_id = self._get_priv_msg(user_id).chat_id
        pub_msg = self._get_public_msg(user_id)
        new_ch = Challenge()
        self.log.debug('Captcha failed:{ chat_id: %s, user_id: %s, pub_msg_id: %s, priv_msg_id: %s}',
                       str(chat_id),
                       str(user_id),
                       str(pub_msg.message_id),
                       str(priv_msg.message_id))

        self.get_captcha_by_user(user_id)['attempts'] += 1
        img, reply_markup = new_ch.gen_img_markup(
            up, ctx, self.gen_captcha_callback(chat_id, user_id))

        up.callback_query.answer(self.db.get_text_by_handler('captcha_failed'))
        try:
            if MAX_ATTEMPTS - self.get_captcha_by_user(user_id)['attempts'] > 0:
                msg = ctx.bot.edit_message_media(
                    chat_id=priv_msg.chat_id,
                    message_id=priv_msg.message_id,
                    media=InputMediaPhoto(
                        media=img,
                        caption=self.extend_captcha_caption(user_id),
                        parse_mode=MARKDOWN_V2),
                    reply_markup=reply_markup,
                )
                self.get_captcha_by_user(user_id)['priv_msg'] = msg
                self.get_captcha_by_user(user_id)['ch'] = new_ch
            else:
                self.log.debug('Attempts drained')
                self.kick_and_restrict(up, ctx, chat_id, user_id, pub_msg, priv_msg, priv_chat_id)(ctx)
        except BadRequest as e:
            self.log.exception(e)

    @log_curr_captchas
    @log_entexit
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
        ctx.bot.restrict_chat_member(chat_id, user_id, permissions=MEMBER_PERMISSIONS)
        ctx.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)

        try:
            ctx.bot.delete_message(
                chat_id=up.effective_chat.id,
                message_id=priv_msg.message_id)
            ctx.bot.delete_message(
                chat_id=chat_id,
                message_id=pub_msg.message_id
            )
        except BadRequest:
            self.log.debug(f'Message %s not found in %s with id: %s',
                           str(priv_msg.message_id),
                           ctx.bot.get_chat(chat_id).full_name,
                           str(chat_id))
        url = ctx.bot.get_chat(chat_id).invite_link
        kb_markup = InlineKeyboardMarkup([[InlineKeyboardButton(
            text='Return to Samari.finance',
            url=url)]])
        send_message(
            up,
            ctx,
            self.db.get_text_by_handler('captcha_complete'),
            reply_markup=kb_markup,
            disable_web_page_preview=True,
        )
        self.db.set_captcha_status(chat_id, user_id, True)
        self.current_captchas.pop(str(user_id), None)

    @log_curr_captchas
    @log_entexit
    def kick_if_incomplete(self,
                           up: Update,
                           ctx: CallbackContext,
                           chat_id: Union[str, int],
                           priv_chat_id: Union[str, int],
                           user_id: Union[str, int],
                           priv_msg: Message,
                           pub_msg: Message) -> None:
        def once(ctx: CallbackContext):
            if not self.db.get_captcha_status(chat_id, user_id):
                for element in [chat_id, priv_chat_id, user_id, priv_chat_id, user_id, priv_msg.message_id,
                                pub_msg.message_id]:
                    if isinstance(element, int):
                        str(element)
                    self.kick_and_restrict(up, ctx, chat_id, user_id, pub_msg, priv_msg, priv_chat_id)

        ctx.job_queue.run_once(callback=once, when=timedelta(seconds=120))

    @log_entexit
    def unban(self, ctx: CallbackContext, chat_id, user_id):
        def unban_in(ctx):
            ctx.bot.restrict_chat_member(chat_id, user_id, permissions=MEMBER_PERMISSIONS)
            ctx.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
            self.db.set_captcha_status(chat_id, user_id, False)
        return unban_in

    @log_entexit
    def kick_and_restrict(self, up, ctx: CallbackContext, chat_id, user_id, pub_msg, priv_msg, priv_chat_id,):
        def inner(ctx: CallbackContext):
            self.log.debug('Kicking %s from %s, and deleting %s from %s and %s from %s',
                           user_id, chat_id, pub_msg.message_id, chat_id, priv_msg.message_id, priv_chat_id)
            ctx.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
            ctx.bot.delete_message(chat_id=chat_id, message_id=pub_msg.message_id)
            ctx.bot.delete_message(chat_id=priv_chat_id, message_id=priv_msg.message_id)
            self.db.remove_ref(chat_id=chat_id, user_id=user_id)
            self.db.set_captcha_status(chat_id=chat_id, user_id=user_id, status=False)
            ctx.job_queue.run_once(callback=self.unban(ctx, chat_id, user_id), when=timedelta(seconds=7200))
            self.current_captchas.pop(chat_id, user_id)
            send_message(up, ctx,
                         chat_id=priv_chat_id,
                         text=f'Captcha failed. \nYou have been banned from '
                              f'{ctx.bot.get_chat(chat_id).full_name} for 2hrs.',
                         parse_mode=MARKDOWN_V2,
                         reply=False)
        return inner

    def extend_captcha_caption(self, user_id):
        caption = str(self.db.get_text_by_handler('captcha_challenge'))
        current_user = self.current_captchas.get(user_id, None)
        if not current_user:
            attempts_left = MAX_ATTEMPTS
        else:
            attempts_left = MAX_ATTEMPTS - current_user.get('attempts', 0)
        return caption + f"\n\n             \\>\\>\\> *__{attempts_left}__* *_ATTEMPTS LEFT_* \\<\\<\\<"

    @log_entexit
    def gen_captcha_callback(self, chat_id, user_id):
        return CAPTCHA_CALLBACK_PREFIX + CALLBACK_DIVIDER +\
               chat_id + CALLBACK_DIVIDER + \
               user_id

    @log_entexit
    def _get_priv_msg(self, user_id: Union[str, int]) -> Message:
        return self.current_captchas.get(int(user_id)).get('priv_msg')

    @log_entexit
    def _get_public_msg(self, user_id: Union[str, int]) -> Message:
        return self.current_captchas.get(int(user_id)).get('pub_msg')

    @log_entexit
    def _get_captcha_by_user(self, user_id):
        return self.current_captchas.get(int(user_id))

    @log_entexit
    def _pop_user(self, user_id):
        self.current_captchas.pop(int(user_id))
