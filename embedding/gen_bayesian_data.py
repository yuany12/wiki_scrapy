
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
    fout = open('author_index.out', 'w')
    for i, author in enumerate(authors):
        fout.write(author + '\n')
    fout.close()
    fout = open('keyword_index.out', 'w')
    for i, keyword in enumerate(keywords):
        fout.write(keyword + '\n')
    fout.close()

def format():
    authors, keywords = [], []
    author2id, keyword2id = {}, {}
    for i, line in enumerate(open('author_index.out')):
        author = line.strip()
        authors.append(author)
        author2id[author] = i
    for i, line in enumerate(open('keyword_index.out')):
        keyword = line.strip()
        keywords.append(keyword)
        keyword2id[keyword] = i

    fout = open('../bayesian/data.main.txt', 'w')
    fout.write("%d %d\n" % (len(authors), len(keywords)))
    cnt = 0
    for i in range(8):
        for line in open('gen_pair.%d.out' % i):
            if cnt % 10000 == 0:
                logging.info('printing author %d' % cnt)
            cnt += 1

            inputs = line.strip().split(';')
            fout.write("%d %d\n" % (author2id[inputs[0]], len(inputs) - 1))
            for j in range(1, len(inputs)):
                in_inputs = inputs[j].split(',')
                fout.write("%d %d\n" % (keyword2id[in_inputs[0]], int(in_inputs[1])))
    fout.close()

    model = gensim.models.Word2Vec.load('keyword.model')
    fout = open('../bayesian/data.embedding.keyword.txt', 'w')
    for i, keyword in enumerate(keywords):
        if i % 10000 == 0:
            logging.info('printing keyword %d/%d' % (i, len(keywords)))

        vec = model[keyword]
        for ele in vec:
            fout.write("%.8f\n" % ele)
    fout.close()

    model = gensim.models.Word2Vec.load('online.author_word.model')
    fout = open('../bayesian/data.embedding.researcher.txt', 'w')
    for i, author in enumerate(authors):
        if i % 10000 == 0:
            logging.info('printing author %d/%d' % (i, len(authors)))

        vec = model[author]
        for ele in vec:
            fout.write("%.8f\n" % ele)
    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # pool = multiprocessing.Pool(processes = 8)
    # pool.map(gen_pair, [(5000000, i) for i in range(8)])
    # indexing()
    format()
