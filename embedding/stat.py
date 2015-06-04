
import os

def count_overlap():
    authors_in_data = []
    for line in open('author_index.out'):
        authors_in_data.append(line.strip())
    authors_in_data = set(authors_in_data)

    files = os.listdir('.')

    print files[0]

    pos_cnt, neg_cnt = 0, 0
    for filename in files:
        if filename in authors_in_data:
            pos_cnt += 1
        else:
            neg_cnt += 1

    print pos_cnt, neg_cnt

if __name__ == '__main__':
    count_overlap()