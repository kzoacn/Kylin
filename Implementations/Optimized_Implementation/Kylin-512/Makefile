CC ?= gcc
CFLAGS ?= -O3 -march=native -std=c99 -Wall -Wextra -Wpedantic
LDFLAGS ?=
INSTANCE = Kylin-512
TOOLS_DIR = ../../tools
BENCH_SOURCE = $(TOOLS_DIR)/bench_sig.c

COMMON_SOURCES = \
	SIG_AlgorithmInstance.c \
	kylin_sign.c \
	address.c \
	merkle.c \
	wots.c \
	wotsx1.c \
	utils.c \
	utilsx1.c \
	bpors.c \
	hash_iccs.c \
	thash_iccs.c \
	auxfunc.c \
	drng.c

.PHONY: all clean test kat bench stack_usage

all: KAT_SIG test_sig

KAT_SIG: KAT_SIG.c $(COMMON_SOURCES)
	$(CC) $(CFLAGS) -o $@ KAT_SIG.c $(COMMON_SOURCES) $(LDFLAGS)

test_sig: test_sig.c $(COMMON_SOURCES)
	$(CC) $(CFLAGS) -o $@ test_sig.c $(COMMON_SOURCES) $(LDFLAGS)

bench_sig: $(BENCH_SOURCE) $(COMMON_SOURCES)
	$(CC) $(CFLAGS) -I. -o $@ $(BENCH_SOURCE) $(COMMON_SOURCES) $(LDFLAGS)

test: test_sig
	./test_sig

bench: bench_sig
	./bench_sig

stack_usage:
	$(RM) -r .stack-usage
	mkdir -p .stack-usage
	for src in $(COMMON_SOURCES) $(BENCH_SOURCE); do \
		base=$${src##*/}; \
		base=$${base%.c}; \
		$(CC) $(CFLAGS) -I. -fstack-usage -c $$src -o .stack-usage/$$base.o; \
	done

kat: KAT_SIG
	./KAT_SIG
	mkdir -p ../../../Test_Vectors
	cp output/KAT_SIG_$(INSTANCE).txt ../../../Test_Vectors/

clean:
	$(RM) KAT_SIG test_sig bench_sig
	$(RM) -r output .stack-usage
