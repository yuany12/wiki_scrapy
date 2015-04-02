import extractor
import logging
import cPickle
import MySQLdb as mdb

def get_db(database):
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, database).cursor()

def extract_all():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    title_keywords = {}
    abs_keywords = {}
    ext = extractor.extractor(get_db('wikipedia'))

    cur.execute("select id, title from publication limit 1000")
    cnt, tot = 0, cur.rowcount
    for id, title in cur.fetchall():
        if cnt % 100 == 0:
            logging.info("loading %d/%d" % (cnt, tot))
        cnt += 1

        keywords = ext.extract_str(title)
        if len(keywords) > 0: title_keywords[id] = keywords

        cur.execute("select abstract from publication_ext")
        abs = cur.fetchone()
        if abs is not None:
            abs = abs[0]
            keywords = ext.extract_str(abs)
            if len(keywords) > 0: title_keywords[id] = keywords

    logging.info('dumping title_keywords')
    cPickle.dump(title_keywords, open('title_keywords.dump', 'wb'))

    logging.info('dumping abs_keywords')
    cPickle.dump(abs_keywords, open('abs_keywords.dump', 'wb'))

if __name__ == '__main__':
    extract_all()

