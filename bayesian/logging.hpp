#pragma once

#include <iostream>
#include <iomanip>
#include <ctime>

using namespace std;

void logging(const char* s) {
    auto t = time(NULL);
    auto tm = *localtime(&t);
    cout << put_time(&tm, "%d-%m-%Y %H-%M-%S") << s << endl;
}