# -*- coding: utf-8 -*-

import MySQLdb as mdb
import nltk
import sys
import collections

MAX_N_GRAM, MIN_N_GRAM = 3, 2
NCITATION = False

def connect_arnet():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def connect_wiki():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'wiki_entities')
    db.set_character_set('utf8')
    return db

def extract_terms(author_id, entity_dict):
    cur = connect_arnet().cursor()
    cur.execute('set names utf8')
    cur.execute('set character set utf8')
    cur.execute('set character_set_connection = utf8')
    cur.execute("select pid from na_author2pub where aid = %s", author_id)
    rows = cur.fetchall()
    entities = collections.defaultdict(int)
    for row in rows:
        cur.execute("select title, ncitation from publication where id = %s", row[0])
        if cur.rowcount > 0:
            t_row = cur.fetchone()
            free_text = t_row[0]
            ncitation = t_row[1]
            if ncitation > 0 or not NCITATION:
                #cur.execute("select abstract from publication_ext where id = %s", row[0])
                #tmp_text = cur.fetchone()[0] if cur.rowcount > 0 else ''
                #if tmp_text is not None and tmp_text != '': free_text += ' ' + tmp_text
                tokens = nltk.word_tokenize(free_text)
                for i in range(len(tokens)):
                    for n in range(MAX_N_GRAM, MIN_N_GRAM - 1, -1):
                        if i + n > len(tokens): break
                        n_gram = " ".join(tokens[i: i + n]).lower()
                        if n_gram in entity_dict:
                            entities[n_gram] += ncitation if NCITATION else 1
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
    if sys.argv[2].startswith('c'): NCITATION = True
    entity_dict = create_dict()
    for e in extract_terms(int(sys.argv[1]), entity_dict):
        print e[0], e[1]