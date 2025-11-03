import json
from pathlib import Path
from typing import Any, Dict


class Translator:
    """Simple JSON-backed localization loader."""

    def __init__(self, language: str, locales_dir: Path | None = None) -> None:
        self.language = language
        self.locales_dir = locales_dir or Path(__file__).resolve().parent.parent / "locales"
        self._strings = self._load_strings()

    def _load_strings(self) -> Dict[str, Any]:
        file_path = self.locales_dir / f"{self.language}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Locale file not found: {file_path}")
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def get(self, path: str, default: str | None = None) -> str:
        """
        Retrieve a localized string by path (dot-separated).

        Example: translator.get("sidebar.heading")
        """
        current: Any = self._strings
        for key in path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                if default is not None:
                    return default
                raise KeyError(f"Missing translation for '{path}' in '{self.language}' locale")
        if isinstance(current, str):
            return current
        raise ValueError(f"Translation at '{path}' is not a string: {current!r}")
