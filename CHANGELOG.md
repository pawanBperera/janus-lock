# Changelog

All notable changes to Janus Lock are documented here.
This project follows [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-10-12

A UI/UX pass focused on visual polish and layout. No changes to
`crypto.py` or `storage.py` — the backend is unchanged and the
on-disk vault format is identical to v0.1.0.

### Changed

- Split `januslock/gui.py` into a `januslock/gui/` package
  (`app.py`, `theme.py`, and `__init__.py`).
- Centralized ttk theming and font sizing in `theme.py`.
  Applies the platform-preferred ttk theme (`vista` on Windows,
  with fallbacks) and configures Tkinter's global named fonts.
- Migrated the main window layout from `pack()` to `grid()` with a
  shared spacing scale (`theme.PAD`), so padding is consistent and
  centrally tunable.
- The main window now centers itself on the primary display at
  startup.
- Raised the window minimum size from 480×360 to 640×400 to keep
  the toolbar and text area usable at the floor.

### Added

- `januslock/gui/theme.py` — ttk style and named-font setup, plus
  the `PAD` spacing scale.
- `JanusLockApp._center_window()` — centers the window on launch.

### Removed

- Duplicate `from januslock import storage` import in the GUI
  module.

## [0.1.0] - 2026-10-01

Initial release.

- Create, open, edit, save, and lock encrypted `.janus` vaults
  from a Tkinter GUI or a small CLI.
- scrypt key derivation, AES-GCM encryption, atomic saves.
- Vague error messages on decryption failure (no info leak between
  "wrong password" and "corrupted file").