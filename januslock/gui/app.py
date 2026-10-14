"""
app.py — Tkinter front-end for Janus Lock.

This module is intentionally thin: it wires widgets to the same
functions the CLI uses. No crypto or file logic lives here.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from januslock import storage
from januslock.gui import theme

# --- Paths ---
# Project root = three levels up from this file:
# januslock/gui/app.py → januslock/gui → januslock → repo root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ICON_PATH = _PROJECT_ROOT / "assets" / "favicon.ico"

class JanusLockApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Janus Lock")
        self._apply_icon()
        self.root.geometry("640x480")
        self.root.minsize(640, 400)

        theme.apply(self.root)
        self._center_window()






        # --- State ---
        # These three only exist while a vault is unlocked.
        # When we lock, we clear them — the key never lingers longer than needed.
        self.vault_path: Path | None = None
        self.key: bytes | None = None
        self.salt: bytes | None = None

        self._build_ui()

    # ---------- window placement ----------

    def _center_window(self) -> None:
        """Center the window on the primary display at startup."""
        self.root.update_idletasks()

        win_w = self.root.winfo_width()
        win_h = self.root.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2

        self.root.geometry(f"+{x}+{y}")

    def _apply_icon(self) -> None:
        """Set the window icon if the .ico file exists.

        Silently skips on non-Windows platforms or if the file is
        missing — an icon is a nicety, not a startup requirement.
        """
        if not ICON_PATH.exists():
            return
        try:
            self.root.iconbitmap(default=str(ICON_PATH))
        except tk.TclError:
            # Not Windows, or the .ico is malformed.
            pass
    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        # Root grid: 3 rows. Row 1 (text area) gets all the extra
        # vertical space; toolbar and status bar stay at natural height.
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Toolbar (row 0) ---
        toolbar = ttk.Frame(self.root, padding=theme.PAD["md"])
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="New Vault", command=self.on_new).pack(
            side=tk.LEFT
        )
        ttk.Button(toolbar, text="Open Vault", command=self.on_open).pack(
            side=tk.LEFT, padx=(theme.PAD["sm"], 0)
        )
        ttk.Button(toolbar, text="Save", command=self.on_save).pack(
            side=tk.LEFT, padx=(theme.PAD["sm"], 0)
        )
        ttk.Button(toolbar, text="Lock", command=self.on_lock).pack(
            side=tk.LEFT, padx=(theme.PAD["sm"], 0)
        )

        # --- Text area (row 1, expands) ---
        # A Frame holds the Text and its Scrollbar side by side.
        editor = ttk.Frame(self.root)
        editor.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=theme.PAD["md"],
            pady=(0, theme.PAD["md"]),
        )
        editor.grid_rowconfigure(0, weight=1)
        editor.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(editor, wrap="word", undo=True, font=("Consolas", 11))
        self.text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(editor, orient=tk.VERTICAL, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set, state=tk.DISABLED)

        # --- Status bar (row 2) ---
        self.status = tk.StringVar(
            value="No vault open. Create one or open an existing vault."
        )
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(theme.PAD["md"], theme.PAD["sm"]),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    # ---------- helpers ----------

    def _set_editable(self, editable: bool) -> None:
        self.text.configure(state=tk.NORMAL if editable else tk.DISABLED)

    def _reset_state(self) -> None:
        """Wipe in-memory secrets and disable the editor."""
        self.vault_path = None
        self.key = None
        self.salt = None
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)

    def _ask_password(self, title: str, prompt: str) -> str | None:
        """Modal password prompt. Returns None if the user cancels."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        result: dict[str, str | None] = {"value": None}

        ttk.Label(dialog, text=prompt, padding=(12, 12, 12, 4)).pack(anchor="w")
        pw_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=pw_var, show="•", width=40)
        entry.pack(padx=12, pady=(0, 8))
        entry.focus_set()

        def on_ok() -> None:
            result["value"] = pw_var.get()
            dialog.destroy()

        def on_cancel() -> None:
            result["value"] = None
            dialog.destroy()

        buttons = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(0, 6))

        dialog.bind("<Return>", lambda _e: on_ok())
        dialog.bind("<Escape>", lambda _e: on_cancel())

        # Center the dialog over the main window.
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 3
        dialog.geometry(f"+{x}+{y}")

        self.root.wait_window(dialog)
        return result["value"]

    # ---------- actions ----------

    def on_new(self) -> None:
        path_str = filedialog.asksaveasfilename(
            title="Create new vault",
            defaultextension=".janus",
            filetypes=[("Janus Lock vault", "*.janus"), ("All files", "*.*")],
        )
        if not path_str:
            return

        path = Path(path_str)
        password = self._ask_password("New vault", "Choose a master password:")
        if password is None:
            return
        if not password:
            messagebox.showerror("Janus Lock", "Password can't be empty.")
            return
        confirm = self._ask_password("New vault", "Confirm master password:")
        if confirm != password:
            messagebox.showerror("Janus Lock", "Passwords don't match.")
            return

        try:
            key, salt = storage.create_vault(path, password)
        except Exception as exc:
            messagebox.showerror("Janus Lock", f"Could not create vault:\n{exc}")
            return

        self.vault_path, self.key, self.salt = path, key, salt
        self._set_editable(True)
        self.text.delete("1.0", tk.END)
        self.status.set(f"Unlocked: {path.name}  (empty)")
        self.text.focus_set()

    def on_open(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Open vault",
            filetypes=[("Janus Lock vault", "*.janus"), ("All files", "*.*")],
        )
        if not path_str:
            return

        path = Path(path_str)
        password = self._ask_password("Unlock vault", f"Master password for {path.name}:")
        if password is None:
            return

        try:
            plaintext, key, salt = storage.load_vault(path, password)
        except Exception:
            # Same vague message as the CLI.
            messagebox.showerror("Janus Lock", "Wrong password or corrupted vault.")
            return

        self.vault_path, self.key, self.salt = path, key, salt
        self._set_editable(True)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", plaintext.decode("utf-8", errors="replace"))
        self.status.set(f"Unlocked: {path.name}")

    def on_save(self) -> None:
        if not self._is_unlocked():
            messagebox.showinfo("Janus Lock", "Open or create a vault first.")
            return

        contents = self.text.get("1.0", "end-1c").encode("utf-8")
        try:
            storage.save_vault(self.vault_path, contents, self.key, self.salt)
        except Exception as exc:
            messagebox.showerror("Janus Lock", f"Could not save:\n{exc}")
            return

        self.status.set(f"Saved: {self.vault_path.name}")

    def on_lock(self) -> None:
        if not self._is_unlocked():
            return
        self._reset_state()
        self.status.set("Locked. No vault open.")

    def _is_unlocked(self) -> bool:
        return self.key is not None and self.vault_path is not None


def main() -> None:
    root = tk.Tk()
    JanusLockApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()