#pragma once

#include <cstdlib>
#include <ctime>
#include <set>
#include <utility>
#include <cmath>
#include <cstdio>
#include <cstring>
#include "utils.hpp"

using namespace std;

char temp[200];

const double LOG_2_PI = log(atan(1)*4 * 2);
const double _2_PI = atan(1) * 8;

class document {
public:
    int r_id;
    int * w_id;
    int w_cnt;
    int * w_freq;
};

inline double gamma_ratio(double x1, double x2) {
    double u = x1 - x2;
    double n = x1 - 0.5 - u * 0.5;
    return fast_pow(n * n + (1 - u * u) / 12, u / 2);
}

double log_gamma_ratio(double x1, double x2) {
    double u = x1 - x2;
    double n = x1 - 0.5 - u * 0.5;
    return u * 0.5 * log(n * n + (1 - u * u) / 12);
}

int uni_sample(double * p, int len) {
    double sum = 0;
    for (int i = 0; i < len; i ++) sum += p[i];
    double cur = 0, th = 1.0 * rand() / RAND_MAX;
    for (int i = 0; i < len; i ++) {
        cur += p[i] / sum;
        if (cur >= th) return i;
    }
    return len - 1;
}

double gaussian(double x, double mu, double lambda) {
    return fast_pow(lambda, 0.5) * exp(- lambda * 0.5 * (x - mu) * (x - mu));
}

double log_gaussian(double x, double mu, double lambda) {
    return 0.5 * lambda * (-lambda * 0.5 * (x - mu) * (x - mu));
}

class model {
public:
    double alpha;   // hyperparameter for dirichlet distribution
    double ** theta_d_t;    // multinomial distibution for each document, D times T
    int ** z_d_m;   // latent topic of each keyword in the document, D times M_d
    double ** f_k_w; // keyword embeddings of each keyword, W times E_k
    int * y_d;  // latent topic of each researcher, D
    double ** f_r_d;    // researcher embeddings, D times E_r

    double mu_0, kappa_0, beta_0, alpha_0; // hyperparameters for Gaussian distribution

    double ** mu_k_t;    // Gaussian mean for keyword embeddings, T
    double ** lambda_k_t;    // Gaussian precision for keyword embeddings, T
    double ** mu_r_t;    // Gaussian mean for researcher embeddings, T
    double ** lambda_r_t;    // Gaussian precision for researcher embeddings, T
    int D;  // number of documents
    int * M;  // number of keywords in each document, D
    const int T = 100;  // number of topics
    int W;  // number of keywords
    static const int E_k = 200;    // dimension of keyword embeddings
    static const int E_r = 128;    // dimension of researcher embeddings

    document * docs;

    const int time_lag = 10;   // time lag of parameter read out
    const int samp_topic_max_iter = 100; // max iteration
    int read_out_cnt;

    int ** n_d_t, ** n_w_t;   // number of topic t in document d, D times T
    int * n_k_t, * n_r_t;
    double ** sqr_k, ** sum_k, ** sqr_r, ** sum_r;

    const double lr = 1e-2; // learning rate for embedding update
    const int emb_max_iter = 10;

    const int learning_max_iter = 10;

    int max_M;

    ~model() {
        for (int i = 0; i < D; i ++) delete [] theta_d_t[i];
        delete [] theta_d_t;

        for (int i = 0; i < D; i ++) delete [] z_d_m[i];
        delete [] z_d_m;

        for (int i = 0; i < W; i ++) delete [] f_k_w[i];
        delete [] f_k_w;

        delete [] y_d;

        for (int i = 0; i < D; i ++) delete [] f_r_d[i];
        delete [] f_r_d;

        for (int i = 0; i < T; i ++) delete [] mu_k_t[i];
        for (int i = 0; i < T; i ++) delete [] lambda_k_t[i];
        for (int i = 0; i < T; i ++) delete [] mu_r_t[i];
        for (int i = 0; i < T; i ++) delete [] lambda_r_t[i];
        delete [] mu_k_t;
        delete [] lambda_k_t;
        delete [] mu_r_t;
        delete [] lambda_r_t;

        delete [] M;
        delete [] docs;

        for (int i = 0; i < D; i ++) delete [] n_d_t[i];
        delete [] n_d_t;

        for (int i = 0; i < W; i ++) delete [] n_w_t[i];
        delete [] n_w_t;

        delete [] n_k_t;
        delete [] n_r_t;

        for (int i = 0; i < T; i ++) delete [] sqr_k[i];
        for (int i = 0; i < T; i ++) delete [] sum_k[i];
        for (int i = 0; i < T; i ++) delete [] sqr_r[i];
        for (int i = 0; i < T; i ++) delete [] sum_r[i];

        delete [] sqr_k;
        delete [] sum_k;
        delete [] sqr_r;
        delete [] sum_r;
    }

    model(document * docs, int D, int W, double ** f_r_d, double ** f_k_w):
        docs(docs), D(D), W(W), f_r_d(f_r_d), f_k_w(f_k_w) {

        srand(0);

        alpha = 1.0 * 50 / T;

        theta_d_t = new double*[D];
        for (int i = 0; i < D; i ++) {
            theta_d_t[i] = new double[T];
            memset(theta_d_t[i], 0, sizeof(double) * T);
        }

        M = new int[D];
        for (int i = 0; i < D; i ++) M[i] = docs[i].w_cnt;

        max_M = 0;
        for (int i = 0; i < D; i ++) max_M = max(max_M, M[i]);

        z_d_m = new int*[D];
        for (int i = 0; i < D; i ++) {
            z_d_m[i] = new int[M[i]];
            for (int j = 0; j < M[i]; j ++) {
                z_d_m[i][j] = rand() % T;
            }
        }

        y_d = new int[D];
        for (int i = 0; i < D; i ++) {
            y_d[i] = rand() % T;
        }

        mu_0 = kappa_0 = alpha_0 = beta_0 = 0.0;

        mu_k_t = new double * [T];
        for (int i = 0; i < T; i ++) {
            mu_k_t[i] = new double[E_k];
            memset(mu_k_t[i], 0, sizeof(double) * E_k);
        }

        lambda_k_t = new double * [T];
        for (int i = 0; i < T; i ++) {
            lambda_k_t[i] = new double[E_k];
            memset(lambda_k_t[i], 0, sizeof(double) * E_k);
        }

        mu_r_t = new double * [T];
        for (int i = 0; i < T; i ++) {
            mu_r_t[i] = new double[E_r];
            memset(mu_r_t[i], 0, sizeof(double) * E_r);
        }

        lambda_r_t = new double * [T];
        for (int i = 0; i < T; i ++) {
            lambda_r_t[i] = new double[E_r];
            memset(lambda_r_t[i], 0, sizeof(double) * E_r);
        }

        n_d_t = new int*[D];   
        for (int i = 0; i < D; i ++) {
            n_d_t[i] = new int[T];
            memset(n_d_t[i], 0, sizeof(int) * T);
        }

        n_w_t = new int*[W];
        for (int i = 0; i < W; i ++) {
            n_w_t[i] = new int[T];
            memset(n_w_t[i], 0, sizeof(int) * T);
        }

        n_k_t = new int[T];
        memset(n_k_t, 0, sizeof(int) * T);

        n_r_t = new int[T];
        memset(n_r_t, 0, sizeof(int) * T);

        sqr_k = new double*[T]; sum_k = new double*[T];
        sqr_r = new double*[T]; sum_r = new double*[T];
        for (int i = 0; i < T; i ++) {
            sqr_k[i] = new double[E_k];
            sum_k[i] = new double[E_k];
            memset(sqr_k[i], 0, sizeof(double) * E_k);
            memset(sum_k[i], 0, sizeof(double) * E_k);

            sqr_r[i] = new double[E_r];
            sum_r[i] = new double[E_r];
            memset(sqr_r[i], 0, sizeof(double) * E_r);
            memset(sum_r[i], 0, sizeof(double) * E_r);
        }

        for (int i = 0; i < D; i ++) {
            int topic = y_d[i];
            for (int j = 0; j < E_r; j ++) {
                sqr_r[topic][j] += f_r_d[i][j] * f_r_d[i][j];
                sum_r[topic][j] += f_r_d[i][j];
            }
            n_r_t[topic] ++;

            for (int j = 0; j < M[i]; j ++) {
                int topic = z_d_m[i][j], w_id = docs[i].w_id[j], w_freq = docs[i].w_freq[j];
                for (int k = 0; k < E_k; k ++) {
                    sqr_k[topic][k] += f_k_w[w_id][k] * f_k_w[w_id][k] * w_freq;
                    sum_k[topic][k] += f_k_w[w_id][k] * w_freq;
                }
                n_k_t[topic] += w_freq;
                n_d_t[i][topic] += w_freq;
                n_w_t[w_id][topic] += w_freq;
            }
        }

        read_out_cnt = 0;

        logging("model init done");
    }

    double log_likelihood() {
        double llh = 0.0;
        for (int i = 0; i < D; i ++) {
            for (int j = 0; j < E_r; j ++) {
                int topic = y_d[i];
                llh += log_gaussian(f_r_d[i][j], mu_r_t[topic][j], lambda_r_t[topic][j]);
            }
        }
        for (int i = 0; i < D; i ++) {
            for (int j = 0; j < M[i]; j ++) {
                int topic = z_d_m[i][j], w_id = docs[i].w_id[j], w_freq = docs[i].w_freq[j];
                for (int k = 0; k < E_k; k ++) {
                    llh += log_gaussian(f_k_w[w_id][k], mu_k_t[topic][k], lambda_k_t[topic][k]) * w_freq;
                }
            }
        }
        return llh;
    }

    void read_out() {
        read_out_cnt ++;

        for (int i = 0; i < D; i ++) {
            double sum = 0;
            for (int j = 0; j < T; j ++) sum += n_d_t[i][j] + alpha;
            for (int j = 0; j < T; j ++) theta_d_t[i][j] += (n_d_t[i][j] + alpha) / sum;
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                mu_r_t[i][j] += kappa_0 + (n_r_t[i] > 0 ? (mu_0 * kappa_0 + sum_r[i][j]) / (kappa_0 + n_r_t[i]) : 0);

                int n = n_r_t[i];
                double mean = n > 0 ? sum_r[i][j] / n : 0;
                double variance = sqr_r[i][j] - (n > 0 ? sum_r[i][j] * sum_r[i][j] / n : 0);

                double alpha_n = alpha_0 + 0.5 * n;
                double beta_n = beta_0 + 0.5 * variance + 
                    kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

                lambda_r_t[i][j] += alpha_n / beta_n;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                mu_k_t[i][j] += kappa_0 + (n_k_t[i] > 0 ? (mu_0 * kappa_0 + sum_k[i][j]) / (kappa_0 + n_k_t[i]) : 0);

                int n = n_k_t[i];
                double mean = n > 0 ? sum_k[i][j] / n : 0;
                double variance = sqr_k[i][j] - (n > 0 ? sum_k[i][j] * sum_k[i][j] / n : 0);

                double alpha_n = alpha_0 + 0.5 * n;
                double beta_n = beta_0 + 0.5 * variance +
                    kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

                lambda_k_t[i][j] += alpha_n / beta_n;
            }
        }
    }

    void norm_read_out() {
        for (int i = 0; i < D; i ++) {
            for (int j = 0; j < T; j ++) {
                theta_d_t[i][j] /= read_out_cnt;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                mu_r_t[i][j] /= read_out_cnt;
                lambda_r_t[i][j] /= read_out_cnt;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                mu_k_t[i][j] /= read_out_cnt;
                lambda_k_t[i][j] /= read_out_cnt;
            }
        }
    }

    inline void set_k_topic(int d, int m, int t, bool del) {
        int topic = z_d_m[d][m], w_id = docs[d].w_id[m], w_freq = docs[d].w_freq[m];
        for (int i = 0; i < E_k; i ++) {
            sqr_k[topic][i] -= f_k_w[w_id][i] * f_k_w[w_id][i] * w_freq;
            sum_k[topic][i] -= f_k_w[w_id][i] * w_freq;
        }
        n_k_t[topic] -= w_freq;
        n_d_t[d][topic] -= w_freq;
        n_w_t[w_id][topic] -= w_freq;
        
        z_d_m[d][m] = t;
        for (int i = 0; i < E_k; i ++) {
            sqr_k[t][i] += f_k_w[w_id][i] * f_k_w[w_id][i] * w_freq;
            sum_k[t][i] += f_k_w[w_id][i] * w_freq;
        }
        n_k_t[t] += w_freq;
        n_d_t[d][t] += w_freq;
        n_w_t[w_id][t] += w_freq;
    }

    inline void set_r_topic(int d, int t) {
        int topic = y_d[d];
        for (int i = 0; i < E_r; i ++) {
            sqr_r[topic][i] -= f_r_d[d][i] * f_r_d[d][i];
            sum_r[topic][i] -= f_r_d[d][i];
        }
        n_r_t[topic] --;

        y_d[d] = t;
        for (int i = 0; i < E_r; i ++) {
            sqr_r[t][i] += f_r_d[d][i] * f_r_d[d][i];
            sum_r[t][i] += f_r_d[d][i];
        }
        n_r_t[t] ++;
    }

    inline double g(int t, int e, double f, int * n_r_t, double ** sum_r, double ** sqr_r, int dn) {
        double ret = 1.0;
        int n = n_r_t[t];
        ret *= gamma_ratio(n + dn, n);
        double beta_n_pr = n > 0 ? 0.5 * (sqr_r[t][e] - sum_r[t][e] * sum_r[t][e] / n) : 0;
        double t_sum = sum_r[t][e] + f * dn;
        double beta_n = 0.5 * (sqr_r[t][e] + f * f * dn - t_sum * t_sum / (n + dn));
        ret *= fast_pow(beta_n_pr, n) / fast_pow(beta_n, n + dn);
        ret *= fast_pow(n / (n + dn), 0.5);
        ret *= fast_pow(_2_PI, dn * 0.5);
        return ret;

        // int n = n_r_t[t];
        // double mean = n > 0 ? sum_r[t][e] / n : 0;
        // double variance = n > 0 ? sqr_r[t][e] - sum_r[t][e] * sum_r[t][e] / n : 0;

        // double alpha_n_pr = alpha_0 + 0.5 * n;
        // double beta_n_pr = beta_0 + 0.5 * variance +
        //     kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);
        // double kappa_n_pr = kappa_0 + n;

        // n += dn;
        // double sum = sum_r[t][e] + f * dn;
        // double sqr = sqr_r[t][e] + f * f * dn;
        // mean = sum / n;
        // variance = sqr - sum * sum / n;

        // double alpha_n = alpha_0 + 0.5 * n;
        // double beta_n = beta_0 + 0.5 * variance + 
        //     kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);
        // double kappa_n = kappa_0 + n;

        // double ret = 1.0;
        // ret *= gamma_ratio(alpha_n, alpha_n_pr);
        // ret *= fast_pow(beta_n_pr, alpha_n_pr) / fast_pow(beta_n, alpha_n);
        // ret *= fast_pow(kappa_n_pr / kappa_n, 0.5);
        // ret *= fast_pow(_2_PI, dn * 0.5);
        // return ret;
    }

    void sample_topics() {
        int topics[D];
        int ** k_topics = new int * [D];
        for (int i = 0; i < D; i ++) k_topics[i] = new int[M[i]];

        for (int i = 0; i < samp_topic_max_iter; i ++) {
            sprintf(temp, "sampling topics #%d log-likelihood = %0.8f\n", i, log_likelihood());
            logging(temp);

            #pragma omp parallel for num_threads(64)
            for (int j = 0; j < D; j ++) {
                if (j % 10000 == 0) {
                    sprintf(temp, "sampling researcher %d", j);
                    logging(temp);
                }

                double p[T];

                for (int k = 0; k < T; k ++) {
                    p[k] = n_d_t[j][k];

                    for (int l = 0; l < E_r; l ++) {
                        p[k] *= g(k, l, f_r_d[j][l], n_r_t, sum_r, sqr_r, 1);
                    }
                }

                topics[j] = uni_sample(p, T);
            }

            for (int j = 0; j < D; j ++) {
                set_r_topic(j, topics[j]);
            }

            #pragma omp parallel for num_threads(64) schedule(dynamic, 1000)
            for (int j = 0; j < D; j ++) {
                if (j % 10000 == 0) {
                    sprintf(temp, "sampling keyword %d", j);
                    logging(temp);
                }

                double p[T];

                for (int k = 0; k < M[j]; k ++) {
                    int w_id = docs[j].w_id[k], w_freq = docs[j].w_freq[k];

                    for (int l = 0; l < T; l ++) {
                        p[l] = n_d_t[j][y_d[j]] + ((l == y_d[j]) - (z_d_m[j][k] == y_d[j])) * w_freq;

                        for (int m = 0; m < E_k; m ++) {
                            p[l] *= g(l, m, f_k_w[w_id][m], n_k_t, sum_k, sqr_k, w_freq);
                        }
                    }
                    k_topics[j][k] = uni_sample(p, T);
                }
            }
            for (int j = 0; j < D; j ++) {
                for (int k = 0; k < M[j]; k ++) {
                    set_k_topic(j, k, k_topics[j][k]);
                }
            }

            if (i > 0 && i % time_lag == 0) {
                read_out();
            }
        }

        norm_read_out();

        for (int i = 0; i < D; i ++) delete [] k_topics[i];
        delete [] k_topics;
    }

    void embedding_update() {
        for (int tt = 0; tt < emb_max_iter; tt ++) {
            sprintf(temp, "updating embeddings #%d log-likelihood = %0.8f\n", tt, log_likelihood());
            logging(temp);

            for (int i = 0; i < D; i ++) {
                for (int j = 0; j < E_r; j ++) {
                    double gd = 0.0;
                    for (int k = 0; k < T; k ++) {
                        if (n_d_t[i][k] == 0) continue;
                        gd += 0.5 * n_d_t[i][k] * lambda_r_t[k][j] * log(lambda_r_t[k][j]) * (f_r_d[i][j] - mu_r_t[k][j]);
                    }
                    f_r_d[i][j] -= gd * lr;
                }
            }

            for (int i = 0; i < D; i ++) {
                for (int j = 0; j < M[i]; j ++) {
                    int w_id = docs[i].w_id[j];
                    for (int k = 0; k < E_k; k ++) {
                        double gd = 0.0;
                        for (int l = 0; l < T; l ++) {
                            if (n_w_t[w_id][l] == 0) continue;
                            gd += 0.5 * n_w_t[w_id][l] * lambda_k_t[l][k] * log(lambda_k_t[l][k]) * (f_k_w[w_id][k] - mu_k_t[l][k]);
                        }
                        f_k_w[w_id][k] -= gd * lr;
                    }
                }
            }
        }
    }

    void learn() {
        for (int i = 0; i < learning_max_iter; i ++) {
            sprintf(temp, "##### learning #%d #####\n", i);
            logging(temp);

            sample_topics();
            embedding_update();
        }
    }

    double predict(int r_id, int w_id) {
        double prob = 0.0;
        for (int i = 0; i < T; i ++) {
            if (theta_d_t[r_id][i] == 0) continue;
            double cur = 1.0;
            for (int j = 0; j < E_r; j ++)
                cur *= gaussian(f_r_d[r_id][j], mu_r_t[i][j], lambda_r_t[i][j]);
            for (int j = 0; j < E_k; j ++)
                cur *= gaussian(f_k_w[w_id][j], mu_k_t[i][j], lambda_k_t[i][j]);
            cur *= theta_d_t[r_id][i];
            prob += cur;
        }
        return prob;
    }
};