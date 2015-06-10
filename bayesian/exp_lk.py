
import json
import pymongo
from bson.objectid import ObjectId

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

        for keyword in author2words[author]:
            flag = False
            for skill in doc['skills']:
                skill = skill.lower().replace(' ', '_')
                if skill in keyword or keyword in skill:
                    flag = True
                    break
            if flag:
                keywords.add(keyword)
        if len(keywords) > 0:
            gt[author] = keywords

    fout = open('lk_test.txt', 'w')
    for k, v in gt.iteritems():
        fout.write(k)
        for e in v:
            fout.write(',' + e)
        fout.write('\n')
    fout.close()

if __name__ == '__main__':
    gen_test_data()