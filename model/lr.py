
from sklearn import linear_model
import cPickle

def train_lr():
    clf = linear_model.LogisticRegression(C = 1.0, tol = 1e-6)
    features = np.load('features.npy')
    labels = np.load('labels.npy')
    clf.fit(features, labels)
    cPickle.dump(clf, open('lr_model.dump', 'wb'), protocol = 2)

if __name__ == '__main__':
    train_lr()