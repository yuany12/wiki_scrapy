#pragma once

#include <iostream>
#include <iomanip>
#include <ctime>
#include <cstring>

using namespace std;

inline void logging(const char* s) {
    auto t = time(NULL);
    auto tm = *localtime(&t);
    char * ctime = asctime(&tm);
    ctime[strlen(ctime) - 1] = ' ';
    cout << ctime << s << endl;
}

inline double fast_pow(double a, double b) {
    union {
        double d;
        int x[2];
    } u = { a };
    u.x[1] = (int)(b * (u.x[1] - 1072632447) + 1072632447);
    u.x[0] = 0;
    return u.d;
}