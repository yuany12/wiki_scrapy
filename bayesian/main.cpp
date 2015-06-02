
#include "data.hpp"
#include "model.hpp"

int main() {
    int D, W;
    document * docs;
    float ** f_r, ** f_k;

    read_data(D, W, docs, f_r, f_k);

    model m(docs, D, W, f_r, f_k);

    m.learn();
}