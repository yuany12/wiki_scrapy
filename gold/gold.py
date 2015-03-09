from bs4 import BeautifulSoup
import urllib2
import requests
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
        #return nltk.word_tokenize(BeautifulSoup(urllib2.urlopen(link, timeout = 1).read()).get_text())
        return nltk.word_tokenize(BeautifulSoup(requests.get(link, timeout = 1, proxies = {'http': '104.236.43.250:50080'}).text).get_text())
    except urllib2.HTTPError, e:
        logging.error(e.code)
        return []
    except Exception, detail:
        logging.error(detail)
        return []
    return []

def extract_entities(tokens, entity_dict):
    entities, ids = set(), set()
    for i in range(len(tokens)):
        for n in range(MAX_N_GRAM, MIN_N_GRAM - 1, -1):
            if i + n > len(tokens): break
            n_gram = " ".join(tokens[i: i + n]).lower()
            if n_gram in entities: break
            if n_gram in entity_dict:
                entities.add(n_gram)
                ids.add(entity_dict[n_gram])
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

def create_dict(cur):
    cur.execute("select * from page")
    ret = {}
    i, tot = 0, cur.rowcount
    for row in cur.fetchall():
        if i % 10000 == 0:
            logging.info("Creating dictionary %d/%d" % (i, tot))
        i += 1
        if not any(s[0].isupper() for s in row[1].split()[1:]):
            ret[row[1].lower()] = row[0]
    return ret

def set_proxy():
    proxy = urllib2.ProxyHandler({'http': '104.236.43.250:50080'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)

def link_pages():
    db = connect_arnet()
    cur = db.cursor()
    create_table(cur)
    cur.execute("select id, homepage from contact_info where homepage <> %s", "")
    wiki_cur = get_connection().cursor()
    entity_dict = create_dict(wiki_cur)
    i, tot, inv = 0, cur.rowcount, 0
    for row in cur.fetchall():
        if i % 100 == 0:
            logging.info("Processing %d/%d; invalid %d" % (i, tot, inv))
        i += 1
        entity_ids = extract_entities(page_tokens(row[1]), entity_dict)
        if len(entity_ids) == 0: inv += 1
        for entity_id in entity_ids:
            cur.execute("insert into entities (author_id, page_id) values (%(author_id)s, %(page_id)s)", {'author_id': row[0], 'page_id': entity_id})
        db.commit()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    if len(sys.argv) > 2:
        MIN_N_GRAM = int(sys.argv[2])
        MAX_N_GRAM = int(sys.argv[3])
    link_pages()