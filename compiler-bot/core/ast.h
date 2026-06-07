#ifndef AST_H
#define AST_H

typedef struct {
    char **entities;
    int    entity_count;
} ModuloEspec;

typedef struct {
    char **techs;
    int    tech_count;
} OpcionalTech;

typedef struct {
    char        *accion;
    char        *obj_tipo;
    ModuloEspec  objetivo;
    OpcionalTech techs;
} ASTNode;

void ast_free(ASTNode *ast);
void ast_free(ASTNode *ast) {
    if (!ast) return;
    if (ast->accion)    free(ast->accion);
    if (ast->obj_tipo)  free(ast->obj_tipo);
    for (int i = 0; i < ast->objetivo.entity_count; i++)
        free(ast->objetivo.entities[i]);
    free(ast->objetivo.entities);
    for (int i = 0; i < ast->techs.tech_count; i++)
        free(ast->techs.techs[i]);
    free(ast->techs.techs);
}

#endif
