# -*- coding: utf-8 -*-

import MySQLdb as mdb
import nltk
import sys
import collections

MAX_N_GRAM, MIN_N_GRAM = 3, 2

def connect_arnet():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def connect_wiki():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wiki_entities')

def get_text(author_id):
    cur = connect_arnet().cursor()
    cur.execute("select pid from na_author2pub where aid = %s", author_id)
    rows = cur.fetchall()
    free_text = ""
    for row in rows:
        cur.execute("select title from publication where id = %s", row[0])
        if cur.rowcount > 0:
            free_text += ' ' + cur.fetchone()[0]
            cur.execute("select abstract from publication_ext where id = %s", row[0])
            tmp_text = cur.fetchone()[0] if cur.rowcount > 0 else ''
            if tmp_text is not None and tmp_text != '': free_text += ' ' + tmp_text
    return nltk.word_tokenize(free_text)

def extract_terms(tokens, entity_dict):
    entities = collections.defaultdict(int)
    for i in range(len(tokens)):
        for n in range(MAX_N_GRAM, MIN_N_GRAM - 1, -1):
            if i + n > len(tokens): break
            n_gram = " ".join(tokens[i: i + n]).lower()
            if n_gram in entity_dict:
                entities[n_gram] += 1
    return sorted([(k, v) for k, v in entities.iteritems()], key = lambda x: x[1], reverse = True)

def create_dict():
    cur = connect_wiki().cursor()
    cur.execute("select * from page")
    ret = {}
    for row in cur.fetchall():
        if not any(s[0].isupper() for s in row[1].split()[1:]):
            ret[row[1].lower()] = row[0]
    return ret

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    entity_dict = create_dict()
    print extract_terms(get_text(int(sys.argv[1])), entity_dict)