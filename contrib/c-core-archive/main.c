#include "common.h"
#include "token.h"

#include <stdio.h>
#include <string.h>

static void print_usage(void) {
    fprintf(stderr, "Usage: recpl-core --mode=<mode>\n");
    fprintf(stderr, "Modes: preprocess, lex, parse, semantic, ir, full\n");
}

static int mode_preprocess(void) {
    fprintf(stdout, "mode preprocess: not implemented yet\n");
    return 0;
}

static int mode_lex(void) {
    fprintf(stdout, "mode lex: not implemented yet\n");
    return 0;
}

static int mode_parse(void) {
    fprintf(stdout, "mode parse: not implemented yet\n");
    return 0;
}

static int mode_semantic(void) {
    fprintf(stdout, "mode semantic: not implemented yet\n");
    return 0;
}

static int mode_ir(void) {
    fprintf(stdout, "mode ir: not implemented yet\n");
    return 0;
}

static int mode_full(void) {
    fprintf(stdout, "mode full: not implemented yet\n");
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage();
        return 1;
    }

    const char *mode = parse_flag(argv, "--mode");
    if (!mode) {
        fprintf(stderr, "Error: --mode is required\n");
        print_usage();
        return 1;
    }

    if (strcmp(mode, "preprocess") == 0) return mode_preprocess();
    if (strcmp(mode, "lex") == 0)         return mode_lex();
    if (strcmp(mode, "parse") == 0)       return mode_parse();
    if (strcmp(mode, "semantic") == 0)    return mode_semantic();
    if (strcmp(mode, "ir") == 0)          return mode_ir();
    if (strcmp(mode, "full") == 0)        return mode_full();

    fprintf(stderr, "Unknown mode: %s\n", mode);
    return 1;
}
