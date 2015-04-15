
from sklearn import linear_model
import cPickle
import numpy as np
import logging

def train_lr():
    clf = linear_model.LogisticRegression(C = 1.0, tol = 1e-6)
    features = np.load('features.npy')
    labels = np.load('labels.npy')
    logging.info('training lr')
    clf.fit(features, labels)
    logging.info('dumping lr')
    cPickle.dump(clf, open('lr_model.dump', 'wb'), protocol = 2)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    train_lr()