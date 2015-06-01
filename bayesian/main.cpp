
#include "data.hpp"
#include "model.hpp"

int main() {
    int D, W;
    document * docs;
    double ** f_r, ** f_k;

    read_data(D, W, docs, f_r, f_k);

    printf("add = %d\n", docs);

    model m(docs, D, W, f_r, f_k);

    printf("init done\n");

    m.learn();
}