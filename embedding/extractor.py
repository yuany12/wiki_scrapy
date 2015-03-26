from __future__ import unicode_literals
from spacy.en import English
import logging

class extractor:
    tagger = English()
    forbidden = {'PRP','PRP$','VBZ', '.', ':', '``', "''", 'DT'}

    def __init__(self, cur):
        cur.execute("select page_title from page where id < 10000")
        self.entities = []
        cnt, tot = 0, cur.rowcount
        for row in cur.fetchall():
            if cnt % 10000 == 0:
                logging.info('loading wikipedia %d/%d' % (cnt, tot))
            cnt += 1
            self.entities.append(row[0].lower())
        self.entities = set(self.entities)

    def pos_rule(self, tokens):
        tags = [e.tag_ for e in tokens]
        has_nns = False
        for e in tags:
            if e is None: return False
            if e in self.forbidden: return False
            if e.startswith('NN'): has_nns = True
        if not has_nns: return False
        if tags[0] == 'CD': return False
        return True

    def extract_str(self, s):
        tokens = self.tagger(s, tag = True, parse = False)
        i, ret = 0, []
        while i < len(tokens) - 1:
            if i + 2 < len(tokens) and self.pos_rule(tokens[i: i + 3]):
                word = "_".join(e.orth_.lower() for e in tokens[i: i + 3])
                if word in self.entities:
                    ret.append(word)
                    i += 3
                    continue
            if self.pos_rule(tokens[i: i + 2]):
                word = "_".join(e.orth_.lower() for e in tokens[i: i + 2])
                if word in self.entities:
                    ret.append(word)
                    i += 2
                    continue
            i += 1
        return ret