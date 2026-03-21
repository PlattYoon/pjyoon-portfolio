CC=gcc -std=c99 -pedantic
FAST_FLAGS=-Wall -Wextra -Werror -Wshadow -g -O3
SAFE_FLAGS=-Wall -Wextra -Werror -Wshadow -g -fsanitize=undefined -DDEBUG

LIB= lib/*.o
SAFE_LIB=$(LIB:%.o=%-safe.o)
FAST_LIB=$(LIB:%.o=%-fast.o)

BDICT_LIB=lib/boardutil-safe.o lib/hdict-safe.o lib/queue-safe.o

BITVECTOR=bitvector.c bitvector-test.c
BDICT    =bitvector.c bdict.c bdict-test.c
MOVES    =bitvector.c bdict.c lightsout.c move-test.c
LIGHTSOUT=bitvector.c bdict.c lightsout.c

.PHONY: lightsout lightsout-d bitvector-test bdict-test clean
#
default: lightsout lightsout-d

bitvector-test: $(BITVECTOR)
	@$(CC) $(SAFE_FLAGS) $? -o $@

bdict-test: $(BDICT_LIB) $(BDICT)
	@$(CC) $(SAFE_FLAGS) $? -o $@

move-test: $(SAFE_LIB) $(MOVES)
	@$(CC) $(SAFE_FLAGS) $? -o $@

lightsout: $(FAST_LIB) $(LIGHTSOUT) lightsout-main-fast.o
	@$(CC) $(FAST_FLAGS) $? -o $@

lightsout-d: $(SAFE_LIB) $(LIGHTSOUT) lightsout-main-safe.o
	@$(CC) $(SAFE_FLAGS) $? -o $@

lightsout-fast: $(FAST_LIB) bitvector-large.c bdict.c lightsout-fast.c
	@$(CC) $(FAST_FLAGS) $? -o $@


help:
	@echo "make bitvector-test   -- compile bit vector tests"
	@echo "make bdict-test       -- compile bit vector dictionary tests"
	@echo "make move-test        -- compile moves tests"
	@echo "make lightsout        -- compile lightsout"
	@echo "make lightsout-d      -- compile lightsout with contracts on"
	@echo "make lightsout-fast   -- compile large bit vector tests"
	@echo "make clean            -- remove executables"
	@echo "make help             -- show this message"


clean:
	@rm -Rf bitvector-test bdict-test move-test                            \
                lightsout lightsout-d lightsout-fast                           \
                *.dSYM
