fout = open('proxy_list.txt', 'w')
cnt, prev = 0, ''
for line in open('raw_ips.txt'):
    cnt += 1
    inputs = line.strip().split()
    if cnt % 2 == 1:
        s = 1 if '.' in inputs[1] else 2
        prev = inputs[s] + ':' + inputs[s + 1]
    else:
        if inputs[0] == 'HTTP':
            fout.write('http://' + prev + '\n')
fout.close()