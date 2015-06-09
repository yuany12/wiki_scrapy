
import os
import json

def count_overlap():
    authors_in_data = []
    for line in open('author_index.out'):
        authors_in_data.append(line.strip())
    authors_in_data = set(authors_in_data)

    files = os.listdir('../homepage')

    pos_cnt, neg_cnt = 0, 0
    for filename in files:
        filename = filename.split('.')[0]
        if filename in authors_in_data:
            pos_cnt += 1
        else:
            neg_cnt += 1

    print pos_cnt, neg_cnt

def count_linkedin_overlap():
    authors_in_data = []
    for line in open('author_index.out'):
        authors_in_data.append(line.strip())
    authors_in_data = set(authors_in_data)

    authors_in_lk = json.load(open('../match_linkedin.json'))
    authors_in_lk = [e[1] for e in authors_in_lk]

    pos_cnt, neg_cnt = 0, 0
    for author in authors_in_lk:
        if author in authors_in_data:
            pos_cnt += 1
        else:
            neg_cnt += 1
    print pos_cnt, neg_cnt

def count_more_than_five():
    target_authors = []
    for filename in os.listdir('../homepage'):
        target_authors.append(filename.split('.')[0])
    target_authors = set(target_authors)

    cnt = 0
    for line in open('sample.pair.select.txt'):
        inputs = line.strip().split(';')
        if inputs[0] in target_authors and len(inputs) >= 6:
            cnt += 1
    print cnt

if __name__ == '__main__':
    # count_overlap()
    # count_more_than_five()
    count_linkedin_overlap()