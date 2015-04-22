import extractor
import logging
import cPickle
import pymongo
import MySQLdb as mdb

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30019)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
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

        id = str(doc['_id'])
        title = doc['title'] if 'title' in doc else ''
        abs = doc['abstract'] if 'abstract' in doc else ''

        title_keywords = ext.extract_str(title)
        abstract_keywords = ext.extract_str(abs)

        pubs.update_one({'_id': doc['_id']}, {'$set': {'title_keywords': title_keywords,\
         'abstract_keywords': abstract_keywords}})

    # logging.info('dumping title_keywords')
    # cPickle.dump(title_keywords, open('title_keywords.dump', 'wb'), protocol = 2)

    # logging.info('dumping abs_keywords')
    # cPickle.dump(abs_keywords, open('abs_keywords.dump', 'wb'), protocol = 2)

if __name__ == '__main__':
    extract_all()

