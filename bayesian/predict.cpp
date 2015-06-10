
#include "model.hpp"
#include "data.hpp"


#include <utility>
#include <algorithm>

using namespace std;

bool comp(const pair<int, float> p1, const pair<int, float> p2) {
    return p1.second > p2.second;
}

char temp_[50];

int main() {
    int D, W;
    document * docs;
    float ** f_r, ** f_k;

    read_data(D, W, docs, f_r, f_k);

    model m(docs, D, W, f_r, f_k, "model.save.txt.temp");

    FILE * fin = fopen("../embedding/keyword_index.out", "r");

    char ** keyword = new char * [W];
    for (int i = 0; i < W; i ++) {
        keyword[i] = new char[50];
        fscanf(fin, "%s", keyword[i]);
    }
    fclose(fin);

    fin = fopen("../embedding/author_index.out", "r");

    char ** author = new char * [D];
    for (int i = 0; i < D; i ++) {
        author[i] = new char[50];
        fscanf(fin, "%s", author[i]);
    }
    fclose(fin);

    FILE * fout = fopen("model.predict.txt.temp", "w");

    float ** prob = new float * [D];

    for (int i = 0; i < D; i ++) {
        prob[i] = new float[m.M[i]];
    }

    #pragma omp parallel for num_threads(64) schedule(dynamic, 1000)
    for (int i = 0; i < D; i ++) {
        if (i % 10000 == 0) {
            sprintf(temp_, "predicting %d", i);
            logging(temp_);
        }

        int M = m.M[i];
        for (int j = 0; j < M; j ++) {
            int w_id = docs[i].w_id[j];
            prob[i][j] = m.predict(i, w_id);
        }
    }

    for (int i = 0; i < D; i ++) {
        if (i % 10000 == 0) {
            sprintf(temp_, "printing %d", i);
            logging(temp_);
        }

        int M = m.M[i];

        pair<int, float> * pairs = new pair<int, float>[M];
        for (int j = 0; j < M; j ++) {
            pairs[j] = make_pair(j, prob[i][j]);
        }
        fprintf(fout, "%s %d %d\n", author[i], m.y_d[i], M);
        sort(pairs, pairs + M, comp);
        for (int k = 0; k < M; k ++) {
            int j = pairs[k].first;
            int w_id = docs[i].w_id[j];
            fprintf(fout, "%s,%f,%d\n", keyword[w_id], pairs[k].second, m.z_d_m[i][j]);
        }
        fprintf(fout, "##############\n");
        delete [] pairs;

        fprintf(fout, "#####\n");
    }
    fclose(fout);
}