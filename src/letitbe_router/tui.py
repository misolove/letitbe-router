"""Tiny terminal menu renderer for lr server control."""

from __future__ import annotations

from letitbe_router import __version__


def render_tui_menu(*, base_url: str = "http://localhost:20128") -> str:
    return f"""========================================
  Choose Interface (lr v{__version__})
  Server: {base_url}
========================================

 ★ OpenAI API (Custom base URL: {base_url}/v1)
  ☆ Terminal UI (Interactive CLI)
  ☆ Hide to Background (lr daemon start)
  ☆ Exit
"""
