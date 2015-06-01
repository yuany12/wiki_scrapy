
import pymongo
from collections import defaultdict as dd
import multiprocessing
import logging
from bson.objectid import ObjectId
import time
import gensim

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30019)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def gen_pair(bulk_info = (39000000, 0)):
    model = gensim.models.Word2Vec.load('keyword.model')

    bulk_size, bulk_no = bulk_info

    db = get_mongodb()
    author_keywords = db.author_keywords
    cnt, tot = 0, author_keywords.count()

    recs = []

    for doc in author_keywords.find(skip = bulk_size * bulk_no, limit = bulk_size):
        if cnt % 100 == 0:
            logging.info('generating %d/%d in thread %d' % (cnt, tot, bulk_no))
        cnt += 1

        if 'title_keywords' not in doc: continue
        valid_cnt = 0
        for k, v in doc['title_keywords'].iteritems():
            if k in model: valid_cnt += 1
        if valid_cnt < 10: continue
        recs.append((str(doc['_id']), doc['title_keywords']))

        if len(recs) == 10000:
            fout = open('gen_pair.%d.out' % bulk_no, 'a+')
            for rec in recs:
                fout.write('%s' % rec[0])
                for k, v in rec[1].iteritems():
                    if k not in model: continue
                    fout.write(';%s,%d' % (k, v))
                fout.write('\n')
            fout.close()
            recs = []

    if len(recs) > 0:
        fout = open('gen_pair.%d.out' % bulk_no, 'a+')
        for rec in recs:
            fout.write('%s' % rec[0])
            for k, v in rec[1].iteritems():
                if k not in model: continue
                fout.write(';%s,%d' % (k, v))
            fout.write('\n')
        fout.close()

def indexing():
    authors, keywords = set(), set()
    cnt = 0
    for i in range(8):
        for line in open('gen_pair.%d.out' % i):
            if cnt % 10000 == 0:
                logging.info('indexing %d' % cnt)
            cnt += 1

            inputs = line.strip().split(';')
            authors.add(inputs[0])
            for j in range(1, len(inputs)):
                keywords.add(inputs[j].split(',')[0])
    fout = open('author_index.out')
    for i, author in enumerate(authors):
        fout.write(author + '\n')
    fout.close()
    fout = open('keyword_index.out')
    for i, keyword in enumerate(keywords):
        fout.write(keyword + '\n')
    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # pool = multiprocessing.Pool(processes = 8)
    # pool.map(gen_pair, [(5000000, i) for i in range(8)])
    indexing()
