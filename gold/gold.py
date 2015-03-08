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

def connect_arnet():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def page_tokens(link):
    try:
        return nltk.word_tokenize(BeautifulSoup(urllib2.urlopen(link, timeout = 1).read()).get_text())
    except:
        logging.warning("time out %s" % link)
        return []

def extract_entities(tokens, cur):
    entities, ids = set(), set()
    for i in range(len(tokens)):
        for n in range(MAX_N_GRAM, MIN_N_GRAM - 1, -1):
            if i + n > len(tokens): break
            n_gram = " ".join(tokens[i: i + n])
            if n_gram in entities: break
            cur.execute("select * from page where title = %s", n_gram)
            if cur.rowcount > 0:
                row = cur.fetchone()
                if not any(s[0].isupper() for s in row[1].split()[1:]):
                    entities.add(row[1])
                    ids.add(row[0])
                break
    return ids

def print_page(link):
    print extract_entities(page_tokens(link), get_connection().cursor())

def create_table(cur):
    cur.execute("drop table if exists entities")
    cur.execute("create table entities (id int not null auto_increment, \
        author_id int, \
        page_id int, \
        primary key (id))")

def link_pages():
    db = connect_arnet()
    cur = db.cursor()
    create_table(cur)
    cur.execute("select id, homepage from contact_info")
    wiki_cur = get_connection().cursor()
    i, tot = 0, cur.rowcount
    for row in cur.fetchall():
        if i % 100 == 0:
            logging.info("Processing %d/%d" % (i, tot))
        i += 1
        if row[1] is None or row[1] == '': continue
        for entity_id in extract_entities(page_tokens(row[1]), wiki_cur):
            cur.execute("insert into entities (author_id, page_id) values (%(author_id)s, %(page_id)s)", {'author_id': row[0], 'page_id': entity_id})
        db.commit()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    if len(sys.argv) > 2:
        MIN_N_GRAM = int(sys.argv[2])
        MAX_N_GRAM = int(sys.argv[3])
    link_pages()