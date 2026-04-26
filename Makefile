REF_DIRS := $(sort $(dir $(wildcard Implementations/Reference_Implementation/Kylin-*/Makefile)))
OPT_DIRS := $(sort $(dir $(wildcard Implementations/Optimized_Implementation/Kylin-*/Makefile)))
ADD_REF_DIRS := $(sort $(dir $(wildcard Implementations/Additional_Implementation/Reference_Implementation/Kylin-*/Makefile)))
ADD_OPT_DIRS := $(sort $(dir $(wildcard Implementations/Additional_Implementation/Optimized_Implementation/Kylin-*/Makefile)))
ALL_DIRS := $(REF_DIRS) $(OPT_DIRS) $(ADD_REF_DIRS) $(ADD_OPT_DIRS)
KAT_DIRS := $(REF_DIRS) $(ADD_REF_DIRS)

.PHONY: all build test kat metrics clean params verify

all: build

params:
	python3 paper/code/search_ngcc_params.py

build:
	@for d in $(ALL_DIRS); do \
		$(MAKE) -C $$d all; \
	done

test:
	@for d in $(ALL_DIRS); do \
		$(MAKE) -C $$d test; \
	done

kat:
	@for d in $(KAT_DIRS); do \
		$(MAKE) -C $$d kat; \
	done

metrics:
	python3 Implementations/tools/collect_metrics.py

clean:
	@for d in $(ALL_DIRS); do \
		$(MAKE) -C $$d clean; \
	done

verify: clean params build test kat metrics
