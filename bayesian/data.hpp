#pragma once

#include <cstdio>
#include "model.hpp"

using namespace std;

void read_data(int & D, int & W, document * docs, double ** f_r, double ** f_k) {
    FILE * fin = fopen("data.main.txt", "r");
    fscanf(fin, "%d %d\n", &D, &W);

    docs = new document[D];

    for (int i = 0; i < D; i ++) {
        int r_id, w_cnt;
        fscanf(fin, "%d %d\n", &r_id, &w_cnt);
        docs[i].r_id = r_id;
        docs[i].w_cnt = w_cnt;
        docs[i].w_id = new int[w_cnt];
        docs[i].w_freq = new int[w_cnt];

        for (int j = 0; j < w_cnt; j ++) {
            fscanf(fin, "%d %d\n", &(docs[i].w_id[j]), &(docs[i].w_freq[j]));
        }
    }

    fclose(fin);

    printf("loading data main done\n");

    fin = fopen("data.embedding.researcher.txt", "r");
    f_r = new double*[D];
    for (int i = 0; i < D; i ++) {
        f_r[i] = new double[model::E_r];
    }
    for (int i = 0; i < D; i ++) {
        for (int j = 0; j < model::E_r; j ++)
            fscanf(fin, "%lf\n", &f_r[i][j]);
    }
    fclose(fin);

    printf("loading researcher done\n");

    fin = fopen("data.embedding.keyword.txt", "r");
    f_k = new double*[W];
    for (int i = 0; i < W; i ++) {
        f_k[i] = new double[model::E_k];
    }
    for (int i = 0; i < W; i ++) {
        for (int j = 0; j < model::E_k; j ++)
            fscanf(fin, "%lf\n", &f_k[i][j]);
    }
    fclose(fin);

    printf("loading keyword done\n");
}