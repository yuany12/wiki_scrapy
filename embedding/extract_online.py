import extractor
import logging
import cPickle
import pymongo
import multiprocessing
# import MySQLdb as mdb

def get_mongodb():
    password = open('password_mongo.txt').readline().strip()
    client = pymongo.MongoClient(host = 'localhost', port = 30019)
    db = client.bigsci
    db.authenticate('kegger_bigsci', password)
    return db

def extract_all(bulk_info = (80000000, 0)):
    bulk_size, bulk_no = bulk_info
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # ext = extractor.extractor(get_db('wikipedia'))
    ext = extractor.extractor('wiki_dump.txt', db = False)

    mongodb = get_mongodb()
    pubs = mongodb.publication_dupl
    word_colls = mongodb.keywords
    cnt, tot = 0, pubs.count()
    for doc in pubs.find(skip = bulk_size * bulk_no, limit = bulk_size):
        if cnt % 100 == 0 and bulk_no == 0:
            logging.info("loading title %d/%d" % (cnt, tot))
            # logging.info("loading abstract %d/%d" % (cnt, tot))
        cnt += 1

        if 'lang' in doc and doc['lang'] == 'zh': continue

        title = doc['title'] if 'title' in doc else ''
        # abs = doc['abstract'] if 'abstract' in doc else ''

        title_keywords = ext.extract_str(title)
        # abstract_keywords = ext.extract_str(abs)

        word_colls.update_one({'_id': doc['_id']}, {'$set': {'title_keywords': title_keywords}}, upsert = True)
        # pubs.update_one({'_id': doc['_id']}, {'$set': {'abstract_keywords': abstract_keywords}})

    # logging.info('dumping title_keywords')
    # cPickle.dump(title_keywords, open('title_keywords.dump', 'wb'), protocol = 2)

    # logging.info('dumping abs_keywords')
    # cPickle.dump(abs_keywords, open('abs_keywords.dump', 'wb'), protocol = 2)

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes = 4)
    pool.map(extract_all, [(15070000, i) for i in range(4)])
    # extract_all()
