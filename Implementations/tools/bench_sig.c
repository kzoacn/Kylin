#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#include "SIG_AlgorithmInstance.h"
#include "drng.h"

#define MSG_LEN 32U
#define WARMUP_ITERS 0
#define MEASURE_ITERS 1

DRNG_ctx drng_algorithm;

static double now_ms(void)
{
    struct timeval tv;

    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec * 1000.0 + (double)tv.tv_usec / 1000.0;
}

static int cmp_double(const void *lhs, const void *rhs)
{
    const double a = *(const double *)lhs;
    const double b = *(const double *)rhs;

    return (a > b) - (a < b);
}

static double median(double *samples, size_t count)
{
    qsort(samples, count, sizeof(*samples), cmp_double);
    if ((count & 1U) != 0U) {
        return samples[count / 2U];
    }
    return (samples[count / 2U - 1U] + samples[count / 2U]) / 2.0;
}

static int run_keygen(unsigned char *pk, unsigned char *sk,
    unsigned long long *pk_len, unsigned long long *sk_len)
{
    return sig_keygen(pk, pk_len, sk, sk_len);
}

static int run_sign(unsigned char *sk, unsigned long long sk_len,
    unsigned char *msg, unsigned long long msg_len,
    unsigned char *sig, unsigned long long *sig_len)
{
    return sig_sign(sk, sk_len, msg, msg_len, sig, sig_len);
}

static int run_verify(unsigned char *pk, unsigned long long pk_len,
    unsigned char *sig, unsigned long long sig_len,
    unsigned char *msg, unsigned long long msg_len)
{
    return sig_verify(pk, pk_len, sig, sig_len, msg, msg_len);
}

int main(void)
{
    unsigned long long pk_len = sig_get_pk_len_bytes();
    unsigned long long sk_len = sig_get_sk_len_bytes();
    unsigned long long sig_len = sig_get_sn_len_bytes();
    unsigned char *pk = malloc((size_t)pk_len);
    unsigned char *sk = malloc((size_t)sk_len);
    unsigned char *sig = malloc((size_t)sig_len);
    unsigned char msg[MSG_LEN];
    double keygen_samples[MEASURE_ITERS];
    double sign_samples[MEASURE_ITERS];
    double verify_samples[MEASURE_ITERS];
    unsigned char seed[64];
    size_t i;

    if (pk == NULL || sk == NULL || sig == NULL) {
        fprintf(stderr, "allocation failed\n");
        free(pk);
        free(sk);
        free(sig);
        return 1;
    }

    for (i = 0; i < MSG_LEN; i++) {
        msg[i] = (unsigned char)(0xA5U ^ (unsigned char)i);
    }
    memset(seed, 0x42, sizeof(seed));

    if (init_random_number(&drng_algorithm, seed, sizeof(seed)) != 0) {
        fprintf(stderr, "DRNG initialization failed\n");
        free(pk);
        free(sk);
        free(sig);
        return 1;
    }

    for (i = 0; i < WARMUP_ITERS; i++) {
        unsigned long long out_pk_len = 0;
        unsigned long long out_sk_len = 0;
        unsigned long long out_sig_len = 0;

        if (run_keygen(pk, sk, &out_pk_len, &out_sk_len) != 0) {
            fprintf(stderr, "warmup keygen failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }
        if (run_sign(sk, out_sk_len, msg, MSG_LEN, sig, &out_sig_len) != 0) {
            fprintf(stderr, "warmup sign failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }
        if (run_verify(pk, out_pk_len, sig, out_sig_len, msg, MSG_LEN) != 0) {
            fprintf(stderr, "warmup verify failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }
    }

    for (i = 0; i < MEASURE_ITERS; i++) {
        unsigned long long out_pk_len = 0;
        unsigned long long out_sk_len = 0;
        double start = now_ms();

        if (run_keygen(pk, sk, &out_pk_len, &out_sk_len) != 0) {
            fprintf(stderr, "keygen failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }

        keygen_samples[i] = now_ms() - start;
    }

    if (run_keygen(pk, sk, &pk_len, &sk_len) != 0) {
        fprintf(stderr, "setup keygen failed\n");
        free(pk);
        free(sk);
        free(sig);
        return 1;
    }

    for (i = 0; i < MEASURE_ITERS; i++) {
        unsigned long long out_sig_len = 0;
        double start = now_ms();

        if (run_sign(sk, sk_len, msg, MSG_LEN, sig, &out_sig_len) != 0) {
            fprintf(stderr, "sign failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }

        sign_samples[i] = now_ms() - start;
        sig_len = out_sig_len;
    }

    if (run_sign(sk, sk_len, msg, MSG_LEN, sig, &sig_len) != 0) {
        fprintf(stderr, "setup sign failed\n");
        free(pk);
        free(sk);
        free(sig);
        return 1;
    }

    for (i = 0; i < MEASURE_ITERS; i++) {
        double start = now_ms();

        if (run_verify(pk, pk_len, sig, sig_len, msg, MSG_LEN) != 0) {
            fprintf(stderr, "verify failed\n");
            free(pk);
            free(sk);
            free(sig);
            return 1;
        }

        verify_samples[i] = now_ms() - start;
    }

    printf("instance=%s\n", ALGORITHM_INSTANCE);
    printf("message_bytes=%u\n", MSG_LEN);
    printf("iterations=%u\n", MEASURE_ITERS);
    printf("keygen_ms=%.3f\n", median(keygen_samples, MEASURE_ITERS));
    printf("sign_ms=%.3f\n", median(sign_samples, MEASURE_ITERS));
    printf("verify_ms=%.3f\n", median(verify_samples, MEASURE_ITERS));
    printf("pk_bytes=%llu\n", pk_len);
    printf("sk_bytes=%llu\n", sk_len);
    printf("sig_bytes=%llu\n", sig_len);

    free(pk);
    free(sk);
    free(sig);
    return 0;
}
