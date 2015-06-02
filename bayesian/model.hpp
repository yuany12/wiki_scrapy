#pragma once

#include <cstdlib>
#include <ctime>
#include <set>
#include <utility>
#include <cmath>
#include <cstdio>
#include <cstring>
#include "utils.hpp"
#include "fast.hpp"

using namespace std;

char temp[200];

const float LOG_2_PI = log2(atan(1) * 8);
const float _2_PI = atan(1) * 8;

class document {
public:
    int r_id;
    int * w_id;
    int w_cnt;
    int * w_freq;
};

float log_gamma_ratio(float x1, float x2) {
    float u = x1 - x2;
    float n = x1 - 0.5 - u * 0.5;
    return u * 0.5 * log(n * n + (1 - u * u) / 12);
}

int uni_sample(float * p, int len) {
    float sum = 0;
    for (int i = 0; i < len; i ++) sum += p[i];
    float cur = 0, th = 1.0 * rand() / RAND_MAX;
    for (int i = 0; i < len; i ++) {
        cur += p[i] / sum;
        if (cur >= th) return i;
    }
    return len - 1;
}

float gaussian(float x, float mu, float lambda) {
    return pow(lambda, 0.5) * exp(- lambda * 0.5 * (x - mu) * (x - mu));
}

float log_gaussian(float x, float mu, float lambda) {
    return 0.5 * log(lambda) * (-lambda * 0.5 * (x - mu) * (x - mu));
}

class model {
public:
    float alpha;   // hyperparameter for dirichlet distribution
    float ** theta_d_t;    // multinomial distibution for each document, D times T
    int ** z_d_m;   // latent topic of each keyword in the document, D times M_d
    float ** f_k_w; // keyword embeddings of each keyword, W times E_k
    int * y_d;  // latent topic of each researcher, D
    float ** f_r_d;    // researcher embeddings, D times E_r

    float mu_0, kappa_0, beta_0, alpha_0; // hyperparameters for Gaussian distribution

    float ** mu_k_t;    // Gaussian mean for keyword embeddings, T
    float ** lambda_k_t;    // Gaussian precision for keyword embeddings, T
    float ** mu_r_t;    // Gaussian mean for researcher embeddings, T
    float ** lambda_r_t;    // Gaussian precision for researcher embeddings, T
    int D;  // number of documents
    int * M;  // number of keywords in each document, D
    const int T = 100;  // number of topics
    int W;  // number of keywords
    static const int E_k = 200;    // dimension of keyword embeddings
    static const int E_r = 128;    // dimension of researcher embeddings

    document * docs;

    const int time_lag = 1;   // time lag of parameter read out
    const int samp_topic_max_iter = 100; // max iteration
    int read_out_cnt;

    int ** n_d_t, ** n_w_t;   // number of topic t in document d, D times T
    int * n_k_t, * n_r_t;
    float ** sqr_k, ** sum_k, ** sqr_r, ** sum_r;

    const float lr = 1e-2; // learning rate for embedding update
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

    model(document * docs, int D, int W, float ** f_r_d, float ** f_k_w):
        docs(docs), D(D), W(W), f_r_d(f_r_d), f_k_w(f_k_w) {

        srand(0);

        alpha = 1.0 * 50 / T;

        theta_d_t = new float*[D];
        for (int i = 0; i < D; i ++) {
            theta_d_t[i] = new float[T];
            memset(theta_d_t[i], 0, sizeof(float) * T);
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

        mu_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            mu_k_t[i] = new float[E_k];
            memset(mu_k_t[i], 0, sizeof(float) * E_k);
        }

        lambda_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            lambda_k_t[i] = new float[E_k];
            memset(lambda_k_t[i], 0, sizeof(float) * E_k);
        }

        mu_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            mu_r_t[i] = new float[E_r];
            memset(mu_r_t[i], 0, sizeof(float) * E_r);
        }

        lambda_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            lambda_r_t[i] = new float[E_r];
            memset(lambda_r_t[i], 0, sizeof(float) * E_r);
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

        sqr_k = new float*[T]; sum_k = new float*[T];
        sqr_r = new float*[T]; sum_r = new float*[T];
        for (int i = 0; i < T; i ++) {
            sqr_k[i] = new float[E_k];
            sum_k[i] = new float[E_k];
            memset(sqr_k[i], 0, sizeof(float) * E_k);
            memset(sum_k[i], 0, sizeof(float) * E_k);

            sqr_r[i] = new float[E_r];
            sum_r[i] = new float[E_r];
            memset(sqr_r[i], 0, sizeof(float) * E_r);
            memset(sum_r[i], 0, sizeof(float) * E_r);
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

    float log_likelihood() {
        float llh = 0.0;
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
            float sum = 0;
            for (int j = 0; j < T; j ++) sum += n_d_t[i][j] + alpha;
            for (int j = 0; j < T; j ++) theta_d_t[i][j] += (n_d_t[i][j] + alpha) / sum;
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                mu_r_t[i][j] += kappa_0 + (n_r_t[i] > 0 ? (mu_0 * kappa_0 + sum_r[i][j]) / (kappa_0 + n_r_t[i]) : 0);

                int n = n_r_t[i];
                float mean = n > 0 ? sum_r[i][j] / n : 0;
                float variance = sqr_r[i][j] - (n > 0 ? sum_r[i][j] * sum_r[i][j] / n : 0);

                float alpha_n = alpha_0 + 0.5 * n;
                float beta_n = beta_0 + 0.5 * variance + 
                    kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

                lambda_r_t[i][j] += alpha_n / beta_n;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                mu_k_t[i][j] += kappa_0 + (n_k_t[i] > 0 ? (mu_0 * kappa_0 + sum_k[i][j]) / (kappa_0 + n_k_t[i]) : 0);

                int n = n_k_t[i];
                float mean = n > 0 ? sum_k[i][j] / n : 0;
                float variance = sqr_k[i][j] - (n > 0 ? sum_k[i][j] * sum_k[i][j] / n : 0);

                float alpha_n = alpha_0 + 0.5 * n;
                float beta_n = beta_0 + 0.5 * variance +
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

    inline void set_k_topic(int d, int m, int t) {
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

    inline float g_t(int t, int * n_r_t, int dn) {
        float ret = 0.0;
        int n = n_r_t[t];
        ret += log_gamma_ratio(n + dn, n);
        ret += 0.5 * log2(n / (n + dn));
        ret += 0.5 * dn * LOG_2_PI;
        return ret;
    }

    inline float g(int t, int e, float f, int * n_r_t, float ** sum_r, float ** sqr_r, int dn) {
        int n = n_r_t[t];
        float beta_n_pr = n > 0 ? 0.5 * (sqr_r[t][e] - sum_r[t][e] * sum_r[t][e] / n) : 0;
        float t_sum = sum_r[t][e] + f * dn;
        float beta_n = 0.5 * (sqr_r[t][e] + f * f * dn - t_sum * t_sum / (n + dn));
        return n * fasterlog2(beta_n_pr) - (n + dn) * fasterlog2(beta_n);

        // int n = n_r_t[t];
        // float mean = n > 0 ? sum_r[t][e] / n : 0;
        // float variance = n > 0 ? sqr_r[t][e] - sum_r[t][e] * sum_r[t][e] / n : 0;

        // float alpha_n_pr = alpha_0 + 0.5 * n;
        // float beta_n_pr = beta_0 + 0.5 * variance +
        //     kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);
        // float kappa_n_pr = kappa_0 + n;

        // n += dn;
        // float sum = sum_r[t][e] + f * dn;
        // float sqr = sqr_r[t][e] + f * f * dn;
        // mean = sum / n;
        // variance = sqr - sum * sum / n;

        // float alpha_n = alpha_0 + 0.5 * n;
        // float beta_n = beta_0 + 0.5 * variance + 
        //     kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);
        // float kappa_n = kappa_0 + n;

        // float ret = 1.0;
        // ret *= gamma_ratio(alpha_n, alpha_n_pr);
        // ret *= fast_pow(beta_n_pr, alpha_n_pr) / fast_pow(beta_n, alpha_n);
        // ret *= fast_pow(kappa_n_pr / kappa_n, 0.5);
        // ret *= fast_pow(_2_PI, dn * 0.5);
        // return ret;
    }

    void sample_topics() {
        const int max_con = 10;

        int topics[D];
        int ** k_topics = new int * [D];
        for (int i = 0; i < D; i ++) k_topics[i] = new int[M[i]];

        float g_r_t[T];
        float g_k_t[T][max_con + 1];

        for (int i = 0; i < samp_topic_max_iter; i ++) {
            sprintf(temp, "sampling topics #%d log-likelihood = %f", i, log_likelihood());
            logging(temp);

            for (int j = 0; j < T; j ++) {
                g_r_t[j] = g_t(j, n_r_t, 1);
            }

            #pragma omp parallel for num_threads(64)
            for (int j = 0; j < D; j ++) {
                float p[T];

                for (int k = 0; k < T; k ++) {
                    p[k] = n_d_t[j][k];
                    if (p[k] == 0) continue;

                    float temp = g_r_t[j] * E_r;

                    for (int l = 0; l < E_r; l ++) {
                        temp += g(k, l, f_r_d[j][l], n_r_t, sum_r, sqr_r, 1);
                    }

                    p[k] *= pow2(temp);
                }

                topics[j] = uni_sample(p, T);
            }

            for (int j = 0; j < D; j ++) {
                set_r_topic(j, topics[j]);
            }

            for (int j = 0; j < T; j ++) {
                for (int k = 1; k < max_con + 1; k ++) {
                    g_k_t[j][k] = g_t(j, n_k_t, k);
                }
            }

            #pragma omp parallel for num_threads(64) schedule(dynamic, 1000)
            for (int j = 0; j < D; j ++) {
                if (j % 100000 == 0) {
                    sprintf(temp, "sampling keyword %d", j);
                    logging(temp);
                }

                float p[T];

                for (int k = 0; k < M[j]; k ++) {
                    int w_id = docs[j].w_id[k], w_freq = docs[j].w_freq[k];

                    for (int l = 0; l < T; l ++) {
                        p[l] = n_d_t[j][y_d[j]] + ((l == y_d[j]) - (z_d_m[j][k] == y_d[j])) * w_freq;

                        float temp = w_freq <= max_con ? g_k_t[l][w_freq] : g_t(l, n_k_t, w_freq);
                        temp *= E_k;

                        for (int m = 0; m < E_k; m ++) {
                            temp += g(l, m, f_k_w[w_id][m], n_k_t, sum_k, sqr_k, w_freq);
                        }

                        p[l] *= pow2(temp);
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
            sprintf(temp, "updating embeddings #%d log-likelihood = %f", tt, log_likelihood());
            logging(temp);

            for (int i = 0; i < D; i ++) {
                for (int j = 0; j < E_r; j ++) {
                    float gd = 0.0;
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
                        float gd = 0.0;
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
            sprintf(temp, "##### learning #%d #####", i);
            logging(temp);

            sample_topics();
            embedding_update();
        }
    }

    float predict(int r_id, int w_id) {
        float prob = 0.0;
        for (int i = 0; i < T; i ++) {
            if (theta_d_t[r_id][i] == 0) continue;
            float cur = 1.0;
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