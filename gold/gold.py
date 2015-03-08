from bs4 import BeautifulSoup
import urllib2
import nltk
import sys
import MySQLdb as mdb
import logging

MIN_N_GRAM = 2
MAX_N_GRAM = 3

def get_connection():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'wiki_entities')
    db.set_character_set('utf8')
    return db

def page_tokens(link):
    try:
        return nltk.word_tokenize(BeautifulSoup(urllib2.urlopen(link, timeout = 1).read()).get_text())
    except:
        logging.warning("time out %s" % link)
        return []

def extract_entities(tokens, cur):
    entities = set()
    print tokens
    for i in range(len(tokens)):
        for n in range(MAX_N_GRAM, MIN_N_GRAM - 1, -1):
            if i + n > len(tokens): break
            n_gram = " ".join(tokens[i: i + n])
            if n_gram in entities: break
            cur.execute("select * from page where title = %s", n_gram)
            if cur.rowcount > 0:
                row = cur.fetchone()[1]
                if not any(s[0].isupper() for s in row.split()[1:]): entities.add(row)
                break
    return entities

def print_page(link):
    entities = extract_entities(page_tokens(link), get_connection().cursor())
    for e in entities: print e

if __name__ == '__main__':
    if len(sys.argv) > 2:
        MIN_N_GRAM = int(sys.argv[2])
        MAX_N_GRAM = int(sys.argv[3])
    print_page(sys.argv[1])