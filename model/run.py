import MySQLdb as mdb
import cPickle
import collections
import numpy as np
import ntn
import gensim

SAMPLE_RATE = 0.5
DIMENSION = 128
SAMPLE_RATIO = 0.5

def get_reverse_index(model):
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
    cur.execute("select aid, tag, cnt from wiki_tag")
    word2cnt = collections.defaultdict(int)
    author2tags = collections.defaultdict(list)
    for row in cur.fetchall():
        word2cnt[row[1]] += row[2]
        author2tags['A_' + str(row[0])] += (row[1], row[2])
    for k in author2tags.keys():
        author2tags[k].sort(key = lambda x: x[1], reverse = True)
    return author2tags, word2cnt

def get_training_data(author2tags, keyword2idx, model, word2cnt):
    data = []
    for author, tags in author2tags.iteritems():
        if author not in model: continue
        author_idx = keyword2idx[author]
        for tag in tags[: SAMPLE_RATIO * len(tags)]:
            word = tag[0]
            if word2cnt[word] < 10 or word not in model: continue
            word_idx = keyword2idx[word]
            data.append([author_idx, word_idx])
    return np.array(data)

def train_model(keyword2idx, idx2keyword, word2cnt, author2tags, model):
    evs = np.zeros((DIMENSION, len(idx2keyword)))
    for i in range(len(idx2keyword)):
        evs[:, i] = model[idx2keyword[i]]
    params = {'embedding_size': DIMENSION, 'num_entities': len(index2keywords), 'slice_size': 5,
        'lamda': 1e-2, 'batch_size': 1000, 'corrupt_size': 10, 'num_iterations': 100,
        'batch_iterations': 5, 'ev_fixed': False, 'threshold': -0.0, 'save_file': 'ntn_model.dump'}
    network = ntn.my_neural_tensor_network(params, evs)
    data = get_training_data(author2tags, keyword2idx, model, word2cnt)
    network.train(data)

if __name__ == '__main__':
    cur = connect_arnet().cursor()
    model = gensim.models.Word2Vec.load('../embedding/author_word.model')
    keyword2idx, idx2keyword = get_reverse_index(model)
    author2tags, word2cnt = load_wiki_tag()
    train_model(keyword2idx, idx2keyword, word2cnt, author2tags, model)
