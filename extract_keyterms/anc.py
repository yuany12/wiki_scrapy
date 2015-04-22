
import logging
import MySQLdb as mdb

def get_cursor():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wikipedia').cursor()

def load_db(cur):
    cur.execute("select page_id, page_is_redirect, page_namespace, page_title from page")
    pages, cats = {}, {}
    tot = cur.rowcount
    for i in range(tot):
        row = cur.fetchone()
        if i % 10000 == 0:
            logging.info('loading %d/%d' % (i, tot))
        if row[2] == 0: pages[row[3].lower()] = (row[0], row[1])
        elif row[2] == 14: cats[row[3].lower()] = row[0]
    return pages, cats

def anc(infile, outfile, cur, pages, cats):
    fout = open(outfile, 'w')
    for line in open(infile):
        inputs = line.strip().split('\t')
        words = []
        for word in inputs[2].strip().split('|'):
            if word not in pages: continue
            name = word
            if pages[word][1] == 1:
                cur.execute("select rd_title from redirect where id_from = %s", pages[word][0])
                name = cur.fetchone()[0].lower()
            words.append(name)
        appeared = set(words)
        for word in words:
            