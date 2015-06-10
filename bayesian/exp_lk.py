
import json
import pymongo
from bson.objectid import ObjectId
import unicodedata
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30017)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def gen_test_data():
    linkedin = get_mongodb().linkedin

    authors_in_lk = json.load(open('../match_linkedin.json'))
    
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = set()
        for keyword in inputs[1: ]:
            author2words[author].add(keyword)

    gt = {}

    for ele in authors_in_lk:
        lk_id, author = tuple(ele)
        if author not in author2words: continue

        doc = linkedin.find_one({'_id': lk_id})

        if 'skills' not in doc: continue
        keywords = set()

        # for keyword in author2words[author]:
        #     flag = False
        #     for skill in doc['skills']:
        #         skill = skill.lower().replace(' ', '_')
        #         if skill in keyword or keyword in skill:
        #             flag = True
        #             break
        #     if flag:
        #         keywords.add(keyword)
        for skill in doc['skills']:
            keywords.add(skill)

        if len(keywords) > 0:
            gt[author] = keywords

    fout = open('lk_test.txt', 'w')
    for k, v in gt.iteritems():
        fout.write(k)
        for e in v:
            e = unicodedata.normalize('NFKD', e).encode('ascii','ignore')
            fout.write(',' + e.lower().replace(' ', '_'))
        fout.write('\n')
    fout.close()

def fuzzy_match(k1, ks):
    for k2 in ks:
        if k1 in k2 or k2 in k1: return True
        if similar(k1, k2) > 0.5: return True
    return False

# 0.447747747748
def test_bayesian():
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = []
        for keyword in inputs[1: ]:
            author2words[author].append(keyword)

    rt, rt_cnt = 0.0, 0
    for line in open('lk_test.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        keywords = set(inputs[1 :])

        pos_cnt, neg_cnt = 0, 0

        for keyword in author2words[author][: 5]:
            if fuzzy_match(keyword, keywords): pos_cnt += 1
            else: neg_cnt += 1
        rt += 1.0 * pos_cnt / (pos_cnt + neg_cnt)
        rt_cnt += 1
    print rt / rt_cnt

# 0.438025345592
def test_random_guess():
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = set()
        for keyword in inputs[1: ]:
            author2words[author].add(keyword)

    rt, rt_cnt = 0.0, 0
    for line in open('lk_test.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        keywords = set(inputs[1 :])

        pos_cnt = 0
        for keyword in author2words[author]:
            if fuzzy_match(keyword, keywords): pos_cnt += 1

        rt += 1.0 * pos_cnt / len(author2words[author])
        rt_cnt += 1
    print rt / rt_cnt

# 0.386636636637
def test_old():
    people = get_mongodb().people

    rt, rt_cnt = 0.0, 0
    cnt = 0
    for line in open('lk_test.txt'):
        cnt += 1
        inputs = line.strip().split(',')
        author = inputs[0]
        keywords = set(inputs[1 :])

        doc = people.find_one({'_id': ObjectId(author)})

        pos_cnt, neg_cnt = 0, 0

        for keyword in doc['tags'][: 5]:
            keyword = keyword['t'].lower().replace(' ', '_')
            if fuzzy_match(keyword, keywords): pos_cnt += 1
            else: neg_cnt += 1
        rt += 1.0 * pos_cnt / (pos_cnt + neg_cnt) if pos_cnt  + neg_cnt > 0 else 0.0
        rt_cnt += 1
    print rt / rt_cnt

if __name__ == '__main__':
    gen_test_data()
    test_bayesian()
    test_random_guess()
    test_old()

