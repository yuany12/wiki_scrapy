
def get_cursor():
    password = open('password.txt').readline().strip()
    return = mdb.connect('localhost', 'root', password, 'wikipedia').cursor()

def desym(infile, outfile, cur):
    appeared = set()
    fout = open(outfile, 'w')
    for line in open(infile):
        inputs = line.strip().split()
        words = []
        for word in inputs[2].split('|'):
            cur.execute("select page_id, page_isredirect from page where page_title = %s", word.capitalize())
            flag = True
            for row in cur.fetchall():
                if row[1] == 1:
                    cur.execute("select rd_title from redirect where rd_from = %s", row[0])
                    name = cur.fetchone()[0]
                    if name in appeared:
                        flag = False
                    else:
                        appeared.add(name)
                    break
            if flag:
                words.append(word)
        fout.write("\t".join(inputs[:2] + ["|".join(words)]) + '\n')
    fout.close()

if __name__ == '__main__':
    cur = get_cursor()
    for jconf in ['ASPLOS', 'SIGCOMM', 'CRYPTO', 'OSDI', 'STOC', 'SIGMOD Conference', 'KDD', 'SIGGRAPH', 'ICML', 'CHI']:
        desym('res_' + jconf + '.out', 'desym_' + jconf + '.out', cur)