import gensim
import MySQLdb as mdb
# from tsne import bh_sne
# from matplotlib import pyplot as plt
import numpy as np
import random
import string
import cPickle
from collections import defaultdict as dd

def arnet_conn():
    password = open('password.txt').readline().strip()
    return mdb.connect('127.0.0.1', 'root', password, 'arnet_db')

def test():
    model = gensim.models.Word2Vec.load('author_word.model')
    x, label = [], []
    cur = arnet_conn().cursor()
    for word in ['A_1458619', 'A_745329', 'A_123223', 'A_386117', 'A_1464342', 'A_826096', 'A_191749', 'A_221919', \
     'A_161041', 'A_265966', 'A_560995', 'A_750943', 'A_14169490', 'A_1479768', 'A_340525', 'A_773167', 'A_173433', \
     'A_546561', 'A_856261']:
        name = word
        if name.startswith('A_'):
            cur.execute("select names from na_person where id = %s", name[2:])
            name = cur.fetchone()[0]

        x.append(model[word])
        label.append(name)

        for e in model.most_similar(positive = [word], negative = [], topn = 15):
            if e[0].startswith('A_'):
                x.append(model[e[0]])
                label.append('')

                cur.execute("select names from na_person where id = %s", e[0][2:])
                row = cur.fetchone()
                if row is not None and row[0] is not None:
                    e = (row[0], e[1])
            print name, e
    x = bh_sne(np.array(x, dtype = np.float64))
    x1, x2 = x[:, 0], x[:, 1]

    fig, ax = plt.subplots()
    ax.scatter(x1, x2)

    for i in range(len(label)):
        ax.annotate(label[i], xy = (x1[i], x2[i]))

    plt.savefig('test.embedding.png', bbox_inches = 'tight')

def sample_vectors():
    model = gensim.models.Word2Vec.load('keyword.model')
    title_keywords = cPickle.load(open('title_keywords.dump', 'rb'))

    cur = arnet_conn().cursor()
    author2wordvec = dd(list)

    for aid in [1458619, 826096, 935753, 123223, 745329, 687715, 191749, 1152750]:
        cur.execute("select pid from na_author2pub where aid = %s", aid)
        row = cur.fetchone()
        if row is not None and row[0] is not None and row[0] in title_keywords:
            for keyword in title_keywords[row[0]]:
                if keyword not in model: continue
                author2wordvec[aid].append((keyword, model[keyword]))
    cPickle.dump(author2wordvec, open('vector_case_study.dump', 'wb'))


if __name__ == '__main__':
    # test()
    sample_vectors()