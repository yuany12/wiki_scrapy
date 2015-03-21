import logging
import random
import MySQLdb as mdb

def get_cursor():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wikipedia').cursor()

def load_db(cur):
    cur.execute("select page_id, page_is_redirect, page_namespace, page_title from page")
    pages = {}
    tot = cur.rowcount
    for i in range(tot):
        row = cur.fetchone()
        if i % 10000 == 0:
            logging.info('loading %d/%d' % (i, tot))
        if row[2] != 0: continue
        if row[3].lower() in pages:
            words = row[3].split('_')
            if len(words) == 1: continue
            else:
                if words[1][0].isupper(): continue
        pages[row[3].lower()] = (row[0], row[1])
    return pages

def redirect(infile, outfile, cur, pages):
    fout = open(outfile, 'w')
    appeared = {}
    for line in open(infile):
        word = line.strip()
        if word not in pages: continue
        name = word
        if pages[word][1] == 1:
            cur.execute("select rd_title from redirect where rd_from = %s", pages[word][0])
            name = cur.fetchone()[0].lower()
        if name in appeared:
            if name == word:
                appeared[name] = name
        else:
            appeared[name] = word
    output = [v for _, v in appeared.iteritems()]
    random.shuffle(output)
    for e in output:
        fout.write(e + '\n')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = get_cursor()
    pages = load_db(cur)
    for jconf in ['ASPLOS', 'SIGCOMM', 'CRYPTO', 'OSDI', 'STOC', 'SIGMOD Conference', 'KDD', 'SIGGRAPH', 'ICML', 'CHI']:
        logging.info('processing %s' % jconf)
        redirect('tag_desym_' + jconf + '.out', 're_desym_' + jconf + '.out', cur, pages)
