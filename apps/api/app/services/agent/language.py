from app.core.config import Settings


def detect_language(message: str, settings: Settings, explicit_language: str | None = None) -> str:
    if explicit_language and explicit_language in settings.supported_language_list:
        return explicit_language

    lowered = message.lower()
    if any(token in lowered for token in ("šta", "kako", "gde", "veštine", "iskustvo", "dostupnost")):
        return "sr" if "sr" in settings.supported_language_list else settings.default_language
    if any(token in lowered for token in ("fähigkeiten", "erfahrung", "verfügbarkeit", "können sie")):
        return "de" if "de" in settings.supported_language_list else settings.default_language
    return settings.default_language
