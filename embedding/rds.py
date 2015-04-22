__author__ = 'yutao'

import redis
from bs4 import UnicodeDammit

from CoDA.utils import Utils


SUBJECT_CLASSIFICATION_PREFIX = {1: "SUBJECT_CLASSIFICATION_PREFIX::ZH8::",
                                 2: "SUBJECT_CLASSIFICATION_PREFIX::EN8::",
                                 3: "SUBJECT_CLASSIFICATION_PREFIX::ZH86::",
                                 4: "SUBJECT_CLASSIFICATION_PREFIX::EN86::"}

EXPERT_SORT_ORDER_BY = { 1: "::HINDEX",
                         2: "::ACTIVITY",
                         3: "::NPUBS",
                         4: "::NCITE"}

class RdsClient(object):
    def __init__(self, host, port, db=2):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.redis0 = redis.StrictRedis(host=host, port=port, db=0)
        self.redis1 = redis.StrictRedis(host=host, port=port, db=1)
        self.redis2 = redis.StrictRedis(host=host, port=port, db=2)
        self.redis = redis.StrictRedis(host=host, port=6383)
        self.redis2 = redis.StrictRedis(host=host, port=6383)
        self.redis0 = redis.StrictRedis(host=host, port=6383)

    def set_hot_topic(self, key, data):
        import json
        self.redis.set("ht:%s" % key, json.dumps(data))

    def clean_hot_topic(self, key):
        self.redis.delete("ht:%s" % key)

    def get_hot_topic(self, key):
        data = self.redis.get("ht:%s" % key)
        return data

    # Author Service
    def get_author_id(self, pid, order):
        aid = self.redis.get("m1:%s.%s" % (pid, order))
        return aid

    def get_photo(self, pid):
        url = self.redis2.get("photo:%s" % pid)
        return url

    def set_photo(self, pid,url):
        self.redis2.set(("photo:%s" % pid),url)

    def get_pdf(self, pid):
        url = self.redis2.get("paper_pdf:%s" % pid)
        return url

    def set_pdf(self,pid,url):
        self.redis2.set(("paper_pdf:%s" % pid),url)

    def set_person_attr(self, attr, value, _id):
        key = "ATTR:P:%s:%s" % (_id, attr)
        self.redis2.set(key, value)

    def get_person_attr(self, _id, attr):
        key = "RANK:P:%s" % attr
        d = self.redis2.zscore(key, _id)
        if type(d) is float:
            return round(d, 2)
        else:
            return d

    def add_person_attr_rank(self, attr, value,  _id):
        key = "RANK:P:%s" % attr
        self.redis.zadd(key, value, _id)

    def get_person_attr_rank(self, attr, offset=0, size=10):
        key = "RANK:P:%s" % attr
        return self.redis.zrevrange(key, offset, offset+size, withscores=True)

    def set_top_person_attr_rank(self, attr, value,  _id):
        key = "TOP_RANK:P:%s" % attr
        self.redis.zadd(key, value, _id)

    def get_top_person_attr_rank(self, attr, offset=0, size=10):
        key = "TOP_RANK:P:%s" % attr
        return self.redis.zrevrange(key, offset, offset+size, withscores=True)

    def set_author_attr(self, attr, value, _id, order):
        key = "%s:%s" % (attr, value)
        self.redis.sadd(key, "%s.%s" % (str(_id), str(order)))

    def set_author_attr_lang(self, attr, value, _id, order, lang):
        key = "%s:%s:%s" % (lang, attr, value)
        self.redis.sadd(key, "%s.%s" % (str(_id), str(order)))

    def get_pub_by_attr(self, attr, value):
        key = "%s:%s" % (attr, value)
        return self.redis.smembers(key)

    def get_pub_by_attr_lang(self, attr, value, lang):
        key = "%s:%s:%s" % (lang, attr, value)
        return self.redis.smembers(key)

    def scan(self, pattern, size=10000):
        cursor, data = self.redis.scan(0, pattern, size)
        return cursor, data

    def iterate(self, pattern, token, size=10000):
        cursor, data = self.redis.scan(token, pattern, size)
        return cursor, data

    def smembers(self, key):
        data = self.redis.smembers(key)
        return data

    def append_name_uniqueness(self, name):
        y = name.split()
        self.redis.zincrby("uf", y[0], 1)
        self.redis.zincrby("ul", y[-1], 1)
        self.redis.zincrby("un", name, 1)

    def get_name_uniqueness(self, name):
        y = name.split()
        f = self.redis.zscore("uf", y[0])
        l = self.redis.zscore("ul", y[-1])
        # n = self.redis.zscore("un", name)
        n = self.redis.scard("name:%s" % name)
        if n == 0:
            n = self.redis.scard("name_zh:%s" % name)
        return f, l, n

    def set_cluster(self, name, result):
        pass

    # def insert_person(self, items, _id):
    # for item in items:
    # self.redis.set("m1:%s" % item, _id)
    #
    def insert_person_mapping(self, pubs, ranks, pid):
        for p in pubs:
            self.redis.set("m1:%s.%s" % (p, str(ranks[p])), pid)

    def insert_person_name_mapping(self, name, pid):
        self.redis.sadd("c2:%s" % name, pid)

    def insert_persons(self, items, ids, name):
        self.redis.set("c1:%s" % name, ",".join(ids))
        for i, item in enumerate(items):
            for d in item:
                if not ids[i]:
                    continue
                self.redis.set("m1:%s" % d, ids[i])



    def insert_person_cluster_by_name(self, ids, name):
        self.redis.set("c1:%s" % name, ",".join(ids))

    def get_persons_by_name(self, name):
        return self.redis.smembers("c2:%s" % name)

    def clear_person_name_mapping(self, name):
        self.redis.delete("c2:%s" % name)

    def delete_person_name_mapping(self, name, pid):
        self.redis.srem("c2:%s" % name, pid)

    def clear_persons(self):
        token = 0
        cursor, keys = self.redis.scan(token, "c1:*", 10000)
        cnt = 0
        while cursor != token:
            cnt += len(keys)
            print cnt
            for k in keys:
                self.redis.delete(k)
            cursor, keys = self.redis.scan(cursor, "c1:*", 10000)

        cursor, keys = self.redis.scan(token, "m1:*", 10000)
        cnt = 0
        while cursor != token:
            cnt += len(keys)
            print cnt
            for k in keys:
                self.redis.delete(k)
            cursor, keys = self.redis.scan(cursor, "m1:*", 10000)

    def get_person_by_name(self, name):
        name = UnicodeDammit(Utils.clean_name(name)).markup
        data = self.redis.get("c1:%s" % name)
        if data is not None and data != "":
            return data.split(",")[0]
        else:
            return None

    def get_pub_cluster_by_name(self, name):
        data = self.redis.get("c0:%s" % name)
        if data is None:
            return None
        tmp = data.split(";")
        return [c.split(",") for c in tmp]

    def get_person_cluster_by_name(self, name):
        data = self.redis.get("c1:%s" % name)
        if data is None:
            return []
        tmp = data.split(",")
        return tmp

    def iterate_pub_cluster_by_name(self, token, size=10000):
        cursor, data = self.redis.scan(token, "c0:*", size)
        return cursor, data

    def get_cache_search_person(self, query):
        # return None
        query = query.lower()
        data = self.redis.get("s5:%s" % query)
        return data

    def set_person_name_mapping(self, name, n_pubs, _id):
        self.redis.zadd("person:name:%s" % name, n_pubs, _id)

    def get_person_name_mapping(self, name):
        self.redis.z


    def store_cache_search_person(self, query, data):
        # return None
        query = query.lower()
        self.redis.set("s5:%s" % query, data)

    def get_cached_concept(self, query):
        query = query.lower()
        data = self.redis.get("ce0:%s" % query)
        return data

    def store_cached_concept(self, query, data):
        query = query.lower()
        self.redis.set("ce0:%s" % query, data)

    def get_pub_by_name(self, name):
        k = "name:%s" % name
        items = list(self.redis.smembers(k))
        ids = []
        ranks = {}
        for p in items:
            tmp = p.split(".")
            ids.append(tmp[0])
            ranks[tmp[0]] = int(tmp[1])
        return ids, ranks

    def get_cite_by_pid(self, pid):
        return list(self.redis0.smembers("CITE_REF_REL:C:" + str(pid)))

    def get_cite_size_by_pid(self, pid):
        return self.redis0.scard("CITE_REF_REL:C:" + str(pid))

    def get_ref_by_pid(self, pid):
        return list(self.redis0.smembers("CITE_REF_REL:R:" + str(pid)))

    def get_ref_size_by_pid(self, pid):
        return self.redis0.scard("CITE_REF_REL:R:" + str(pid))


    # field name : [A-H],[A01-HXX]
    # offset : from [0, ++ )
    # limit : -1 , [1, ++ ) . -1 mins
    # type :
    # 0: merged
    #   1: chinese pub classified to 8 A,B,C ... H
    #   2: english pub classified to 8 A,B,C ... H
    #   3: ch... 86 A01 , A02 , ...
    #   4: en... 86
    #   prefix :
    #   "SUBJECT_CLASSIFICATION_PREFIX::"
    #       "ZH8::";
    #       "EN8::";
    #       "ZH86::";
    #       "EN86::";

    def get_nsfc_experts(self, field_name="A01", offset=0, limit=100, orderBy = 1, type=4):
        if type in SUBJECT_CLASSIFICATION_PREFIX:
            # from single level
            return self.redis0.zrevrange(SUBJECT_CLASSIFICATION_PREFIX[type] + field_name + EXPERT_SORT_ORDER_BY[orderBy], offset, limit + offset - 1,
                                         "WITHSCORES")
        else:
            # from each level
            return []
        return None

    def get_nsfc_experts_no_score(self, field_name="A01", offset=0, limit=100, orderBy = 1, type=4):
        if type in SUBJECT_CLASSIFICATION_PREFIX:
            # from single level
            return self.redis0.zrevrange(SUBJECT_CLASSIFICATION_PREFIX[type] + field_name + EXPERT_SORT_ORDER_BY[orderBy], offset, limit + offset - 1)
        else:
            # from each level
            return []
        return None

    def get_nsfc_code_by_id(self, pid):
        codes = []
        for code in "ABCDEFGH":
            if self.redis0.zscore(SUBJECT_CLASSIFICATION_PREFIX[2] + code + EXPERT_SORT_ORDER_BY[1], pid):
                codes.append(code)
        return codes


    # order by :
    # 1 : h_index
    # 2 : activity
    # 3 : n_pubs
    # 4 : n_cites
    def get_all_nsfc_experts(self, field_name="A01", orderBy = 1, type=4 ):
        if type in SUBJECT_CLASSIFICATION_PREFIX:
            # from single level
            return self.redis0.zrevrange(SUBJECT_CLASSIFICATION_PREFIX[type] + field_name + EXPERT_SORT_ORDER_BY[orderBy], 0, -1)
        else:
            # from each level
            return []
        return None

    # type :
    #   1: chinese pub classified to 8 A,B,C ... H
    #   2: english pub classified to 8 A,B,C ... H
    #   3: ch... 86 A01 , A02 , ...
    #   4: en... 86
    def get_nsfc_experts_count(self, field_name="A01", orderBy = 1, type=4):
        if type in SUBJECT_CLASSIFICATION_PREFIX:
            return self.redis0.zcard(SUBJECT_CLASSIFICATION_PREFIX[type] + field_name + EXPERT_SORT_ORDER_BY[orderBy])
        else:
            return -1
        return None


    def is_nsfc_name(self, name):
        return self.redis1.redis1.sismember("NSFC_NAMES_SET", str(name).lower())