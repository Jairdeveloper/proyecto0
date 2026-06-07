CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic -Werror
OPT     ?= -O2
DEBUG   ?= -g -DDEBUG
LIBS    := -lm

SRC := $(wildcard *.c)
OBJ := $(SRC:.c=.o)
TARGET := recpl-core

.PHONY: all release debug test clean

all: release

release: CFLAGS += $(OPT)
release: $(TARGET)

debug: CFLAGS += $(DEBUG)
debug: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

test: debug
	@echo "=== Running tests ==="
	@mkdir -p test_output
	@./run_tests.sh 2>&1 || true

clean:
	rm -f $(OBJ) $(TARGET) test_output/*
