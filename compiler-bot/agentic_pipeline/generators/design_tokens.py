"""DesignTokens — centralized design system tokens for UI generation."""


class DesignTokens:
    COLORS = {
        "primary": "#6366F1",
        "secondary": "#10B981",
        "background": "#FFFFFF",
        "surface": "#F9FAFB",
        "text": "#111827",
        "text_secondary": "#6B7280",
        "border": "#E5E7EB",
        "error": "#EF4444",
    }

    FONTS = {
        "sans": "'Inter', sans-serif",
        "mono": "'JetBrains Mono', monospace",
    }

    BORDER_RADIUS = "8px"

    SPACING = {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "48px",
    }

    BREAKPOINTS = {
        "sm": "640px",
        "md": "768px",
        "lg": "1024px",
        "xl": "1280px",
    }

    @classmethod
    def as_css_vars(cls) -> str:
        lines = [":root {"]
        for key, val in cls.COLORS.items():
            lines.append(f"  --color-{key}: {val};")
        lines.append(f"  --font-sans: {cls.FONTS['sans']};")
        lines.append(f"  --font-mono: {cls.FONTS['mono']};")
        lines.append(f"  --radius: {cls.BORDER_RADIUS};")
        for key, val in cls.SPACING.items():
            lines.append(f"  --space-{key}: {val};")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def tailwind_config(cls) -> dict:
        return {
            "colors": {
                "primary": cls.COLORS["primary"],
                "secondary": cls.COLORS["secondary"],
                "surface": cls.COLORS["surface"],
                "border": cls.COLORS["border"],
                "error": cls.COLORS["error"],
            },
            "fontFamily": {
                "sans": [cls.FONTS["sans"]],
                "mono": [cls.FONTS["mono"]],
            },
            "borderRadius": {
                "DEFAULT": cls.BORDER_RADIUS,
            },
            "spacing": cls.SPACING,
        }

    @classmethod
    def css(cls) -> str:
        return cls.as_css_vars()
