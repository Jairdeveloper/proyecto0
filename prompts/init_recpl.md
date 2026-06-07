Inicia el flujo de delegacion del bot RECPL.

## Instrucciones

1. Lee los agentes en `.opencode/agents/`:
   - `orquestador1-delega.md`
   - `orquestador2-delega.md`
   - `orquestador3-generador.md`
2. Lee las especificaciones en `docs/`:
   - `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md`
   - `007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md`
3. Lee `AGENTS.md` para reglas del proyecto.
4. Invoca a **Orquestador1** como punto de entrada de la cadena de delegacion.
5. Orquestador1 debe:
   - Crear el mapa de ejecucion (DONDE/QUE/CUANDO/QUIEN/COMO)
   - Delegar a Orquestador3 la generacion de prompts para cada tarea
   - Recibir los prompts y pasarlos a Orquestador2 para ejecucion
   - Recibir los reportes de Orquestador2 y validar resultados
6. Sigue el pipeline completo: FASE-1 → FASE-2 → FASE-3 → FASE-4 → FASE-5
7. Reporta el estado final de cada tarea y fase al terminar.
