import MySQLdb as mdb
import collections

def count():
    cnt = collections.defaultdict(int)
    for line in open('page_links.dump'):
        for word in line.strip().split()[1].split(','): cnt[int(word)] += 1
    return sorted([(k, v) for k, v in cnt.iteritems()], key = lambda x: x[1], reverse = True)

def create_dict():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'wiki_entities')
    db.set_character_set('utf8')
    cur = db.cursor()
    cur.execute("select * from page")
    ret = {}
    for row in cur.fetchall():
        if not any(s[0].isupper() for s in row[1].split()[1:]):
            ret[row[0]] = row[1].lower()
    return ret

if __name__ == '__main__':
    cnt_list = count()
    entity_dict = create_dict()
    for e in cnt_list:
        print entity_dict[e[0]], e[1]