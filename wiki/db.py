import MySQLdb as mdb
import json
import logging

def get_connection():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wiki_entities')

def create_tables():
    con = get_connection()
    cur = con.cursor()
    cur.execute("drop table if exists cat2cat")
    cur.execute("drop table if exists cat2page")
    cur.execute("drop table if exists cat")
    cur.execute("drop table if exists page")
    cur.execute("create table cat (id int not null, \
        title varchar (63), \
        primary key (id))")
    cur.execute("create table page (id int not null, \
        title varchar (63), \
        primary key (id))")
    cur.execute("create table cat2cat (id int not null auto_increment, \
        parent_id int, \
        child_id int, \
        primary key (id), \
        foreign key (parent_id) references cat(id), \
        foreign key (child_id) references cat(id))")
    cur.execute("create table cat2page (id int not null auto_increment, \
        cat_id int, \
        page_id int, \
        primary key (id), \
        foreign key (cat_id) references cat(id), \
        foreign key (page_id) references page(id))")

def insert_contents():
    cats = json.load(open('out.json'))
    cat2ind, cat_cnt = {}, 0
    page2ind, page_cnt = {}, 0
    cur = get_connection().cursor()
    tt, ttt = 0, len(cats)
    for c in cats:
        if tt % 1000 == 0:
            logging.info("traverse categories %d/%d" % (tt, ttt))
        tt += 1
        cat = c['title']
        if cat not in cat2ind:
            cat2ind[cat] = cat_cnt
            cur.execute("insert into cat values (%(id)s, %(title)s)", {'id': cat_cnt, 'title': cat})
            cat_cnt += 1
        for subcat in c['subcats']:
            if subcat not in cat2ind:
                cat2ind[subcat] = cat_cnt
                cur.execute("insert into cat values (%(id)s, %(title)s)", {'id': cat_cnt, 'title': subcat})
                cat_cnt += 1
            cur.execute("insert into cat2cat (parent_id, child_id) values (%(parent_id)s, %(child_id)s)", {'parent_id': cat2ind[cat], 'child_id': cat2ind[subcat]})
        for page in c['pages']:
            if page not in page2ind:
                page2ind[page] = page_cnt
                cur.execute("insert into page values (%(id)s, %(title)s)", {'id': page_cnt, 'title': page})
                page_cnt += 1
            cur.execute("insert into cat2page (cid, pid) values (%(cid)s, %(pid)s)", {'cid': cat2ind[cat], 'pid': page2ind[page]})
        cur.commit()

def create_index():
    cur = get_connection().cursor()
    cur.execute("create index cat_title_index on cat (title)")
    cur.execute("create index page_title_index on page (title)")
    cur.execute("create index c1_index on cat2cat (parent_id)")
    cur.execute("create index c2_index on cat2cat (child_id)")
    cur.execute("create index c_index on cat2page (cat_id)")
    cur.execute("create index p_index on cat2page (page_id)")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    create_tables()
    insert_contents()