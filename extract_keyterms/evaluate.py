import MySQLdb as mdb
import logging

def get_cursor():
    password = open('password.txt').readline().strip()
    return mdb.connect('localhost', 'root', password, 'wikipedia').cursor()

def load_db(cur):
    cur.execute("select page_id, page_is_redirect, page_namespace, page_title from page where page_id < 10000")
    pages = {}
    tot = cur.rowcount
    for i in range(tot):
        row = cur.fetchone()
        if i % 10000 == 0:
            logging.info('loading %d/%d' % (i, tot))
        if row[2] != 0: continue
        if row[3].lower() in pages:
            words = row[3].split('_')
            if len(words) == 1: continue
            else:
                if words[1][0].isupper(): continue
        pages[row[3].lower()] = (row[0], row[1])
    return pages

def evaluate(py, y):
    tp = sum([1 if e in y else 0 for e in py])
    fp = len(py) - tp
    fn = len(y) - tp
    return tp, fp, fn

def redirect(words, pages, cur):
    ret = []
    for word in words:
        if word in pages and pages[word][1] == 1:
            cur.execute("select rd_title from redirect where rd_from = %s", pages[word][0])
            word = cur.fetchone()[0]
        ret.append(word)
    return set(ret)

def read_from_person(infile):
    ret = []
    for line in open(infile):
        ret.append(int(line.strip()))
    return ret

def read_from_label(infile, pages, cur):
    ret = []
    for line in open(infile):
        inputs = line.strip().split(',')
        if inputs[0] == '1': ret.append(inputs[1])
    return redirect(ret, pages, cur)

def read_from_keyterms(infile, pages, cur, gold):
    ret, gold_ret = {}, {}
    for line in open(infile):
        inputs = line.strip().split('\t')
        ret[int(inputs[0])] = redirect(inputs[2].split('|'), pages, cur)
        gold_ret[int(inputs[0])] = ret[int(inputs[0])].intersection(gold)
    return ret, gold_ret

def read_from_extractor(infile, pages, cur, gold):
    ret = {}
    for line in open(infile):
        inputs = line.strip().split('\t')
        ret[int(inputs[0])] = redirect([e.replace(' ', '_') for e in inputs[2].split(',')], pages, cur)
    return ret

def evaluate_keyterm_baseline(pages, cur, jconfs):
    tp, fp, fn = 0, 0, 0
    for jconf in jconfs:
        persons = read_from_person('person_desym_' + jconf + '.out')
        gold = read_from_label('re_desym_' + jconf + '.out.csv', pages, cur)
        keyterms, goldterms = read_from_keyterms('desym_' + jconf + '.out', pages, cur, gold)
        for person in persons:
            ctp, cfp, cfn = evaluate(keyterms[person], goldterms[person])
            tp, fp, fn = tp + ctp, fp + cfp, fn + cfn
    return tp, fp, fn

def evaluate_extractor_baseline(pages, cur, jconfs):
    tp, fp, fn = 0, 0, 0
    for jconf in jconfs:
        persons = read_from_person('person_desym_' + jconf + '.out')
        gold = read_from_label('re_desym_' + jconf + '.out.csv', pages, cur)
        keyterms = read_from_extractor('ext_terms/res_' + jconf + '.out', pages, cur, gold)
        _, goldterms = read_from_keyterms('desym_' + jconf + '.out', pages, cur, gold)
        for person in persons:
            ctp, cfp, cfn = evaluate(keyterms[person], keyterms[person])
            tp, fp, fn = tp + ctp, fp + cfp, fn + cfn
    return tp, fp, fn

def report(name, tp, fp, fn):
    precision = float(tp) / (tp + fp) if tp + fp > 0 else 0.0
    recall = float(tp) / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    print 'evaluating %s: %f, %f, %f' % (name, precision, recall, f1)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cur = get_cursor()
    pages = load_db(cur)
    jconfs = ['KDD', 'ICML']
    report('keyterm', evaluate_keyterm_baseline(pages, cur, jconfs))
    report('extractor', evaluate_extractor_baseline(pages, cur, jconfs))
