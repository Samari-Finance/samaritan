from pymongo import MongoClient

from core.default_commands import commands


class MongoConn:

    def __init__(self,
                 path: str = None):
        self._init_conn(path)

    def set_invite_link_by_id(self, chat_id, link, user_id):
        self._chat_members(chat_id).update_one({'_id': user_id},
                                               {'$set': {'invite_link': link}}, upsert=True)

    def set_new_ref(self, chat_id, link, new_ref_user_id):
        new_ref_user_id = int(new_ref_user_id)
        self._chat_members(chat_id).update_one({'invite_link': link}, {'$push': {'refs': new_ref_user_id},
                                                                       '$inc': {'refs_size': 1}}, upsert=True)

    def get_members_pts(self, chat_id):
        c = self._chat_members(chat_id).find({'refs_size': {'$gt': 0}})
        lst = []
        for doc in c:
            print(doc)
            lst.append({'id': doc['_id'], 'pts': len(doc['refs'])})
        return lst

    def get_invite_by_user_id(self, chat_id, user_id):
        c = self._chat_members(chat_id).find_one({'_id': user_id})
        if c:
            c = c.get('invite_link', None)
        return c

    def remove_ref(self, chat_id, user_id):
        user_id = int(user_id)
        self._chat_members(chat_id).find_one_and_update({'refs': user_id, 'refs_size': {'$gt': 0}},
                                                        {'$pull': {'refs': user_id},
                                                         '$inc': {'refs_size': -1}})

    def set_default_handlers(self):
        for key, value in commands.items():
            for inner_key, inner_val in value.items():
                self.default_handlers.update_one({'_id': key},
                                                 {'$set': {
                                                     inner_key: inner_val
                                                 }}, upsert=True)

    def get_text_by_handler(self, key: str):
        try:
            #  text = self.handlers.find_one({'_id': key})['text']
            text = self.default_handlers.find_one({'_id': key})['text']
        except TypeError:
            try:
                text = self.default_handlers.find_one({'_id': key})['text']
            except TypeError:
                raise KeyError(f'key {key} does not exist in default handlers.')

        return text

    def get_admins(self):
        return self.admins.find()

    def set_handler_description(self, command: str, description: str):
        self._upsert_handler(command, 'delay', description)

    def set_handler_enabled(self, command, on):
        self._upsert_handler(command, 'enabled', on)

    def set_handler_type(self, command: str, handler_type: str):
        self._upsert_handler(command, 'type', handler_type)

    def set_handler_delay(self, command: str, timeout_in_sec: int):
        self._upsert_handler(command, 'delay', timeout_in_sec)

    def set_handler_parse_mode(self, command: str, parse_mode: str):
        self._upsert_handler(command, 'parse_mode', parse_mode)

    def _upsert_handler(self, command: str, key: str, value):
        self.handlers.update({'_id': command}, {'$set': {key: value}}, upsert=True)

    def _chat_members(self, chat_id):
        return self.chats_db[str(chat_id)]

    def _init_conn(self, path):
        self.client = MongoClient(path)
        self.main_db = self.client['main']
        self.chats_db = self.client['chats']
        self._init_cols()

    def _init_cols(self):
        self.handlers = self.main_db['handlers']
        self.default_handlers = self.main_db['default_handlers']
        self.admins = self.main_db['admins']
        self.set_default_handlers()

    def set_captcha_status(self, chat_id, user_id, status: bool):
        if isinstance(user_id, str):
            user_id = int(user_id)
        self._chat_members(chat_id).update_one({'_id': user_id},
                                               {'$set': {
                                                   'captcha_completed': status
                                               }}, upsert=True)

    def get_captcha_status(self, chat_id, user_id) -> bool:
        user_id = int(user_id)
        try:
            return self._chat_members(chat_id).find_one({'_id': user_id}).get('captcha_completed', False)

        except (KeyError, AttributeError, TypeError):
            self.set_captcha_status(user_id=user_id, chat_id=chat_id, status=False)
            return False

    def set_private_chat_id(self, chat_id, user_id, priv_chat_id):
        self._chat_members(chat_id).update_one({'_id': int(user_id)},
                                               {'$set': {'chat_id': int(priv_chat_id)}}, upsert=True)

    def get_private_chat_id(self, chat_id, user_id):
        try:
            return self._chat_members(chat_id).find_one({
                '_id': int(user_id),
                'chat_id': {'$exists': True}}).get('chat_id')
        except (KeyError, AttributeError, TypeError):
            return None
