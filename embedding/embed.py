import MySQLdb as mdb
import extractor
import collections
import gensim
import cPickle
import multiprocessing
import logging
import random

SIZE = 128
WINDOW = 7
NEGATIVE = 10
RAN_TIMES = 100
LENGTH = 20

class author_word_embedding:

    def conn_db(self, database):
        password = open('password.txt').readline().strip()
        db = mdb.connect('localhost', 'root', password, database)
        db.set_character_set('utf8')
        return db

    def build_graph(self):
        cur = self.conn_db('arnet_db').cursor()
        cur.execute("select id, title from publication")
        self.vertices = collections.defaultdict(list)
        self.vocab = []
        ext = extractor.extractor(self.conn_db('wikipedia').cursor())
        cnt, tot = 0, cur.rowcount
        for row in cur.fetchall():
            if cnt % 10000 == 0:
                logging.info('building graph %d/%d' % (cnt, tot))
            cnt += 1
            keywords = ext.extract_str(row[1])
            cur.execute("select abstract from publication_ext where id = %d" % row[0])
            sub_row = cur.fetchone()
            if sub_row is not None and sub_row[0] is not None and sub_row[0] != '': keywords += ext.extract_str(sub_row[0])
            cur.execute("select aid from na_author2pub where pid = %d" % row[0])
            for sub_row in cur.fetchall():
                keywords.append("A_" + str(sub_row[0]))
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    self.vertices[keywords[i]].append(keywords[j])
                    self.vertices[keywords[j]].append(keywords[i])
            self.vocab.append(keywords)
        logging.debug('vocab size = %d' % len(self.vocab))

    def save_graph(self):
        cPickle.dump(self.vertices, open('vertices.graph.dump', 'wb'))
        cPickle.dump(self.vocab, open('vocab.graph.dump', 'wb'))

    def load_graph(self):
        self.vertices = cPickle.load(open('vertices.graph.dump', 'rb'))
        self.vocab = cPickle.load(open('vocab.graph.dump', 'rb'))

    def generator(self):
        keys = self.vertices.keys()
        random.shuffle(keys)
        for key in keys:
            path = [key]
            for _ in range(LENGTH):
                path.append(random.choice(self.vertices[path[-1]]))
            yield path

    def train_model(self):
        model = gensim.models.Word2Vec(None, size = SIZE, window = WINDOW, min_count = 0, negative = NEGATIVE, \
             workers = multiprocessing.cpu_count())
        model.build_vocab(self.vocab)
        for i in range(RAN_TIMES):
            logging.info('training model %d/%d' % (i, RAN_TIMES))
            model.train(self.generator())
            model.save('author_word.model')

    def resume_training(self):
        model = gensim.models.Word2Vec.load('author_word.model')
        model.window = WINDOW
        for i in range(RAN_TIMES):
            logging.info('training model %d/%d' % (i, RAN_TIMES))
            model.train(self.generator())
            model.save('author_word.model')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    emd = author_word_embedding()
    #emd.build_graph()
    #emd.save_graph()
    #emd.train_model()
    emd.load_graph()
    emd.resume_training()
    