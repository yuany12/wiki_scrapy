
#include "data.hpp"
#include "model.hpp"

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

    model m(docs, D, W, f_r, f_k);

    // m.learn();

    FILE * fin;
    if (SMALL_DATA)
        fin = fopen("../embedding/keyword_index.out~", "r");
    else
        fin = fopen("../embedding/keyword_index.out", "r");

    char ** keyword = new char * [W];
    for (int i = 0; i < W; i ++) {
        keyword[i] = new char[50];
        fscanf(fin, "%s", keyword[i]);
    }
    fclose(fin);

    m.sample_topics();

    char buffer[200];
    FILE * fout;
    if (SMALL_DATA)
        fout = fopen("model.result.prob.txt~", "w");
    else
        fout = fopen("model.result.prob.txt", "w");

    for (int i = 0; i < D; i ++) {
        if (i % 10000 == 0) {
            sprintf(temp_, "predicting %d", i);
            logging(temp_);
        }

        pair<int, float> * pairs = new pair<int, float>[m.M[i]];
        for (int j = 0; j < m.M[i]; j ++) {
            int w_id = docs[i].w_id[j];
            float prob = m.predict(i, w_id);
            pairs[j] = make_pair(j, prob);
        }
        fprintf(fout, "%d\n", m.y_d[i]);
        sort(pairs, pairs + m.M[i], comp);
        for (int k = 0; k < m.M[i]; k ++) {
            int j = pairs[k].first;
            int w_id = docs[i].w_id[j];
            fprintf(fout, "%s,%f,%d\n", keyword[w_id], pairs[k].second, m.z_d_m[i][j]);
        }
        fprintf(fout, "##############\n");
        delete [] pairs;

        // fprintf(fout, "%d\n", m.y_d[i]);
        // for (int j = 0; j < m.M[i]; j ++) {
        //     int w_id = docs[i].w_id[j];
        //     fprintf(fout, "%s,%d\n", keyword[w_id], m.z_d_m[i][j]);
        // }
        // fprintf(fout, "#####\n");
    }
    fclose(fout);

    if (SMALL_DATA)
        fout = fopen("model.result.topics.txt~", "w");
    else
        fout = fopen("model.result.topics.txt", "w");
    for (int i = 0; i < m.T; i ++) {
        fprintf(fout, "###topic%d\n", i);
        for (int j = 0; j < D; j ++) {
            for (int k = 0; k < m.M[j]; k ++) {
                if (m.z_d_m[j][k] != i) continue;
                int w_id = docs[j].w_id[k];
                fprintf(fout, "%s\n", keyword[w_id]);
            }
        }
    }
    fclose(fout);

    m.save_model();
}
