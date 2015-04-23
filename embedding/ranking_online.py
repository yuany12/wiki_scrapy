import pymongo
from collections import defaultdict as dd

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30017)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def count_word():
    db = get_mongodb()
    people = db.people
    keywords = db.keywords
    author_keywords = db.author_keywords
    cnt, tot = 0, people.count()
    for doc in people.find():
        if cnt % 1000 == 0:
            logging.info('word counting %d/%d' % (cnt, tot))
        cnt += 1

        if 'pubs' not in doc: continue
        word_cnt = dd(int)
        for pub in doc['pubs']:
            if 'i' not in pub: continue
            pid = pymongo.ObjectId(pub['i'])
            k_doc = keywords.find_one({'_id': pid})
            if k_doc is not None and 'title_keywords' in k_doc:
                for keyword_ in k_doc['title_keywords']:
                    word_cnt[keyword_] += 1
        author_keywords.update_one({'_id': doc['_id']}, {'$set': {'title_keywords': dict(word_cnt)}})

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    count_word()