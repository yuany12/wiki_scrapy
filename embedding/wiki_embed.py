
import cPickle
from collections import defaultdict as dd
import gensim
import logging
import multiprocessing

SIZE = 200
WINDOW = 10
MIN_COUNT = 10
SAMPLE = 1e-4

TH_DB_CNT = 10
TH_HIT_CNT = 4

class wiki_embedding:
    
    def load_vocab(self):
        logging.info('loading title_keywords')
        title_keywords = cPickle.load(open('title_keywords.dump', 'rb'))

        logging.info('loading abs_keywords')
        abs_keywords = cPickle.load(open('abs_keywords.dump', 'rb'))

        self.keywords = dd(int)
        cnt, tot = 0, len(title_keywords)
        for k, v in title_keywords.iteritems():
            if cnt % 10000 == 0:
                logging.info('iterating title_keywords %d/%d' % (cnt, tot))
            cnt += 1

            for keyword in v:
                self.keywords[keyword] += 1

        cnt, tot = 0, len(abs_keywords)
        for k, v in abs_keywords.iteritems():
            if cnt % 10000 == 0:
                logging.info('iterating abs_keywords %d/%d' % (cnt, tot))
            cnt += 1

            for keyword in v:
                self.keywords[keyword] += 1

    def generator(self):
        cnt = 0
        cache = []
        for line in open('../../wiki/wiki.text'):
            if cnt % 100 == 0:
                logging.info('writing line %d/7980452' % cnt)
                fout = open('wiki_corpus.txt', 'a+')
                for cacheline in cache:
                    fout.write(cacheline + '\n')
                fout.close()
                cache = []
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
            cache.append(" ".join(ret))
            yield ret

    def loader(self):
        for line in open('wiki_corpus.txt'):
            yield line.strip().split()

    def train_model(self):
        model = gensim.models.Word2Vec(None, size = SIZE, window = WINDOW, min_count = MIN_COUNT, \
             workers = multiprocessing.cpu_count(), sample = SAMPLE)
        model.build_vocab(self.generator())
        model.save('keyword.model')
        model.train(self.loader())
        model.save('keyword.model')

    def resume_training(self):
        model = gensim.models.Word2Vec.load('keyword.model')
        model.train(self.loader())
        model.save('keyword.model')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    emd = wiki_embedding()
    emd.load_vocab()
    emd.train_model()

