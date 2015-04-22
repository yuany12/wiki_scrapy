import MySQLdb as mdb
# import extractor
import collections
import gensim
import cPickle
import multiprocessing
import logging
import random
import rds
import pymongo

SIZE = 128
WINDOW = 5
# NEGATIVE = 10
RAN_TIMES = 200
LENGTH = 15
MIN_COUNT = 3

class author_embedding:

    def conn_db(self):
        password = open('password_mongo.txt').readline().strip()
        client = pymongo.MongoClient(host = 'localhost', port = 30017)
        db = client.bigsci
        db.authenticate('kegger_bigsci', password)
        return db

    def get_rds_client(self):
        return rds.RdsClient('localhost', 6383)

    def build_graph(self):
        db = self.conn_db()
        pubs = db.publication_dupl
        self.vertices = collections.defaultdict(list)
        self.vocab = []
        cnt, tot = 0, pubs.count()
        rds = self.get_rds_client()
        for doc in pubs.find():
            if cnt % 10000 == 0:
                logging.info('building graph %d/%d' % (cnt, tot))
            cnt += 1

            keywords = []
            if 'authors' not in doc: continue
            author_cnt = len(doc['authors'])
            for i in range(author_cnt):
                keywords.append(rds.get_author_id(str(doc['_id']), i))
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    self.vertices[keywords[i]].append(keywords[j])
                    self.vertices[keywords[j]].append(keywords[i])
            self.vocab.append(keywords)
        logging.info('vocab size = %d' % len(self.vocab))

    def save_graph(self):
        cPickle.dump(self.vertices, open('online.authors.graph.dump', 'wb'), protocol = 2)
        cPickle.dump(self.vocab, open('online.author_vocab.graph.dump', 'wb'), protocol = 2)

    def load_graph(self):
        self.vertices = cPickle.load(open('online.authors.graph.dump', 'rb'))
        self.vocab = cPickle.load(open('online.author_vocab.graph.dump', 'rb'))

    def generator(self):
        keys = self.vertices.keys()
        random.shuffle(keys)
        for key in keys:
            path = [key]
            for _ in range(LENGTH):
                path.append(random.choice(self.vertices[path[-1]]))
            yield path

    def train_model(self):
        model = gensim.models.Word2Vec(None, size = SIZE, window = WINDOW, min_count = MIN_COUNT, \
             workers = multiprocessing.cpu_count())
        model.build_vocab(self.vocab)
        for i in range(RAN_TIMES):
            logging.info('training model %d/%d' % (i, RAN_TIMES))
            model.train(self.generator())
            if i % 10 == 0:
                model.save('online.author_word.model')

    def resume_training(self):
        model = gensim.models.Word2Vec.load('online.author_word.model')
        for i in range(RAN_TIMES):
            logging.info('training model %d/%d' % (i, RAN_TIMES))
            model.train(self.generator())
            model.save('online.author_word.model')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # emd = author_word_embedding()
    emd = author_embedding()
    emd.build_graph()
    emd.save_graph()
    emd.train_model()
    # emd.load_graph()
    # emd.resume_training()
    