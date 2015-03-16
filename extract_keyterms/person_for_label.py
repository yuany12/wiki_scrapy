import MySQLdb as mdb
import collections
import logging

def arnet_db():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'arnet_db')
    db.set_character_set('utf8')
    return db

def jconfs_list(cur):
    ret = []
    for jconf in ['ASPLOS', 'SIGCOMM', 'CRYPTO', 'OSDI', 'STOC', 'SIGMOD Conference', 'KDD', 'SIGGRAPH', 'ICML', 'CHI']:
        cur.execute("select id from jconf where name = %s", jconf)
        ret.append((cur.fetchone()[0], jconf))
    return ret

def paper_list(cur, jconf_id):
    ret = []
    cur.execute("select id from publication where jconf = %s", jconf_id)
    for row in cur.fetchall():
        ret.append(row[0])
    return ret

def author_list(cur, paper_ids):
    author2cnt = collections.defaultdict(int)
    for paper_id in paper_ids:
        cur.execute("select aid from na_author2pub where pid = %s", paper_id)
        for row in cur.fetchall():
            author2cnt[row[0]] += 1
    return sorted([(k, v) for k, v in author2cnt.iteritems()], key = lambda x: x[1], reverse = True)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = arnet_db().cursor()
    for jconf_id, jconf in jconfs_list(cur):
        logging.info('extracting %s' % jconf)
        fout = open(jconf + '.out', 'w')
        for aid, cnt in author_list(cur, paper_list(cur, jconf_id)):
            cur.execute("select names from na_person where id = %s", aid)
            names = cur.fetchone()[0]
            fout.write(str(aid) + '\t' + str(cnt) + '\t' + names + '\n')
        fout.close()