
import logging
import MySQLdb as mdb

def dump_wiki():
    password = open('password.txt').readline().strip()
    cur = mdb.connect('localhost', 'root', password, 'arnet_db').cursor()

    cur.execute("select page_title from page")
    fout = open('wiki_dump.txt', 'w')
    cnt, tot = 0, cur.rowcount
    for row in cur.fetchall():
        if cnt % 10000 == 0:
            logging.info('loading wikipedia %d/%d' % (cnt, tot))
        cnt += 1
        fout.write(row[0] + '\n')
    fout.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    dump_wiki()