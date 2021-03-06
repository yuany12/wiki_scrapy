import logging
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

def desym(infile, outfile, cur, pages):
    fout = open(outfile, 'w')
    for line in open(infile):
        appeared = set()
        inputs = line.strip().split('\t')
        if len(inputs) < 3: continue
        words = []
        for word in inputs[2].split('|'):
            if word not in pages: continue
            name = word
            if pages[word][1] == 1:
                cur.execute("select rd_title from redirect where rd_from = %s", pages[word][0])
                name = cur.fetchone()[0].lower()
            if name in appeared: continue
            appeared.add(name)
            words.append(word)
        fout.write("\t".join(inputs[:2] + ["|".join(words)]) + '\n')
    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = get_cursor()
    pages = load_db(cur)
    for jconf in ['ASPLOS', 'SIGCOMM', 'CRYPTO', 'OSDI', 'STOC', 'SIGMOD Conference', 'KDD', 'SIGGRAPH', 'ICML', 'CHI']:
        logging.info('processing %s' % jconf)
        desym('res_' + jconf + '.out', 'desym_' + jconf + '.out', cur, pages)