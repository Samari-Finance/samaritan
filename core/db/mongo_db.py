from pymongo import MongoClient


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

    def get_attr(self):
        return self.attr

    def _init_cols(self):
        self.members = self.db['members']
        self.attr = self.db['attr']

    def _init_conn(self, path):
        self.client = MongoClient(path)
        self.db = self.client['main']
        self._init_cols()
