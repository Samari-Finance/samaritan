from pymongo import MongoClient

from core.default_commands import commands


class MongoConn:

    def __init__(self,
                 path: str = None):
        self._init_conn(path)

    def set_invite_link_by_id(self, link, user_id):
        self.members.insert({'_id': user_id,
                             'invite_link': link})

    def set_new_ref(self, link, new_ref_user_id):
        self.members.update_one({'invite_link': link}, {'$push': {'refs': new_ref_user_id},
                                                        '$inc': {'refs_size': 1}})

    def get_members_pts(self):
        c = self.members.find({'refs_size': {'$gt': 0}})
        lst = []
        for doc in c:
            print(doc)
            lst.append({'id': doc['_id'], 'pts': len(doc['refs'])})
        return lst

    def get_invite_by_user_id(self, user_id):
        c = self.members.find_one({'_id': user_id})
        return c

    def remove_ref(self, user_id):
        self.members.find_one_and_update({'refs': user_id, 'refs_size': {'$gt': 0}},
                                         {'$pull': {'refs': user_id},
                                          '$inc': {'refs_size': -1}})

    def get_members(self):
        return self.members

    def get_handlers(self):
        return self.handlers

    def set_default_handlers(self):
        for key, value in commands.items():
            self.default_handlers.update_one({'_id': key},
                                             {'$set': {
                                                 'text': value.get('text', ),
                                                 'type': value.get('type', 'command'),
                                                 'aliases': value.get('aliases', [key]),
                                                 'delay': value.get('delay')
                                             }}, upsert=True)

    def get_text_by_handler(self, key: str):
        try:
            text = self.handlers.find_one({'_id': key})['text']
        except TypeError as e:
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

    def _init_cols(self):
        self.members = self.db['members']
        self.handlers = self.db['handlers']
        self.default_handlers = self.db['default_handlers']
        self.admins = self.db['admins']
        self.set_default_handlers()

    def _init_conn(self, path):
        self.client = MongoClient(path)
        self.db = self.client['main']
        self._init_cols()
