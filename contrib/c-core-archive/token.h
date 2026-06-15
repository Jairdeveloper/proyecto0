#ifndef TOKEN_H
#define TOKEN_H

typedef enum {
    TOKEN_UNKNOWN = 0,
    TOKEN_ACTION_CREATE,
    TOKEN_ACTION_DELETE,
    TOKEN_ACTION_UPDATE,
    TOKEN_ACTION_READ,
    TOKEN_MODULE,
    TOKEN_ENTITY,
    TOKEN_TECH_NESTJS,
    TOKEN_TECH_PRISMA,
    TOKEN_TECH_EXPRESS,
    TOKEN_TECH_FASTAPI,
    TOKEN_TECH_REACT,
    TOKEN_TECH_VUE,
    TOKEN_TECH_POSTGRES,
    TOKEN_TECH_MONGODB,
    TOKEN_TECH_DOCKER,
    TOKEN_TECH_K8S,
    TOKEN_TECH_GRAPHQL,
    TOKEN_TECH_NEXT,
    TOKEN_TECH_DJANGO,
    TOKEN_TECH_FLASK,
    TOKEN_TECH_SPRING,
    TOKEN_TECH_GIN,
    TOKEN_TECH_SVELTE,
    TOKEN_PREP_IN,
    TOKEN_SEPARATOR,
    TOKEN_EOF,
    TOKEN_ERROR
} TokenType;

typedef struct {
    TokenType type;
    char     *lexeme;
    int       line;
    int       col;
} Token;

const char *token_type_name(TokenType t);
const char *token_type_name(TokenType t) {
    switch (t) {
        case TOKEN_UNKNOWN:       return "UNKNOWN";
        case TOKEN_ACTION_CREATE: return "ACTION_CREATE";
        case TOKEN_ACTION_DELETE: return "ACTION_DELETE";
        case TOKEN_ACTION_UPDATE: return "ACTION_UPDATE";
        case TOKEN_ACTION_READ:   return "ACTION_READ";
        case TOKEN_MODULE:        return "MODULE";
        case TOKEN_ENTITY:        return "ENTITY";
        case TOKEN_TECH_NESTJS:   return "TECH_NESTJS";
        case TOKEN_TECH_PRISMA:   return "TECH_PRISMA";
        case TOKEN_TECH_EXPRESS:  return "TECH_EXPRESS";
        case TOKEN_TECH_FASTAPI:  return "TECH_FASTAPI";
        case TOKEN_TECH_REACT:    return "TECH_REACT";
        case TOKEN_TECH_VUE:      return "TECH_VUE";
        case TOKEN_TECH_POSTGRES: return "TECH_POSTGRES";
        case TOKEN_TECH_MONGODB:  return "TECH_MONGODB";
        case TOKEN_TECH_DOCKER:   return "TECH_DOCKER";
        case TOKEN_TECH_K8S:      return "TECH_K8S";
        case TOKEN_TECH_GRAPHQL:  return "TECH_GRAPHQL";
        case TOKEN_TECH_NEXT:     return "TECH_NEXT";
        case TOKEN_TECH_DJANGO:   return "TECH_DJANGO";
        case TOKEN_TECH_FLASK:    return "TECH_FLASK";
        case TOKEN_TECH_SPRING:   return "TECH_SPRING";
        case TOKEN_TECH_GIN:      return "TECH_GIN";
        case TOKEN_TECH_SVELTE:   return "TECH_SVELTE";
        case TOKEN_PREP_IN:       return "PREP_IN";
        case TOKEN_SEPARATOR:     return "SEPARATOR";
        case TOKEN_EOF:           return "EOF";
        case TOKEN_ERROR:         return "ERROR";
    }
    return "?";
}

#endif
