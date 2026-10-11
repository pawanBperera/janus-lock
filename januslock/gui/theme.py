"""
theme.py — centralized ttk styling and font configuration.

Call `apply(root)` once at app startup. All style decisions live
here so the rest of the GUI code stays focused on layout and
behavior.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


# Spacing scale, in pixels. Layout code should use these names
# instead of raw numbers so the visual rhythm stays consistent.
PAD = {
    "xs": 2,
    "sm": 4,
    "md": 8,
    "lg": 16,
    "xl": 24,
}


def apply(root: tk.Misc) -> None:
    """Apply the ttk theme and global font sizes to the app."""
    style = ttk.Style(root)

    # Prefer the native Windows theme; fall back gracefully.
    available = style.theme_names()
    for name in ("vista", "winnative", "clam", "default"):
        if name in available:
            style.theme_use(name)
            break

    # Set global named fonts. Anything not overriding the font
    # explicitly will pick these up automatically.
    defaults = [
        ("TkDefaultFont", 10),
        ("TkTextFont", 10),
        ("TkMenuFont", 10),
        ("TkHeadingFont", 10, "bold"),
    ]
    for spec in defaults:
        name, size, *rest = spec
        weight = rest[0] if rest else "normal"
        tkfont.nametofont(name).configure(size=size, weight=weight)