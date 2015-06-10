
from bs4 import BeautifulSoup
import os
import pymongo
from bson.objectid import ObjectId

def test_bayesian():
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = []
        for keyword in inputs[1: ]:
            author2words[author].append(keyword)

    target_authors = []
    rt, rt_cnt = 0.0, 0
    for filename in os.listdir('../homepage'):
        author = filename.split('.')[0]
        if author not in author2words: continue

        doc = open('../homepage/' + filename).read()
        soup = BeautifulSoup(doc)
        doc = soup.get_text()

        pos_cnt, neg_cnt = 0, 0

        for keyword in author2words[author][: 5]:
            if keyword.replace('_', ' ') in doc: pos_cnt += 1
            else: neg_cnt += 1

        rt += 1.0 * pos_cnt / (pos_cnt + neg_cnt)
        rt_cnt += 1

        print rt / rt_cnt

    print rt / rt_cnt

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'aminer.org', port = 30019)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def test_old():
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = []
        for keyword in inputs[1: ]:
            author2words[author].append(keyword)

    people = get_mongodb().people

    target_authors = []
    rt, rt_cnt = 0.0, 0
    cnt = 0
    for filename in os.listdir('../homepage'):
        if cnt % 100 == 0:
            print 'calc', cnt
        cnt += 1

        author = filename.split('.')[0]
        if author not in author2words: continue

        doc = open('../homepage/' + filename).read()
        soup = BeautifulSoup(doc)
        doc = soup.get_text()

        people_doc = people.find_one({'_id': ObjectId(author)})

        pos_cnt, neg_cnt = 0, 0

        for keyword in people_doc['tags'][: 5]:
            keyword = keyword['t']
            if keyword.replace('_', ' ') in doc: pos_cnt += 1
            else: neg_cnt += 1

        rt += 1.0 * pos_cnt / (pos_cnt + neg_cnt) if pos_cnt + neg_cnt > 0 else 0.0
        rt_cnt += 1

        print rt / rt_cnt

    print rt / rt_cnt

if __name__ == '__main__':
    # test_bayesian()
    test_old()