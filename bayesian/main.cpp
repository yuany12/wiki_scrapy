
#include "data.hpp"
#include "model.hpp"

#include <utility>
#include <algorithm>

using namespace std;

bool comp(const pair<int, float> p1, const pair<int, float> p2) {
    return p1.second > p2.second;
}

int main() {
    int D, W;
    document * docs;
    float ** f_r, ** f_k;

    read_data(D, W, docs, f_r, f_k);

    model m(docs, D / 100, W, f_r, f_k);

    m.learn();

    FILE * fin = fopen("../embedding/keyword_index.out", "r");
    char ** keyword = new char * [W];
    for (int i = 0; i < W; i ++) {
        keyword[i] = new char[50];
        fscanf(fin, "%s", keyword[i]);
    }
    fclose(fin);

    char buffer[200];
    FILE * fout = fopen("model.result.prob.txt", "w");
    for (int i = 0; i < D / 100; i ++) {
        pair<int, float> * pairs = new pair<int, float>[m.M[i]];
        for (int j = 0; j < m.M[i]; j ++) {
            int w_id = docs[i].w_id[j];
            float prob = m.predict(i, w_id);
            pairs[j] = make_pair(j, prob);
        }
        fprintf(fout, "%d\n", m.y_d[i]);
        sort(pairs, pairs + m.M[i], comp);
        for (int j = 0; j < m.M[i]; j ++) {
            int w_id = docs[i].w_id[j];
            fprintf(fout, "%s,%f,%d\n", keyword[w_id], pairs[j].second, m.z_d_m[i][pairs[j].first]);
        }
        fprintf(fout, "##############\n");
        delete [] pairs;
    }
    fclose(fout);
}