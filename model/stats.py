import MySQLdb as mdb
import collections

def connect_arnet():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'arnet_db')

def count():
    cur = connect_arnet().cursor()
    cur.execute("select tag, cnt from wiki_tag")
    tag2cnt = collections.defaultdict(int)
    for row in cur.fetchall():
        tag2cnt[row[0]] += row[1]
    cnt2cnt = collections.defaultdict(int)
    for _, v in tag2cnt.iteritems():
        cnt2cnt[v] += 1
    for k, v in cnt2cnt.iteritems():
        print k, v

if __name__ == '__main__':
    count()