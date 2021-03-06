
import pymongo
from collections import defaultdict as dd
import multiprocessing
import logging
from bson.objectid import ObjectId
import time
import gensim
import random
import os
import numpy as np
import json

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

def select(bulk_info):
    model = gensim.models.Word2Vec.load('keyword.model')

    strs = []
    for i in range(8):
        for line in open('gen_pair.%d.out' % i):
            strs.append(line.strip())

    bulk_no, bulk_size = bulk_info
    fout = open('pair.select.%d.txt' % bulk_no, 'w')
    for i in range(bulk_size * bulk_no, min(len(strs), bulk_size * (bulk_no + 1))):
        if i % 1000 == 0:
            logging.info('selecting %d/%d in thread %d' % (i, bulk_size, bulk_no))

        inputs = strs[i].split(';')
        rid = inputs[0]
        keywords = []
        for j in range(1, len(inputs)):
            in_inputs = inputs[j].split(',')
            keywords.append((in_inputs[0], int(in_inputs[1])))
        stats = []
        for j in range(len(keywords)):
            score = 0.0
            for k in range(len(keywords)):
                score += model.similarity(keywords[j][0], keywords[k][0]) * keywords[k][1]
            stats.append((keywords[j][0], keywords[j][1], score))
        stats.sort(key = lambda x: x[2], reverse = True)

        fout.write(rid)
        for j in range(int(len(stats) * 0.5)):
            fout.write(';%s,%d' % (stats[j][0], stats[j][1]))
        fout.write('\n')
    fout.close()

def select_():
    CORE_NUM = 16
    bulk_size = 650000 / CORE_NUM

    pool = multiprocessing.Pool(processes = CORE_NUM)
    pool.map(select, [(i, bulk_size) for i in range(CORE_NUM)])

def merge():
    fout = open('pair.select.txt', 'w')
    for i in range(16):
        for line in open('pair.select.%d.txt' % i):
            fout.write(line)
    fout.close()

def sample():
    target_authors = []
    for filename in os.listdir('../homepage'):
        target_authors.append(filename.split('.')[0])
    target_authors = set(target_authors)

    authors_in_lk = json.load(open('../match_linkedin.json'))
    authors_in_lk = [e[1] for e in authors_in_lk]

    for author in authors_in_lk:
        target_authors.add(author)

    fout = open('sample.pair.select.txt', 'w')
    temp_list = []
    for line in open('pair.select.txt'):
        temp_list.append((line, len(line.strip().split(';'))))
    temp_list.sort(key = lambda x: x[1], reverse = True)

    cutoff = int(len(temp_list) * 0.1)
    for line, _ in temp_list[: cutoff]:
        fout.write(line)

    for line, _ in temp_list[cutoff :]:
        if line.strip().split(';')[0] in target_authors or random.random() < 0.1:
            fout.write(line)
    fout.close()

def indexing(model):
    # model = gensim.models.Word2Vec.load('online.author_word.model')
    authors, keywords = set(), set()
    cnt = 0
    for line in open('sample.pair.select.txt'):
        if cnt % 10000 == 0:
            logging.info('indexing %d' % cnt)
        cnt += 1

        inputs = line.strip().split(';')
        if inputs[0] not in model: continue
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

def format(a_model):
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
    for line in open('sample.pair.select.txt'):
        if cnt % 10000 == 0:
            logging.info('printing author %d' % cnt)
        cnt += 1

        inputs = line.strip().split(';')
        if inputs[0] not in author2id: continue
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
        norm = np.linalg.norm(vec)
        vec /= norm
        for ele in vec:
            fout.write("%.8f\n" % ele)
    fout.close()

    model = a_model
    fout = open('../bayesian/data.embedding.researcher.txt', 'w')
    for i, author in enumerate(authors):
        if i % 10000 == 0:
            logging.info('printing author %d/%d' % (i, len(authors)))

        vec = model[author]
        norm = np.linalg.norm(vec)
        vec /= norm
        for ele in vec:
            fout.write("%.8f\n" % ele)
    fout.close()

def cnt_pair():
    cnt = 0
    for line in open('sample.pair.select.txt'):
        inputs = line.strip().split(';')
        cnt += len(inputs) - 1
    print cnt

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    model = gensim.models.Word2Vec.load('online.author_word.model')
    # pool = multiprocessing.Pool(processes = 8)
    # pool.map(gen_pair, [(5000000, i) for i in range(8)])
    # select_()
    # merge()
    sample()
    indexing(model)
    format(model)
    cnt_pair()
