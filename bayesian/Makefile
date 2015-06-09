all: main predict

main: main.cpp data.hpp utils.hpp
	g++ -o main main.cpp -std=c++11 -fopenmp -O3

predict: predict.cpp
	g++ -o predict predict.cpp -std=c++11 -fopenmp -O3

clean:
	rm main