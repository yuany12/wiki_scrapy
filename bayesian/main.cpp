
#include "data.hpp"
#include "model.hpp"

int main() {
    int D, W;
    document * docs;
    double ** f_r, ** f_k;

    read_data(D, W, docs, f_r, f_k);

    printf("D = %d\n", D);
    for (int i = 0; i < D; i ++) {
        printf("i = %d\n", i);
        int x = docs[i].w_cnt;
    }
    printf("check done\n");

    model m(docs, D, W, f_r, f_k);

    printf("init done\n");

    m.learn();
}