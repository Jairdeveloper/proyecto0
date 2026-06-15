import re
from .enriched_input import Entities, Entity


class NERExtractor:
    STOP_WORDS: set[str] = {
        "algo", "algun", "una", "uno", "este", "esta", "esto",
        "eso", "esa", "esos", "esas", "todo", "nada", "cada",
        "mismo", "propio", "simple", "basico",
    }

    TECH_WHITELIST: list[str] = [
        "nestjs", "prisma", "react", "vue", "nextjs", "nuxt",
        "express", "fastapi", "django", "flask", "spring",
        "postgres", "mysql", "mongodb", "redis", "sqlite",
        "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
        "stripe", "paypal", "jwt", "oauth", "tailwind",
        "graphql", "rest", "grpc", "rabbitmq", "kafka",
    ]

    REQUIREMENT_PATTERNS: list[tuple[str, str]] = [
        (r"con\s+(autenticacion\s+\w+)", "autenticacion"),
        (r"con\s+(cache)", "cache"),
        (r"con\s+(\w+)", "integracion"),
        (r"que tenga\s+([\w\s]+?)(?:$| y |,)", "requisito"),
        (r"usando\s+([\w\s]+?)(?:$| y |,)", "tecnologia"),
        (r"sin\s+([\w\s]+?)(?:$| y |,)", "negacion"),
        (r"integrado con\s+(\w+)", "integracion"),
        (r"que soporte\s+([\w\s]+?)(?:$| y |,)", "requisito"),
    ]

    def extract(self, text: str) -> Entities:
        text_lower = text.lower()
        return Entities(
            modulos=self._extract_modules(text_lower),
            techs=self._extract_techs(text_lower),
            requisitos=self._extract_requirements(text_lower),
        )

    def _extract_modules(self, text: str) -> list[Entity]:
        entities: list[Entity] = []
        for match in re.finditer(
            r"(?:modulo\s+de\s+(\w+)|entidad\s+(\w+)|sistema\s+de\s+(\w+))",
            text,
        ):
            name = next(g for g in match.groups() if g)
            entities.append(Entity(nombre=name, tipo="module"))
        if not entities:
            for match in re.finditer(
                r"(?:crea|genera|nuevo|borra|elimina)\s+(?:un\s+)?(?:modulo\s+)?(?:de\s+)?(\w+)",
                text,
            ):
                name = match.group(1)
                if name not in self.TECH_WHITELIST and name not in self.STOP_WORDS:
                    entities.append(Entity(nombre=name, tipo="module"))
        return entities

    def _extract_techs(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        for tech in self.TECH_WHITELIST:
            if tech in text:
                found.append(Entity(nombre=tech, tipo="tech", rol=tech))
        return found

    def _extract_requirements(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        for pattern, tipo in self.REQUIREMENT_PATTERNS:
            for match in re.finditer(pattern, text):
                valor = match.group(1).strip()
                is_neg = "sin" in pattern or "negacion" in tipo
                found.append(Entity(
                    nombre=valor, tipo=tipo, rol=tipo, negado=is_neg,
                ))
        return found
