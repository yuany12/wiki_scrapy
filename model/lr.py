
from sklearn import linear_model
import cPickle
import numpy as np
import logging
import data
import random

def train_lr():
    clf = linear_model.LogisticRegression(C = 1.0, tol = 1e-6)
    features = np.load('features.npy')
    labels = np.load('labels.npy')
    logging.info('training lr')
    clf.fit(features, labels)
    logging.info('dumping lr')
    cPickle.dump(clf, open('lr_model.dump', 'wb'), protocol = 2)

def train_tensor_lr():
    clf = linear_model.LogisticRegression(solver = 'lbfgs', verbose = 1)
    # features = np.load('features.npy')
    labels = np.load('labels.npy')
    # selector = np.load('tensor_selector.npy')
    # dim = np.sum(selector)
    # new_features = np.zeros((features.shape[0], 128 + 200 + dim), dtype = np.float32)
    # for i in range(features.shape[0]):
    #     if i % 1000 == 0:
    #         logging.info('trainsforming %d' % i)
    #     new_features[i, : 328] = features[i, :]
    #     new_features[i, 328 :] = np.outer(features[i, :128], features[i, 128:]).flatten()[selector]

    # np.save('tensor_features.npy', new_features)
    new_features = np.load('tensor_features.npy')

    logging.info('training tensor lr')
    clf.fit(new_features, labels)

    logging.info('dumping tensor lr')
    cPickle.dump(clf, open('tensor_lr_model.dump', 'wb'), protocol = 2)

def test_lr():
    clf = cPickle.load(open('lr_model.dump', 'rb'))
    author2wordvec, authorvec = data.load_vectors()

    fout = open('test_lr.out', 'w')

    for aid in [1458619, 826096, 935753, 123223, 745329, 687715, 191749, 1152750, 534472, 549002, 534472, 1622, 386117, \
    1464342, 221919, 161041, 265966, 560995, 750943, 14169490]:
        if aid not in authorvec or aid not in author2wordvec: continue
        names, a_vec = authorvec[aid]
        ret = []
        word_set = set()
        for keyword, w_vec in author2wordvec[aid]:
            if keyword in word_set: continue
            word_set.add(keyword)
            feature = np.concatenate((a_vec, w_vec))
            feature.reshape((1, feature.shape[0]))
            p = clf.predict_proba(feature)[0, 1]
            ret.append((keyword, p))
        ret.sort(key = lambda x: x[1], reverse = True)
        for keyword, p in ret:
            fout.write("%s,%s,%f\n" % (names, keyword, p))
        fout.write("=" * 20 + '\n')

    fout.close()

def gen_tensor_selector():
    s = np.concatenate((np.ones(128 + 200, dtype = np.int32), np.zeros(128 * 200, dtype = np.int32)))
    s = np.zeros(128 * 200, dtype = np.bool)
    for i in range(128 * 200):
        if random.random() < 0.1:
            s[i] = True
    np.save('tensor_selector.npy', s)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # train_lr()
    # test_lr()
    # gen_tensor_selector()
    train_tensor_lr()
