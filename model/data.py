
import gensim
import cPickle
from collections import defaultdict as dd
import MySQLdb as mdb

def sample_vectors():
    model = gensim.models.Word2Vec.load('../embedding/keyword.model')
    title_keywords = cPickle.load(open('../embedding/title_keywords.dump', 'rb'))
    abs_keywords = cPickle.load(open('../embedding/abs_keywords.dump', 'rb'))

    cur = arnet_conn().cursor()
    author2wordvec = dd(list)

    for aid in [1458619, 826096, 935753, 123223, 745329, 687715, 191749, 1152750, 534472, 549002, 534472, 1622, 386117, \
    1464342, 221919, 161041, 265966, 560995, 750943, 14169490]:
        cur.execute("select pid from na_author2pub where aid = %s", aid)
        for row in cur.fetchall():
            if row is not None and row[0] is not None:
                if row[0] in title_keywords:
                    for keyword in title_keywords[row[0]]:
                        if keyword not in model: continue
                        author2wordvec[aid].append((keyword, model[keyword]))
                if row[0] in abs_keywords:
                    for keyword in abs_keywords[row[0]]:
                        if keyword not in model: continue
                        author2wordvec[aid].append((keyword, model[keyword]))

    cPickle.dump(author2wordvec, open('author2wordvec.dump', 'wb'), protocol = 2)

    author_model = load_author_model()
    authorvec = {}
    for aid in author2wordvec.keys():
        cur.execute("select names from na_person where id = %s", aid)
        names = cur.fetchone()[0]
        a_str = 'A_' + str(aid)
        vec = author_model[a_str]
        authorvec[aid] = (names, vec)

    cPickle.dump(authorvec, open('authorvec', 'wb'), protocol = 2) 

def arnet_conn():
    password = open('password.txt').readline().strip()
    return mdb.connect('127.0.0.1', 'root', password, 'arnet_db')

def load_author_model():
    logging.info('loading author model')
    return gensim.models.Word2Vec.load('../embedding/author_word.model')

def load_keyword_model():
    logging.info('loading keyword model')
    return gensim.models.Word2Vec.load('../embedding/keyword.model')

if __name__ == '__main__':
    sample_vectors()
