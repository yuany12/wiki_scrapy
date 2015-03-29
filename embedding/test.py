import gensim

def test():
    model = gensim.models.Word2Vec.load('author_word.model')
    for word in ['machine_learning', 'data_mining', 'deep_learning', 'social_network', 'support_vector_machine', 'neural_network']:
        for e in model.most_similar(positive = [word], negative = [], topn = 10):
            print word, e

if __name__ == '__main__':
    test()