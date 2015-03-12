import MySQLdb as mdb

def get_connection():
    password = open('password.txt').readline().strip()
    db = mdb.connect('localhost', 'root', password, 'wiki_entities')
    db.set_character_set('utf8')
    return db

def create_tables():
    cur = get_connection().cursor()
    cur.execute("drop table if exists con2page")
    cur.execute("create table con2page (id int not null auto_increment, \
        contact_id int, \
        page_id int, \
        primary key (id)")

def insert_contents():
    db = get_connection()
    cur = db.cursor()
    for line in open('page_links.dump'):
        inputs = line.strip().split()
        contact_id = int(inputs[0])
        for e in inputs[1].split(','):
            cur.execute("insert into con2page (contact_id, page_id) values (%(contact_id)s, %(page_id)s)", {'contact_id': contact_id, 'page_id': int(e)})
    db.commit()

if __name__ == '__main__':
    create_tables()
    insert_contents()