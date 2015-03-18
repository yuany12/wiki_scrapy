import logging
import MySQLdb as mdb

def get_cursor():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wikipedia').cursor()

def desym(infile, outfile, cur):
    fout = open(outfile, 'w')
    for line in open(infile):
        appeared = set()
        inputs = line.strip().split('\t')
        if len(inputs) < 3: continue
        words = []
        for word in inputs[2].split('|'):
            cur.execute("select page_id, page_is_redirect, page_namespace from page where page_title = %s", word.capitalize())
            name = word
            for row in cur.fetchall():
                if row[1] == 1 and row[2] == 0:
                    redirect = True
                    cur.execute("select rd_title from redirect where rd_from = %s", row[0])
                    name = cur.fetchone()[0].lower()
                    break
            if name in appeared: continue
            appeared.add(name)
            words.append(word)
        fout.write("\t".join(inputs[:2] + ["|".join(words)]) + '\n')
    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = get_cursor()
    for jconf in ['ASPLOS', 'SIGCOMM', 'CRYPTO', 'OSDI', 'STOC', 'SIGMOD Conference', 'KDD', 'SIGGRAPH', 'ICML', 'CHI']:
        logging.info('processing %s' % jconf)
        desym('res_' + jconf + '.out', 'desym_' + jconf + '.out', cur)