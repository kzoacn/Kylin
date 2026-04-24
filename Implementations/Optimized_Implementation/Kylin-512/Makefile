CC ?= gcc
CFLAGS ?= -O3 -march=native -std=c99 -Wall -Wextra -Wpedantic
LDFLAGS ?=
INSTANCE = Kylin-512

COMMON_SOURCES = \
	SIG_AlgorithmInstance.c \
	kylin_sign.c \
	address.c \
	merkle.c \
	wots.c \
	wotsx1.c \
	utils.c \
	utilsx1.c \
	fors.c \
	hash_iccs.c \
	thash_iccs.c \
	auxfunc.c \
	drng.c

.PHONY: all clean test kat

all: KAT_SIG test_sig

KAT_SIG: KAT_SIG.c $(COMMON_SOURCES)
	$(CC) $(CFLAGS) -o $@ KAT_SIG.c $(COMMON_SOURCES) $(LDFLAGS)

test_sig: test_sig.c $(COMMON_SOURCES)
	$(CC) $(CFLAGS) -o $@ test_sig.c $(COMMON_SOURCES) $(LDFLAGS)

test: test_sig
	./test_sig

kat: KAT_SIG
	./KAT_SIG
	mkdir -p ../../../Test_Vectors
	cp output/KAT_SIG_$(INSTANCE).txt ../../../Test_Vectors/

clean:
	$(RM) KAT_SIG test_sig
	$(RM) -r output
