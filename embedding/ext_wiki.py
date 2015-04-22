import pickle
import MySQLdb
import re
import itertools
import collections
import time
import os
from spacy.en import English

conn = MySQLdb.connect('127.0.0.1','root', 'keg2012', 'arnet_db')
cursor = conn.cursor()

titles = None
def load_title():
    global titles
    titles = {}
    with open("./page_titles") as f:
        cur_line = 0
        for line in f:
            cur_line += 1
            #if cur_line==1000000:
            #    break
            arg = line.strip().split('\t')
            t_ori = arg[2]
            t_std = t_ori.lower()
            titles[t_std] = t_ori
    for x in titles:
        print x, titles[x]
        break
    return titles
def load_from_pkl():
    f = open('titles_pkl','r')
    titles = pickle.load(f)
    f.close()
    return titles

print "Loading"
titles = load_title()
#titles = load_from_pkl()
print "Loaded"
#output = open('titles_pkl', 'w')
#pickle.dump(titles, output)
#output.close()

pat = re.compile(r'[., ?!+_><;"~*&^%]+')
def is_NN(p):
    return p.startswith("NN")
def is_punct(p):
    return p in {'.', ':', '``', "''"}

forbidden = {'PRP','PRP$','VBZ', '.', ':', '``', "''", 'DT'}
def pos_rule_double(p1, p2):
    if p1 is None or p2 is None:
        return False
    if p1 in forbidden or p2 in forbidden:
        return False
    if not is_NN(p1) and not is_NN(p2):
        return False
    if p1=='CD':
        return False
    return True

def pos_rule(p1, p2, p3=None):
    if p3 is None:
        return pos_rule_double(p1, p2)
    if p1 is None or p2 is None:
        return False
    if p1 in forbidden or p2 in forbidden or p3 in forbidden:
        return False
    if not is_NN(p1) and not is_NN(p2) and not is_NN(p3):
        return False
    if p1=='CD':
        return False
    return True


tagger = English()
def extract_str(s):
    global titles
    #words = [ w for w in pat.split(s) if w!='']
    try:
        s = s.strip().lower().decode('utf8')
        tagged = tagger(s, tag=True, parse=False)
    except Exception:
        return []
    res = []
    if len(tagged)>=3:
        it_fir_w = iter(tagged)
        it_sec_w = iter(tagged)
        it_sec_w.next()
        it_thr_w = iter(tagged)
        it_thr_w.next()
        it_thr_w.next()

        for fir_w, sec_w, thr_w in itertools.izip(it_fir_w, it_sec_w, it_thr_w):
            if pos_rule(fir_w.tag_, sec_w.tag_, thr_w.tag_):
                tag_raw = fir_w.orth_+u'_'+sec_w.orth_+u'_'+thr_w.orth_
                tag_raw = tag_raw.encode('utf8')
                if tag_raw in titles:
                    res.append(titles[tag_raw])
                    continue
            if pos_rule(fir_w.tag_, sec_w.tag_):
                tag_raw = fir_w.orth_+u'_'+sec_w.orth_
                tag_raw = tag_raw.encode('utf8')
                if tag_raw in titles:
                    res.append(titles[tag_raw])

    return res
def extract_para(s):
    res = []
    sens = s.split('.')
    for w in sens:
        w = w.strip()
        if len(w)>2:
            res.extend(extract_str(w))
    return res

time_per_pub = 0
n_pub = 0

#def pull_person_pub(pid):
#    cursor.execute("select pid from na_author2pub where aid=%d" % pid)

def extract_person(pid):
    global time_per_pub
    global n_pub
    cursor.execute("""Select publication.title, publication_ext.abstract from na_author2pub
                inner join publication on publication.id = na_author2pub.pid
                inner join publication_ext on publication.id=publication_ext.id
                where na_author2pub.aid=%d
                """% pid)
    res = collections.Counter()
    for x in cursor.fetchall():
        extracted = []
        if x[0] is not None:
            st_time = time.time()
            extracted.extend(extract_str(x[0]))
            time_per_pub += time.time()-st_time
            n_pub+=1
        """
        if x[1] is not None:
            st_time = time.time()
            extracted.extend(extract_str(x[1]))
            time_per_pub += time.time()-st_time
            n_pub+=1
        """
        #print extracted
        for w in extracted:
            w = w.lower().strip()
            res[w] += 1
    return res

def extract_file(fname):
    fin = open("./author/%s"% fname, "r")
    fout = open("res_wiki_titleonly/res_%s" % fname, "w")
    for line in fin:
        print line,
        arg = line.strip().split('\t')
        pid = int(arg[0])
        name = arg[2]
        res = extract_person(pid)
        res_sorted = sorted([w for w in res], key=lambda w:-res[w])
        fout.write(str(pid)+"\t")
        fout.write(name+"\t")
        output = "|".join(res_sorted)
        fout.write(output+"\n")

    fout.close()
    fin.close()

def extract_full():
    global time_per_pub
    global n_pub
    log_file = open("log",'w')
    for fname in os.listdir("author"):
        if fname[0]=='.':
            continue
        if "KDD" not in fname and "ICML" not in fname:
            continue
        print "FILE:"+fname
        time_per_pub = 0
        n_pub = 0
        st_time = time.time()
        extract_file(fname)
        ed_time = time.time()
        log_file.write("Used "+str((ed_time-st_time)/60)+ " minutes\n")
        log_file.write("average per pub:" + str(time_per_pub/n_pub) +" seconds\n")
    log_file.close()

def extract_full_db():
    all_cursor = conn.cursor()
    all_cursor.execute("select id,names from na_person")
    ins_cursor = conn.cursor()
    for aid_list in all_cursor.fetchall():
        print aid_list[0], aid_list[1]
        try:
            res = extract_person(aid_list[0])
            res_sorted = sorted([(w, res[w]) for w in res], key=lambda w:-res[w])
            for tag,cnt in res_sorted:
                ins_cursor.execute("insert into wiki_tag (aid, tag, cnt) values (%d,'%s',%d )" % (aid_list[0], tag, cnt))
            conn.commit()
        except Exception,e:
            print e
    ins_cursor.close()
    all_cursor.close()

#extract_full()
#extract_person(232288)
extract_full_db()

cursor.close()
conn.close()
