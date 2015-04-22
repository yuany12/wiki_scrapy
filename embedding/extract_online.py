import extractor
import logging
import cPickle
import pymongo
import MySQLdb as mdb

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = '166.111.7.105', port = 30017)
    db = client.bigsci
    db.authenticate('keggger_bigsci', password)
    return db

def get_db(database):
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, database).cursor()

def extract_all():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    title_keywords = {}
    abs_keywords = {}
    ext = extractor.extractor(get_db('wikipedia'))

    mongodb = get_mongodb()
    pubs = mongodb.publication
    cnt, tot = 0, pubs.count()
    for doc in pubs.find():
        if cnt % 100 == 0:
            logging.info("loading %d/%d" % (cnt, tot))
        cnt += 1

        id, title, abs = str(doc['_id']), doc['title'], doc['abstract']

        if title != '':
            keywords = ext.extract_str(title)
            if len(keywords) > 0: title_keywords[id] = keywords

        if abs != '':
            keywords = ext.extract_str(abs)
            if len(keywords) > 0: abs_keywords[id] = keywords

    logging.info('dumping title_keywords')
    cPickle.dump(title_keywords, open('title_keywords.dump', 'wb'), protocol = 2)

    logging.info('dumping abs_keywords')
    cPickle.dump(abs_keywords, open('abs_keywords.dump', 'wb'), protocol = 2)

if __name__ == '__main__':
    extract_all()

