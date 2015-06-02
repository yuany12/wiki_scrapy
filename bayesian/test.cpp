
#include "utils.hpp"
#include <iostream>
#include <cmath>

using namespace std;

void test(double a, double b) {
    cout << fast_pow(a, b) << ' ' << pow(a, b) << endl;
}

int main() {
    test(2.0, 2.0);
    test(2.0, 5.0);
    test(2.0, 10.0);
    test(20.0, 2.0);
    test(20.0, 4.0);
    test(20.0, 4.5);
    test(30.0, 10.0);
    test(100.0, 3.0);
}