
from bs4 import BeautifulSoup
import os
import pymongo
from bson.objectid import ObjectId
import spacy.en

def gen_test_data(bulk_info):
    bulk_size, bulk_no = bulk_info

    nlp = spacy.en.English()

    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = set()
        for keyword in inputs[1: ]:
            author2words[author].add(keyword)

    gt = {}

    filenames = os.listdir('../homepage')
    cnt = 0
    for filename in filenames[bulk_no * bulk_size: min((bulk_no + 1) * bulk_size, len(filenames))]:
        if cnt % 1000 == 0:
            print cnt, bulk_no
        cnt += 1

        author = filename.split('.')[0]
        if author not in author2words: continue

        doc = open('../homepage/' + filename).read()
        soup = BeautifulSoup(doc)
        doc = soup.get_text()

        keywords = set()

        tokens = [e.orth_.lower() for e in nlp(doc, tag = False, parse = False)]
        for i in range(len(tokens) - 1):
            new_word = "_".join(tokens[i: i + 2])
            if new_word in author2words[author]:
                keywords.add(new_word)
        for i in range(len(tokens) - 2):
            new_word = "_".join(tokens[i: i + 3])
            if new_word in author2words[author]:
                keywords.add(new_word)
        if len(keywords) < 5: continue
        gt[author] = keywords

    fout = open('homepage_test_%d.txt' % bulk_no, 'w')
    for k, v in gt.iteritems():
        fout.write(k)
        for e in v:
            fout.write(',' + e)
        fout.write('\n')
    fout.close()

def gen_():
    CORE_NUM = 64
    bulk_size = 68000 / CORE_NUM

    pool = multiprocessing.Pool(processes = CORE_NUM)
    pool.map(gen_test_data, [(i, bulk_size) for i in range(CORE_NUM)])

    fout = open('homepage_test.txt', 'w')
    for i in range(CORE_NUM):
        for line in open('homepage_test_%d.txt' % i):
            fout.write(line)
    fout.close()

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
    for filename in os.listdir('../homepage'):
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
    # test_old()
    gen_()