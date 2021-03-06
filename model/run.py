import MySQLdb as mdb
import cPickle
import collections
import numpy as np
import ntn
import gensim
import logging

DIMENSION = 128
SAMPLE_RATIO = 0.18

def get_reverse_index(model):
    logging.info('get_reverse_index')
    vocab = cPickle.load(open('../embedding/vocab.graph.dump', 'rb'))
    keyword2idx, idx2keyword = collections.defaultdict(int), []
    idx = 0
    for keywords in vocab:
        for keyword in keywords:
            if keyword not in model: continue
            keyword2idx[keyword] = idx
            idx2keyword.append(keyword)
            idx += 1
    return keyword2idx, idx2keyword

def connect_arnet():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def load_wiki_tag(cur):
    logging.info('load_wiki_tag')
    cur.execute("select aid, tag, cnt from wiki_tag")
    word2cnt = collections.defaultdict(int)
    author2tags = collections.defaultdict(list)
    for row in cur.fetchall():
        word2cnt[row[1]] += row[2]
        author2tags['A_' + str(row[0])].append((row[1], row[2]))
    for k in author2tags.keys():
        author2tags[k].sort(key = lambda x: x[1], reverse = True)
    return author2tags, word2cnt

def get_training_data(author2tags, keyword2idx, model, word2cnt):
    logging.info('get_training_data')
    data = []
    for author, tags in author2tags.iteritems():
        if author not in model: continue
        author_idx = keyword2idx[author]
        for tag in tags[: int(SAMPLE_RATIO * len(tags))]:
            word = tag[0]
            if word2cnt[word] < 10 or word not in model: continue
            word_idx = keyword2idx[word]
            data.append([author_idx, word_idx])
    logging.info('training data size = %d' % len(data))
    return np.array(data)

def train_model(keyword2idx, idx2keyword, word2cnt, author2tags, model):
    evs = np.zeros((DIMENSION, len(idx2keyword)))
    for i in range(len(idx2keyword)):
        evs[:, i] = model[idx2keyword[i]]
    params = {'embedding_size': DIMENSION, 'num_entities': len(idx2keyword), 'slice_size': 4,
        'lamda': 1e-2, 'batch_size': 1000, 'corrupt_size': 10, 'num_iterations': 500, 'save_period': 10,
        'batch_iterations': 5, 'ev_fixed': True, 'threshold': -0.0, 'save_file': 'ntn_model.dump'}
    network = ntn.my_neural_tensor_network(params, init_evs = evs, load_file = 'ntn_model.dump')
    data = get_training_data(author2tags, keyword2idx, model, word2cnt)
    network.train(data)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = connect_arnet().cursor()
    model = gensim.models.Word2Vec.load('../embedding/author_word.model')
    keyword2idx, idx2keyword = get_reverse_index(model)
    author2tags, word2cnt = load_wiki_tag(cur)
    train_model(keyword2idx, idx2keyword, word2cnt, author2tags, model)
