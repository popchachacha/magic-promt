"""Entry point for the Magic Prompt UI."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

try:  # noqa: SIM105
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]

from prompt_graph import default_graph
from ui.localization import Translator

if QApplication is not None:
    from ui.main_window import MainWindow, run_headless  # type: ignore
    from ui.theme import build_stylesheet  # type: ignore
else:  # pragma: no cover
    MainWindow = None  # type: ignore[assignment]
    run_headless = None  # type: ignore[assignment]

    def build_stylesheet() -> str:
        raise RuntimeError("PySide6 is required for stylesheet generation")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Magic Prompt UI")
    parser.add_argument("--lang", choices=["ru", "en"], default="ru", help="Interface language")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a headless smoke test to ensure UI components instantiate",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force Qt into offscreen mode (useful for CI or WSL).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if QApplication is None:
        print("PySide6 is not installed. Please run `pip install PySide6` before launching the UI.")
        return 1

    if args.headless:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    translator = Translator(args.lang)
    graph = default_graph()
    stylesheet = build_stylesheet()

    if args.smoke:
        def factory() -> MainWindow:
            window = MainWindow(graph, translator)
            window.setStyleSheet(stylesheet)
            return window

        ok, message = run_headless(factory)
        print(message)
        return 0 if ok else 2

    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    window = MainWindow(graph, translator)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
