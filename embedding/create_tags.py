
import gensim
import pymongo
import multiprocessing

TH_WORD_CNT = 15

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30019)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def create_tags(bulk_info = (80000000, 0)):
    bulk_size, bulk_no = bulk_info

    model = gensim.models.Word2Vec.load('keyword.model')

    db = get_mongodb()
    people = db.people
    author_keywords = db.author_keywords

    for doc in author_keywords.find(skip = bulk_size * bulk_no, limit = bulk_size):
        if 'title_keywords' not in doc: continue
        keywords = doc['title_keywords'].keys()
        word2score = []
        for k1 in keywords:
            if k1 not in model: continue
            score_ = 0.0
            for k2 in keywords:
                if k2 not in model: continue
                score_ += model.similarity(k1, k2) * doc['title_keywords'][k2]
            word2score.append({'w': k1, 's': score_})
        if len(word2score) < TH_WORD_CNT: continue
        word2score.sort(key = lambda x: x['s'], reverse = True)
        people.find_one_and_update({'_id': doc['_id']}, {'$set': {'new_tags': word2score}})

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes = 4)
    pool.map(create_tags, [(10000000, i) for i in range(4)])
