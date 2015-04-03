
import cPickle
from collections import defaultdict as dd
import gensim
import logging

SIZE = 200
WINDOW = 10
MIN_COUNT = 10
SAMPLE = 1e-4

TH_DB_CNT = 10
TH_HIT_CNT = 4

class wiki_embedding:
    
    def load_vocab(self):
        title_keywords = cPickle.load(open('title_keywords.dump', 'rb'))
        abs_keywords = cPickle.load(open('abs_keywords.dump', 'rb'))

        self.keywords = dd(int)
        for k, v in title_keywords.iteritems():
            for keyword in v:
                self.keywords[keyword] += 1
        for k, v in abs_keywords.iteritems():
            for keyword in v:
                self.keywords[keyword] += 1

    def generator(self):
        cnt = 0
        for line in open('../../wiki/wiki.text'):
            if cnt % 100 == 0:
                logging.info('processing line %d/7980452' % cnt)
            cnt += 1
            inputs = line.strip().split()
            i, hit_cnt = 0, 0
            ret = []
            while i + 2 <= len(inputs):
                if i + 3 <= len(inputs):
                    new_word = "_".join(inputs[i: i + 3])
                    if self.keywords[new_word] > TH_DB_CNT:
                        ret.append(new_word)
                        i += 3
                        hit_cnt += 1
                        continue
                new_word = "_".join(inputs[i: i + 2])
                if self.keywords[new_word] > TH_DB_CNT:
                    ret.append(new_word)
                    i += 2
                    hit_cnt += 1
                    continue
                ret.append(inputs[i])
                i += 1
            if hit_cnt < TH_HIT_CNT: continue
            yield ret

    def train_model(self):
        model = gensim.models.Word2Vec(None, size = SIZE, window = WINDOW, min_count = MIN_COUNT, \
             workers = multiprocessing.cpu_count(), sample = SAMPLE)
        model.build_vocab(self.generator())
        model.train(self.generator())
        model.save('keyword.model')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    emd = wiki_embedding()
    emd.load_vocab()
    emd.train_model()

