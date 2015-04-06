
import gensim
import cPickle

def load_author_model():
    return gensim.models.Word2Vec.load('../embedding/author_word.model')

def load_keyword_model():
    return gensim.models.Word2Vec.load('../embedding/keyword.model')

def load_keyword_dict():
    title_keywords = cPickle.load('../embedding/title_keywords.dump')
    abs_keywords = cPickle.load('../embedding/abs_keywords.dump')
    return title_keywords, abs_keywords

def gen_dataset():
    password = open('password.txt').readline().strip()
    cur = mdb.connect('localhost', 'root', password, 'arnet_db').cursor()
    cur.execute("select id from na_person")
    for row in cur.fetchall():
        if row is not None and row[0] is not None:
            cur.execute("select pid from na_author2pub where aid = %s", row[0])