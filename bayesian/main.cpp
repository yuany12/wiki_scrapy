
#include "data.hpp"
#include "model.hpp"

int main() {
    int D, W;
    document * docs;
    double ** f_r, ** f_k;

    printf("addr = %d\n", docs);

    read_data(D, W, docs, f_r, f_k);

    model m(docs, D, W, f_r, f_k);

    printf("init done\n");

    m.learn();
}