#pragma once

#include <iostream>
#include <iomanip>
#include <ctime>

using namespace std;

void logging(const char* s) {
    auto t = time(NULL);
    auto tm = *localtime(&t);
    char * ctime = asctime(&tm);
    ctime[strlen(ctime) - 1] = ' ';
    cout << ctime << s << endl;
}