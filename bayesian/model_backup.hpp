#pragma once

#include <cstdlib>
#include <ctime>
#include <set>
#include <utility>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cassert>
#include "utils.hpp"

using namespace std;

char temp[200];

#define ASSERT_VALNUM(x) assert(! isnan(x) && ! isinf(x));

const float LOG_2_PI = log2(atan(1) * 8);
const float _2_PI = atan(1) * 8;
const float LOG_INV_2_PI = log2(1.0 / (atan(1) * 8));
const float LOG_2_EXP = log2(exp(1.0));

class document {
public:
    int r_id;
    int w_cnt;
    int * w_id;
    int * w_freq;
};

inline float log_gamma_ratio(float x1, float x2) {
    float u = x1 - x2;
    float n = x1 - 0.5 - u * 0.5;
    return u * 0.5 * log2(n * n + (1 - u * u) / 12);
}

inline int uni_sample(float * p, int len) {
    float sum = 0;
    for (int i = 0; i < len; i ++) sum += p[i];
    float cur = 0, th = 1.0 * rand() / RAND_MAX;
    for (int i = 0; i < len; i ++) {
        cur += p[i] / sum;
        if (cur >= th) return i;
    }
    return len - 1;
}

inline int log_uni_sample(float * p, int len) {
    static const float MIN_FLOAT = -1e30;
    static const float BIG_FLOAT = 100.0f;
    static const float MAX_GAP = 4.0f;
    float max_ = MIN_FLOAT;
    for (int i = 0; i < len; i ++) {
        // if (p[i] == 0) continue;
        max_ = max(max_, p[i]);
    }
    for (int i = 0; i < len; i ++) {
        // if (p[i] == 0) continue;
        if (max_ - p[i] > MAX_GAP) p[i] = 0.0;
        else {
            p[i] = BIG_FLOAT / fastpow2(max_ - p[i]);
            ASSERT_VALNUM(p[i]);
        }
    }
    return uni_sample(p, len);
}

inline float log_gaussian(float x, float mu, float lambda) {
    float ret = LOG_INV_2_PI + 0.5 * log2(lambda) + (-lambda * 0.5 * (x - mu) * (x - mu))* LOG_2_EXP;
    ASSERT_VALNUM(ret);
    return ret;
}

class model {
public:
    float alpha;   // hyperparameter for dirichlet distribution
    float ** theta_d_t;    // multinomial distibution for each document, D times T
    int ** z_d_m;   // latent topic of each keyword in the document, D times M_d
    float ** f_k_w; // keyword embeddings of each keyword, W times E_k
    int * y_d;  // latent topic of each researcher, D
    float ** f_r_d;    // researcher embeddings, D times E_r

    float ** t_f_r_d, ** t_f_k_w;

    float mu_0 = 0.0, kappa_0 = 1e-4, beta_0 = 1.0, alpha_0 = 1e3; // hyperparameters for Gaussian distribution

    float ** mu_k_t;    // Gaussian mean for keyword embeddings, T
    float ** lambda_k_t;    // Gaussian precision for keyword embeddings, T
    float ** mu_r_t;    // Gaussian mean for researcher embeddings, T
    float ** lambda_r_t;    // Gaussian precision for researcher embeddings, T
    int D;  // number of documents
    int * M;  // number of keywords in each document, D
    const int T = 200;  // number of topics
    int W;  // number of keywords
    static const int E_k = 200;    // dimension of keyword embeddings 200
    static const int E_r = 128;    // dimension of researcher embeddings 128

    document * docs;

    const int time_lag = 10;   // time lag of parameter read out
    const int samp_topic_max_iter = 10; // max iteration
    int read_out_cnt;

    int ** n_d_t, ** n_w_t;   // number of topic t in document d, D times T
    int * n_k_t, * n_r_t;
    float ** sqr_k, ** sum_k, ** sqr_r, ** sum_r;

    float lr_r = 1e-3, lr_k = 1e-3; // learning rate for embedding update
    const float decay = 0.5;
    const int emb_max_iter = 5;

    const int learning_max_iter = 1;

    float * llh_temp;

    float ** sum_theta_d_t;
    float ** sum_mu_k_t, ** sum_lambda_k_t, ** sum_mu_r_t, ** sum_lambda_r_t;

    const float laplace = 1e-5; // 0.1

    const float multi_magnifier = 0.0;

    int * sum_m;

    ~model() {
        for (int i = 0; i < D; i ++) delete [] theta_d_t[i];
        delete [] theta_d_t;

        for (int i = 0; i < D; i ++) delete [] sum_theta_d_t[i];
        delete [] sum_theta_d_t;

        for (int i = 0; i < D; i ++) delete [] z_d_m[i];
        delete [] z_d_m;

        for (int i = 0; i < D; i ++) delete [] t_f_r_d[i];
        delete [] t_f_r_d;

        for (int i = 0; i < W; i ++) delete [] t_f_k_w[i];
        delete [] t_f_k_w;

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

        for (int i = 0; i < T; i ++) delete [] sum_mu_k_t[i];
        for (int i = 0; i < T; i ++) delete [] sum_lambda_k_t[i];
        for (int i = 0; i < T; i ++) delete [] sum_mu_r_t[i];
        for (int i = 0; i < T; i ++) delete [] sum_lambda_r_t[i];
        delete [] sum_mu_k_t;
        delete [] sum_lambda_k_t;
        delete [] sum_mu_r_t;
        delete [] sum_lambda_r_t;

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

        delete [] llh_temp;

        delete [] sum_m;
    }

    model(document * docs, int D, int W, float ** f_r_d, float ** f_k_w):
        docs(docs), D(D), W(W), f_r_d(f_r_d), f_k_w(f_k_w) {

        // this->D /= 100;

        srand(0);

        t_f_r_d = new float * [D];
        for (int i = 0; i < D; i ++) t_f_r_d[i] = new float[E_r];

        t_f_k_w = new float * [W];
        for (int i = 0; i < W; i ++) t_f_k_w[i] = new float[E_k];

        alpha = 1.0 * 50 / T;

        theta_d_t = new float*[D];
        for (int i = 0; i < D; i ++) {
            theta_d_t[i] = new float[T];
        }

        sum_theta_d_t = new float * [D];
        for (int i = 0; i < D; i ++) {
            sum_theta_d_t[i] = new float[T];
        }

        M = new int[D];
        for (int i = 0; i < D; i ++) M[i] = docs[i].w_cnt;

        int init_topic[W];
        for (int i = 0; i < W; i ++) {
            init_topic[i] = rand() % T;
        }

        z_d_m = new int*[D];
        for (int i = 0; i < D; i ++) {
            z_d_m[i] = new int[M[i]];
            for (int j = 0; j < M[i]; j ++) {
                int w_id = docs[i].w_id[j];
                z_d_m[i][j] = rand() % T;
            }
        }

        y_d = new int[D];
        for (int i = 0; i < D; i ++) {
            y_d[i] = rand() % T;
        }

        mu_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            mu_k_t[i] = new float[E_k];
        }

        lambda_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            lambda_k_t[i] = new float[E_k];
        }

        mu_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            mu_r_t[i] = new float[E_r];
        }

        lambda_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            lambda_r_t[i] = new float[E_r];
        }

        sum_mu_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            sum_mu_k_t[i] = new float[E_k];
        }

        sum_lambda_k_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            sum_lambda_k_t[i] = new float[E_k];
        }

        sum_mu_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            sum_mu_r_t[i] = new float[E_r];
        }

        sum_lambda_r_t = new float * [T];
        for (int i = 0; i < T; i ++) {
            sum_lambda_r_t[i] = new float[E_r];
        }

        n_d_t = new int*[D];   
        for (int i = 0; i < D; i ++) {
            n_d_t[i] = new int[T];
        }

        n_w_t = new int*[W];
        for (int i = 0; i < W; i ++) {
            n_w_t[i] = new int[T];
        }

        n_k_t = new int[T];

        n_r_t = new int[T];

        sqr_k = new float*[T]; sum_k = new float*[T];
        sqr_r = new float*[T]; sum_r = new float*[T];
        for (int i = 0; i < T; i ++) {
            sqr_k[i] = new float[E_k];
            sum_k[i] = new float[E_k];

            sqr_r[i] = new float[E_r];
            sum_r[i] = new float[E_r];
        }

        stat_k_update();
        stat_r_update();
        parameter_update();

        read_out_cnt = 0;

        llh_temp = new float[D];

        sum_m = new int[D];
        for (int i = 0; i < D; i ++) {
            sum_m[i] = 0;
            for (int j = 0; j < M[i]; j ++) sum_m[i] += docs[i].w_freq[j];
        }

        logging("model init done");
    }

    void stat_r_update() {
        memset(n_r_t, 0, sizeof (int) * T);
        for (int i = 0; i < T; i ++) {
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
        }
    }

    void stat_k_update() {
        for (int i = 0; i < D; i ++) memset(n_d_t[i], 0, sizeof(int) * T);
        for (int i = 0; i < W; i ++) memset(n_w_t[i], 0, sizeof(int) * T);

        memset(n_k_t, 0, sizeof (int) * T);

        for (int i = 0; i < T; i ++) {
            memset(sqr_k[i], 0, sizeof(float) * E_k);
            memset(sum_k[i], 0, sizeof(float) * E_k);
        }

        for (int i = 0; i < D; i ++) {
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
    }

    inline float log_likelihood() {
        float llh = 0.0;

        #pragma omp parallel for num_threads(64)
        for (int i = 0; i < D; i ++) {
            llh_temp[i] = 0.0;
            int topic = y_d[i];
            for (int j = 0; j < E_r; j ++) {
                llh_temp[i] += log_gaussian(f_r_d[i][j], mu_r_t[topic][j], lambda_r_t[topic][j]);
            }

            for (int j = 0; j < M[i]; j ++) {
                int topic = z_d_m[i][j], w_id = docs[i].w_id[j], w_freq = docs[i].w_freq[j];
                for (int k = 0; k < E_k; k ++) {
                    llh_temp[i] += log_gaussian(f_k_w[w_id][k], mu_k_t[topic][k], lambda_k_t[topic][k]) * w_freq;
                }
            }

            ASSERT_VALNUM(llh_temp[i]);
        }

        for (int i = 0; i < D; i ++) llh += llh_temp[i];
        return llh;
    }

    inline float temp_log_likelihood() {
        float llh = 0.0;

        #pragma omp parallel for num_threads(64)
        for (int i = 0; i < D; i ++) {
            llh_temp[i] = 0.0;
            int topic = y_d[i];
            for (int j = 0; j < E_r; j ++) {
                llh_temp[i] += log_gaussian(t_f_r_d[i][j], mu_r_t[topic][j], lambda_r_t[topic][j]);
            }

            for (int j = 0; j < M[i]; j ++) {
                int topic = z_d_m[i][j], w_id = docs[i].w_id[j], w_freq = docs[i].w_freq[j];
                for (int k = 0; k < E_k; k ++) {
                    llh_temp[i] += log_gaussian(t_f_k_w[w_id][k], mu_k_t[topic][k], lambda_k_t[topic][k]) * w_freq;
                }
            }

            ASSERT_VALNUM(llh_temp[i]);
        }

        for (int i = 0; i < D; i ++) llh += llh_temp[i];
        return llh;
    }

    void read_out() {
        read_out_cnt ++;

        #pragma omp parallel for num_threads(64)
        for (int i = 0; i < D; i ++) {
            for (int j = 0; j < T; j ++) sum_theta_d_t[i][j] += theta_d_t[i][j];
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                sum_mu_r_t[i][j] += mu_r_t[i][j];
                sum_lambda_r_t[i][j] += lambda_r_t[i][j];
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                sum_mu_k_t[i][j] += mu_k_t[i][j];
                sum_lambda_k_t[i][j] += lambda_k_t[i][j];
            }
        }
    }

    void parameter_update() {
        #pragma omp parallel for num_threads(64)
        for (int i = 0; i < D; i ++) {
            float sum = 0;
            for (int j = 0; j < T; j ++) sum += n_d_t[i][j] + alpha;
            for (int j = 0; j < T; j ++) theta_d_t[i][j] = (n_d_t[i][j] + alpha) / sum;
        }

        #pragma omp parallel for num_threads(12)
        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                mu_r_t[i][j] = (mu_0 * kappa_0 + sum_r[i][j]) / (kappa_0 + n_r_t[i]);

                int n = n_r_t[i];
                float mean = n > 0 ? sum_r[i][j] / n : 0;
                float variance = n > 0 ? sqr_r[i][j] - sum_r[i][j] * sum_r[i][j] / n : 0;

                float alpha_n = alpha_0 + 0.5 * n;
                float beta_n = beta_0 + 0.5 * variance + 
                    kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

                lambda_r_t[i][j] = alpha_n / beta_n;
            }
        }

        #pragma omp parallel for num_threads(12)
        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                mu_k_t[i][j] = (mu_0 * kappa_0 + sum_k[i][j]) / (kappa_0 + n_k_t[i]);

                int n = n_k_t[i];
                float variance = n > 0 ? sqr_k[i][j] - sum_k[i][j] * sum_k[i][j] / n : 0;
                float mean = n > 0 ? sum_k[i][j] / n : 0;

                float alpha_n = alpha_0 + 0.5 * n;
                float beta_n = beta_0 + 0.5 * variance +
                    kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

                lambda_k_t[i][j] = alpha_n / beta_n;
            }
        }
    }

    void norm_read_out() {
        #pragma omp parallel for num_threads(64)
        for (int i = 0; i < D; i ++) {
            for (int j = 0; j < T; j ++) {
                theta_d_t[i][j] = sum_theta_d_t[i][j] / read_out_cnt;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_r; j ++) {
                mu_r_t[i][j] = sum_mu_r_t[i][j] / read_out_cnt;
                lambda_r_t[i][j] = sum_lambda_r_t[i][j] / read_out_cnt;
            }
        }

        for (int i = 0; i < T; i ++) {
            for (int j = 0; j < E_k; j ++) {
                mu_k_t[i][j] = sum_mu_k_t[i][j] / read_out_cnt;
                lambda_k_t[i][j] = sum_lambda_k_t[i][j] / read_out_cnt;
            }
        }
    }

    inline void set_k_topic(int d, int m, int t, bool set = true, bool unset = true) {
        int topic = z_d_m[d][m], w_id = docs[d].w_id[m], w_freq = docs[d].w_freq[m];
        if (unset) {
            for (int i = 0; i < E_k; i ++) {
                sqr_k[topic][i] -= f_k_w[w_id][i] * f_k_w[w_id][i] * w_freq;
                sum_k[topic][i] -= f_k_w[w_id][i] * w_freq;
            }
            n_k_t[topic] -= w_freq;
            n_d_t[d][topic] -= w_freq;
            n_w_t[w_id][topic] -= w_freq;
        }

        if (set) {
            z_d_m[d][m] = t;
            for (int i = 0; i < E_k; i ++) {
                sqr_k[t][i] += f_k_w[w_id][i] * f_k_w[w_id][i] * w_freq;
                sum_k[t][i] += f_k_w[w_id][i] * w_freq;
            }
            n_k_t[t] += w_freq;
            n_d_t[d][t] += w_freq;
            n_w_t[w_id][t] += w_freq;
        }
    }

    inline void set_r_topic(int d, int t, bool set = true, bool unset = true) {
        if (unset) {
            int topic = y_d[d];
            for (int i = 0; i < E_r; i ++) {
                sqr_r[topic][i] -= f_r_d[d][i] * f_r_d[d][i];
                sum_r[topic][i] -= f_r_d[d][i];
            }
            n_r_t[topic] --;
        }

        if (set) {
            y_d[d] = t;
            for (int i = 0; i < E_r; i ++) {
                sqr_r[t][i] += f_r_d[d][i] * f_r_d[d][i];
                sum_r[t][i] += f_r_d[d][i];
            }
            n_r_t[t] ++;
        }
    }

    inline float g_t(int t, int * n_r_t, int dn) {
        assert(dn > 0);
        float ret = 0.0;
        int n = n_r_t[t];
        ret += log_gamma_ratio(alpha_0 + n + dn, alpha_0 + n);
        ret += 0.5 * (log2((kappa_0 + n) / (kappa_0 + n + dn)));
        ret += 0.5 * dn * LOG_2_PI;
        return ret;
    }

    inline float g(int t, int e, float f, int * n_r_t, float ** sum_r, float ** sqr_r, int dn) {
        int n = n_r_t[t];
        float mean = n > 0 ? sum_r[t][e] / n : 0;
        float variance = n > 0 ? sqr_r[t][e] - sum_r[t][e] * sum_r[t][e] / n : 0;

        float beta_n_pr = beta_0 + 0.5 * variance +
            kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

        n += dn;
        float sum = sum_r[t][e] + f * dn;
        float sqr = sqr_r[t][e] + f * f * dn;
        mean = sum / n;
        variance = sqr - sum * sum / n;

        float beta_n = beta_0 + 0.5 * variance + 
            kappa_0 * n * (mean - mu_0) * (mean - mu_0) * 0.5 * (kappa_0 + n);

        float ret = (n + alpha_0) * fasterlog2(beta_n_pr) - (n + dn + alpha_0) * fasterlog2(beta_n);
        return ret;
    }

    void sample_topics() {

        float p[T];
        // float p2[T];

        for (int i = 0; i < samp_topic_max_iter; i ++) {
            sprintf(temp, "sampling topics iter %d log-likelihood = %f", i, log_likelihood());
            logging(temp);

            for (int j = 0; j < D; j ++) {
                set_r_topic(j, 0, false, true);

                #pragma omp parallel for num_threads(20)
                for (int k = 0; k < T; k ++) {
                    float temp_p = n_d_t[j][k] + laplace;
                    temp_p = log2(temp_p) * multi_magnifier;

                    temp_p += g_t(k, n_r_t, 1) * E_r;

                    for (int l = 0; l < E_r; l ++) {
                        temp_p += g(k, l, f_r_d[j][l], n_r_t, sum_r, sqr_r, 1);
                    }
                    ASSERT_VALNUM(temp_p);
                    p[k] = temp_p;
                }

                y_d[j] = log_uni_sample(p, T);
                set_r_topic(j, y_d[j], true, false);
            }

            for (int j = 0; j < D; j ++) {

                for (int k = 0; k < M[j]; k ++) {
                    int w_id = docs[j].w_id[k], w_freq = docs[j].w_freq[k];

                    set_k_topic(j, k, 0, false, true);

                    #pragma omp parallel for num_threads(20)
                    for (int l = 0; l < T; l ++) {
                        // float temp_p = n_d_t[j][y_d[j]] + (l == y_d[j]) * w_freq + laplace;
                        float temp_p = n_d_t[j][l] + alpha;
                        temp_p = log2(temp_p) * multi_magnifier;

                        // if (j == 0 && k == 0 && l == 0)
                        // cout << "log y|z = " << temp_p;

                        temp_p += g_t(l, n_k_t, w_freq) * E_k;
                        // p2[l] = g_t(l, n_k_t, w_freq) * E_k;

                        for (int m = 0; m < E_k; m ++) {
                            temp_p += g(l, m, f_k_w[w_id][m], n_k_t, sum_k, sqr_k, w_freq);
                            // p2[l] += g(l, m, f_k_w[w_id][m], n_k_t, sum_k, sqr_k, w_freq);
                        }

                        // if (j == 0 && k == 0 && l == 0)
                        // cout << "\t log final = " << temp_p << endl;
                        ASSERT_VALNUM(temp_p);
                        p[l] = temp_p;
                    }
                    // if (j == 0 && k == 0) {
                    //     for (int l = 0; l < T; l ++) {
                    //         cout << " " << p[l];
                    //     }
                    //     cout << endl;
                    //     for (int l = 0; l < T; l ++) {
                    //         cout << " " << p2[l];
                    //     }
                    //     cout << endl;
                    // }
                    z_d_m[j][k] = log_uni_sample(p, T);
                    set_k_topic(j, k, z_d_m[j][k], true, false);
                }
            }

            parameter_update();
        }
    }

    void embedding_update() {
        float cur_llh = log_likelihood();

        for (int tt = 0; tt < emb_max_iter; tt ++) {
            sprintf(temp, "updating embeddings iter %d log-likelihood = %f", tt, cur_llh);
            logging(temp);

            #pragma omp parallel for num_threads(64)
            for (int i = 0; i < D; i ++) {
                for (int j = 0; j < E_r; j ++) {
                    int topic = y_d[i];
                    float gd = - lambda_r_t[topic][j] * (f_r_d[i][j] - mu_r_t[topic][j]);
                    t_f_r_d[i][j] = f_r_d[i][j] + gd * lr_r;
                }
            }

            #pragma omp parallel for num_threads(64)
            for (int i = 0; i < W; i ++) {
                for (int k = 0; k < E_k; k ++) {
                    float gd = 0.0;
                    for (int l = 0; l < T; l ++) {
                        if (n_w_t[i][l] == 0) continue;
                        gd += n_w_t[i][l] * (- lambda_k_t[l][k]) * (f_k_w[i][k] - mu_k_t[l][k]);
                    }
                    t_f_k_w[i][k] = f_k_w[i][k] + gd * lr_k;
                }
            }

            float new_llh = temp_log_likelihood();

            if (new_llh < cur_llh) {
                lr_k *= decay;
                lr_r *= decay;
            }
            else {
                cur_llh = new_llh;

                #pragma omp parallel for num_threads(64)
                for (int i = 0; i < D; i ++) {
                    memcpy(f_r_d[i], t_f_r_d[i], sizeof(float) * E_r);
                }

                #pragma omp parallel for num_threads(64)
                for (int i = 0; i < W; i ++) {
                    memcpy(f_k_w[i], t_f_k_w[i], sizeof(float) * E_k);
                }
            }
        }
    }

    void learn() {
        for (int i = 0; i < learning_max_iter; i ++) {
            sprintf(temp, "##### learning #%d #####", i);
            logging(temp);

            sample_topics();

            // embedding_update();

            // stat_k_update();
            // stat_r_update();
        }

        parameter_update();
    }

    float predict(int r_id, int w_id) {
        float prob = -1e30;

        #pragma omp parallel for num_threads(20)
        for (int i = 0; i < T; i ++) {
            float cur = 0.0;
            for (int j = 0; j < E_r; j ++)
                cur += log_gaussian(f_r_d[r_id][j], mu_r_t[i][j], lambda_r_t[i][j]);
            for (int j = 0; j < E_k; j ++)
                cur += log_gaussian(f_k_w[w_id][j], mu_k_t[i][j], lambda_k_t[i][j]);
            // if (r_id == 0 && i == 0) cout << cur << endl;
            // cur = fastpow2(cur) * theta_d_t[r_id][i];
            cur += log2(theta_d_t[r_id][i]);
            ASSERT_VALNUM(cur);
            // prob += cur;
            prob = max(prob, cur);
        }
        return prob;
    }
};
