import gensim
import MySQLdb as mdb

def arnet_conn():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def test():
    model = gensim.models.Word2Vec.load('author_word.model')
    cur = arnet_conn().cursor()
    for word in ['A_1458619', 'A_745329', 'A_123223', 'A_386117', 'A_1464342', 'A_826096', 'A_191749']:
        name = word
        if name.startswith('A_'):
            cur.execute("select names from na_person where id = %s", name[2:])
            name = cur.fetchone()[0]
        for e in model.most_similar(positive = [word], negative = [], topn = 15):
            if e[0].startswith('A_'):
                cur.execute("select names from na_person where id = %s", e[0][2:])
                e = (cur.fetchone()[0], e[1])
            print name, e

if __name__ == '__main__':
    test()