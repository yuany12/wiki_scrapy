import MySQLdb as mdb
import json
import logging
import sys
import copy

def get_connection():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'wiki_entities')
    db.set_character_set('utf8')
    return db

def create_tables():
    con = get_connection()
    cur = con.cursor()
    cur.execute("drop table if exists cat2cat")
    cur.execute("drop table if exists cat2page")
    cur.execute("drop table if exists cat")
    cur.execute("drop table if exists page")
    cur.execute("create table cat (id int not null, \
        title varchar (255), \
        primary key (id))")
    cur.execute("create table page (id int not null, \
        title varchar (255), \
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
    db = get_connection()
    cur = db.cursor()
    tt, ttt = 0, len(cats)
    cur.execute('set names utf8')
    cur.execute('set character set utf8')
    cur.execute('set character_set_connection = utf8')
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
            cur.execute("insert into cat2page (cat_id, page_id) values (%(cat_id)s, %(page_id)s)", {'cat_id': cat2ind[cat], 'page_id': page2ind[page]})
        db.commit()

def create_index():
    cur = get_connection().cursor()
    cur.execute("create index cat_title_index on cat (title)")
    cur.execute("create index page_title_index on page (title)")
    cur.execute("create index c1_index on cat2cat (parent_id)")
    cur.execute("create index c2_index on cat2cat (child_id)")
    cur.execute("create index c_index on cat2page (cat_id)")
    cur.execute("create index p_index on cat2page (page_id)")

def cat_dfs(id, cur, s, visited):
    cur.execute("select title from cat where id = %s", id)
    title = cur.fetchone()[0]
    if title in visited: return
    s += "Category: " + title + " | "
    visited.add(title)
    cur.execute("select parent_id from cat2cat where child_id = %s", id)
    if cur.rowcount == 0:
        print s
    else:
        cat_dfs(cur.fetchone()[0], cur, s, visited)

def page_dfs(id, cur, s):
    cur.execute("select title from page where id = %s", id)
    s += "Page: " + cur.fetchone()[0] + " | "
    cur.execute("select cat_id from cat2page where page_id = %s", id)
    cat_dfs(cur.fetchone()[0], cur, s, set())

def search(query):
    cur = get_connection().cursor()
    cur.execute("select id from page where title = %s", "%%" + query "%%")
    if cur.rowcount > 0:
        page_dfs(cur.fetchone()[0], cur, "")
    else:
        cur.execute("select id from cat where title = %s", "%%" + query + "%%")
        if cur.rowcount > 0:
            cat_dfs(cur.fetchone()[0], cur, "", set())

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    search(sys.argv[1])