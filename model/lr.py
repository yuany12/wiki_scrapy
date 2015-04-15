
from sklearn import linear_model
import cPickle
import numpy as np
import logging
import data

def train_lr():
    clf = linear_model.LogisticRegression(C = 1.0, tol = 1e-6)
    features = np.load('features.npy')
    labels = np.load('labels.npy')
    logging.info('training lr')
    clf.fit(features, labels)
    logging.info('dumping lr')
    cPickle.dump(clf, open('lr_model.dump', 'wb'), protocol = 2)

def test_lr():
    clf = cPickle.load(open('lr_model.dump', 'rb'))
    author2wordvec, authorvec = data.load_vectors()

    fout = open('test_lr.out', 'w')

    for aid in [1458619, 826096, 935753, 123223, 745329, 687715, 191749, 1152750, 534472, 549002, 534472, 1622, 386117, \
    1464342, 221919, 161041, 265966, 560995, 750943, 14169490]:
        names, a_vec = authorvec[aid]
        ret = []
        for keyword, w_vec in author2wordvec[aid]:
            feature = np.concatenate((a_vec, w_vec))
            feature.reshape((1, feature.shape[0]))
            p = clf.predict_proba(feature)[0, 1]
            ret.append((keyword, p))
        ret.sort(key = lambda x: x[1], reverse = True)
        for keyword, p in ret:
            fout.write("%s,%s,%f\n" % (names, keyword, p))

    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # train_lr()
    test_lr()