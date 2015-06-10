
from bs4 import BeautifulSoup
import os

def test_bayesian():
    author2words = {}
    for line in open('model.predict.txt'):
        inputs = line.strip().split(',')
        author = inputs[0]
        author2words[author] = []
        for keyword in inputs[1: ]:
            author2words[author].append(keyword)

    target_authors = []
    rt, rt_cnt = 0.0, 0
    for filename in os.listdir('../homepage'):
        author = filename.split('.')[0]
        if author not in author2words: continue

        doc = open('../homepage/' + filename).read()
        soup = BeautifulSoup(doc)
        doc = soup.get_text()

        pos_cnt, neg_cnt = 0, 0

        for keyword in author2words[author][: 5]:
            if keyword.replace('_', ' ') in doc: pos_cnt += 1
            else: neg_cnt += 1

        rt += 1.0 * pos_cnt / (pos_cnt + neg_cnt)
        rt_cnt += 1

    print rt / rt_cnt

if __name__ == '__main__':
    test_bayesian()