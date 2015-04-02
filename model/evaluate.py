
from collections import defaultdict as dd
import gensim
import ntn
import run
import numpy as np
import logging

DIMENSION = 128

def load_persons(jconf):
    logging.info('loading persons')
    return [int(line.strip()) for line in open('person_desym_' + jconf + '.out')]

def load_author2words(jconf):
    logging.info('loading author word mappings')
    author2words = dd(list)
    for line in open('res_' + jconf + '.out'):
        inputs = line.strip().split('\t')
        if len(inputs) < 3: continue
        id = int(inputs[0])
        for word in inputs[2].split('|'):
            author2words[id].append(word)
    return author2words

def load_word_label(jconf):
    logging.info('loading word labels')
    word2label = {}
    for line in open('re_desym_' + jconf + '.out.csv'):
        inputs = line.strip().split(',')
        word2label[inputs[1]] = int(inputs[0])
    return word2label

def test():
    model = gensim.models.Word2Vec.load('../embedding/author_word.model')
    keyword2idx, idx2keyword = run.get_reverse_index(model)

    evs = np.zeros((DIMENSION, len(idx2keyword)))
    for i in range(len(idx2keyword)):
        evs[:, i] = model[idx2keyword[i]]

    logging.info('loading neural tensor network')
    params = {'embedding_size': DIMENSION, 'num_entities': len(idx2keyword), 'slice_size': 4,
        'lamda': 1e-2, 'batch_size': 1000, 'corrupt_size': 10, 'num_iterations': 500, 'save_period': 10,
        'batch_iterations': 5, 'ev_fixed': True, 'threshold': -0.0, 'save_file': 'ntn_model.dump'}
    network = ntn.my_neural_tensor_network(params, init_evs = evs, load_file = 'ntn_model.dump')

    for jconf in ['KDD', 'ICML']:
        persons = load_persons(jconf)
        author2words = load_author2words(jconf)
        word2label = load_word_label(jconf)
        test_data, test_label = [], []
        for author in persons:
            words = author2words[author]
            for word in words:
                if word not in word2label or word not in keyword2idx: continue
                author_id, word_id = keyword2idx['A_' + str(author)], keyword2idx[word]
                test_data.append([author_id, word_id])
                label = 1 if word2label[word] == 1 else 0
                test_label.append(label)
        test_data = np.array(test_data, dtype = np.int32)

        logging.info('predicting %s' % jconf)

        p_data = network.predict(test_data, score = True)
        fout = open('ntn_predict_' + jconf + '.out', 'w')
        for i in range(len(test_label)):
            author = idx2keyword[test_data[i][0]]
            word = idx2keyword[test_data[i][1]]
            fout.write(",".join([author, word, str(test_label[i]), str(p_data[i])]) + '\n')
        fout.close()

def measure(py, y):
    tp, fn, fp = 0, 0, 0
    for i in range(len(py)):
        if py[i] == 1 and y[i] == 1: tp += 1
        elif py[i] == 1: fp += 1
        elif y[i] == 1: fn += 1
    prec = float(tp) / (tp + fp) if tp + fp > 0 else 0.0
    recall = float(tp) / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0
    logging.info('precision = %.8f' % prec)
    logging.info('recall = %.8f' % recall)
    logging.info('f1 = %.8f' % f1)

def calc_score():
    for jconf in ['KDD', 'ICML']:
        py, y = [], []
        for line in open('ntn_predict_' + jconf + '.out'):
            inputs = line.strip().split(',')
            py.append(float(inputs[-1]))
            y.append(int(inputs[-2]))
        py = sorted([(py[i], i) for i in range(len(py))], key = lambda x: x[0], reverse = True)
        pos_cnt = sum(y)
        ry = [0 for _ in range(len(y))]
        for i in range(pos_cnt):
            ry[py[i][1]] = 1
        measure(ry, y)

def sort_res():
    for jconf in ['KDD', 'ICML']:
        l = []
        for line in open('ntn_predict_' + jconf + '.out'):
            inputs = line.strip().split(',')
            l.append((line, float(inputs[-1])))
        l.sort(key = lambda x: x[1], reverse = True)
        fout = open('ntn_predict_' + jconf + '.sort.out', 'w')
        for e in l:
            fout.write(e[0])
        fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # test()
    # calc_score()
    sort_res()
