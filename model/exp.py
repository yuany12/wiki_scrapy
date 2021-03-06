
import MySQLdb as mdb
import gensim
import cPickle
from collections import defaultdict as dd
import numpy as np
import logging
import random

SAMPLE_RATE = 0.2
WORD_CNT_TH = 20
NEG_POS_RATIO = 10

def load_author_model():
    logging.info('loading author model')
    return gensim.models.Word2Vec.load('../embedding/author_word.model')

def load_keyword_model():
    logging.info('loading keyword model')
    return gensim.models.Word2Vec.load('../embedding/keyword.model')

def load_keyword_dict():
    logging.info('loading title keywords')
    title_keywords = cPickle.load(open('../embedding/title_keywords.dump', 'rb'))

    logging.info('loading abstract keywords')
    abs_keywords = cPickle.load(open('../embedding/abs_keywords.dump', 'rb'))

    return title_keywords, abs_keywords

def gen_dataset(title_keywords, abs_keywords, author_model, keyword_model):
    password = open('password.txt').readline().strip()
    cur = mdb.connect('localhost', 'root', password, 'arnet_db').cursor()

    logging.info('loading na_person')
    cur.execute("select id from na_person")
    fout = open('gold_data.txt', 'w')
    cnt, tot = 0, cur.rowcount
    for row in cur.fetchall():
        if cnt % 1000 == 0:
            logging.info('generating %d/%d' % (cnt, tot))
        cnt += 1

        if row is not None and row[0] is not None:
            author_str = 'A_' + str(row[0])
            if author_str not in author_model: continue
            keyword_cnt = dd(int)
            cur.execute("select pid from na_author2pub where aid = %s", row[0])
            for subrow in cur.fetchall():
                if subrow is not None and subrow[0] is not None:
                    if subrow[0] in title_keywords:
                        for keyword in title_keywords[subrow[0]]:
                            keyword_cnt[keyword] += 1
            keys = keyword_cnt.keys()
            if len(keys) < WORD_CNT_TH: continue
            keyword_dist = []
            for k1 in keys:
                cur_dist = 0.0
                if k1 not in keyword_model: continue
                for k2 in keys:
                    # if k1 == k2: continue
                    if k2 not in keyword_model: continue
                    # cur_dist += np.linalg.norm(keyword_model[k1] - keyword_model[k2]) * keyword_cnt[k2]
                    cur_dist += keyword_model.similarity(k1, k2) * keyword_cnt[k2]
                keyword_dist.append((k1, cur_dist))
            keyword_dist.sort(key = lambda x: x[1], reverse = True)
            for keyword, _ in keyword_dist[:int(len(keyword_dist) * SAMPLE_RATE)]:
                fout.write(author_str + ',' + keyword + '\n')
    fout.close()

def create_npy(author_model, keyword_model):
    pos_pairs, neg_pairs = [], []
    authors, keywords = [], []
    cnt, tot = 0, 250000
    for line in open('gold_data.txt'):
        if cnt % 10000 == 0:
            logging.info('loading gold data %d/%d' % (cnt, tot))
        cnt += 1

        inputs = line.strip().split(',')
        pos_pairs.append((inputs[0], inputs[1]))
        authors.append(inputs[0])
        keywords.append(inputs[1])

    tot = len(pos_pairs) * NEG_POS_RATIO
    for i in range(tot):
        if i % 10000 == 0:
            logging.info('sampling negative instances %d/%d' % (i, tot))

        author = random.choice(authors)
        keyword = random.choice(keywords)
        neg_pairs.append((author, keyword))

    features = np.zeros((len(pos_pairs) + len(neg_pairs), 128 + 200), dtype = np.float32)
    labels = np.concatenate((np.ones(len(pos_pairs), dtype = np.int32), np.zeros(len(neg_pairs), dtype = np.int32)))
    
    tot = len(pos_pairs) + len(neg_pairs)
    for i, pair in enumerate(pos_pairs + neg_pairs):
        if i % 10000 == 0:
            logging.info('creating features %d/%d' % (i, tot))

        features[i, :] = np.concatenate((author_model[pair[0]], keyword_model[pair[1]]))
    index = np.random.permutation(np.arange(features.shape[0]))
    features = features[index]
    labels = labels[index]

    logging.info('saving npy')

    np.save('features', features)
    np.save('labels', labels)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    title_keywords, abs_keywords = load_keyword_dict()
    author_model = load_author_model()
    keyword_model = load_keyword_model()
    # gen_dataset(title_keywords, abs_keywords, author_model, keyword_model)
    create_npy(author_model, keyword_model)

