import os
import shutil
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# VLC playback
import vlc   # pip install python-vlc

# ------------ CONFIG ------------
LIBRARY_ROOT = Path("library") / "audio"   # matches your folder naming
CATEGORIES = [
    ("💪 Gym", "gym"),
    ("💰 Luxury", "luxury"),
    ("😌 Calm", "calm"),
    ("😊 Uplifting", "uplifting"),
    ("🎭 Dramatic", "dramatic"),
    ("📦 Generic", "generic"),
]
EXTS = (".mp3", ".wav", ".m4a", ".flac", ".ogg")
# --------------------------------

class AudioSorter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Sorter – simple & reliable")
        self.geometry("780x320")
        self.resizable(False, False)

        # VLC player
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.files = []
        self.idx = 0
        self.copied_log = set()  # track originals we've copied (for cleanup)

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        top = tk.Frame(self, padx=10, pady=8)
        top.pack(fill="x")

        tk.Label(top, text="1) Pick your audio folder →", font=("Segoe UI", 10)).pack(side="left")
        tk.Button(top, text="Choose Folder", command=self.choose_folder).pack(side="left", padx=8)

        self.progress_var = tk.StringVar(value="0/0 (0%)")
        tk.Label(top, textvariable=self.progress_var, fg="#888").pack(side="right")

        middle = tk.Frame(self, padx=10, pady=4)
        middle.pack(fill="x")

        self.file_label = tk.Label(middle, text="No file loaded yet.", font=("Segoe UI", 12, "bold"))
        self.file_label.pack(fill="x")

        self.status_var = tk.StringVar(value="Pick a folder to start.")
        tk.Label(middle, textvariable=self.status_var, fg="#2a8").pack(anchor="w")

        controls = tk.Frame(self, padx=10, pady=6)
        controls.pack(fill="x")

        tk.Button(controls, text="▶ Play/Pause", width=14, command=self.toggle_play).pack(side="left")
        tk.Button(controls, text="⏭ Skip", width=10, command=self.skip_file).pack(side="left", padx=6)
        tk.Button(controls, text="🗑 Cleanup originals (copied only)", command=self.cleanup_copied).pack(side="right")

        # Categories
        grid = tk.Frame(self, padx=10, pady=8)
        grid.pack(fill="both", expand=True)

        # 2 columns
        for r, pair in enumerate(CATEGORIES):
            if r % 2 == 0:
                row = tk.Frame(grid)
                row.pack(fill="x", pady=4)
            label, folder = pair
            btn = tk.Button(row, text=f"{label}\n→ {folder}",
                            width=36, height=2,
                            command=lambda f=folder: self.copy_to_category(f))
            btn.pack(side="left", padx=6)

        # Hotkeys (1..6)
        self.bind("1", lambda e: self.copy_to_category(CATEGORIES[0][1]))
        self.bind("2", lambda e: self.copy_to_category(CATEGORIES[1][1]))
        self.bind("3", lambda e: self.copy_to_category(CATEGORIES[2][1]))
        self.bind("4", lambda e: self.copy_to_category(CATEGORIES[3][1]))
        self.bind("5", lambda e: self.copy_to_category(CATEGORIES[4][1]))
        self.bind("6", lambda e: self.copy_to_category(CATEGORIES[5][1]))
        self.bind("<space>", lambda e: self.toggle_play())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Core flow ----------
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select folder with audio files")
        if not folder:
            return
        p = Path(folder)
        self.files = sorted([x for x in p.iterdir() if x.suffix.lower() in EXTS])
        self.idx = 0
        if not self.files:
            messagebox.showwarning("No Files", "No audio files found in that folder.")
            return
        self._ensure_category_folders()
        self.load_current()

    def _ensure_category_folders(self):
        for _, slug in CATEGORIES:
            (LIBRARY_ROOT / slug).mkdir(parents=True, exist_ok=True)

    def load_current(self):
        if self.idx >= len(self.files):
            self.status_var.set("🎉 All done!")
            self.file_label.config(text="No more files.")
            self.progress_var.set(f"{len(self.files)}/{len(self.files)} (100%)")
            self.stop_playback()
            return

        f = self.files[self.idx]
        self.file_label.config(text=f"File {self.idx+1}/{len(self.files)} — {f.name}")
        pct = int(self.idx * 100 / max(1, len(self.files)))
        self.progress_var.set(f"{self.idx}/{len(self.files)} ({pct}%)")

        # Start VLC on the ORIGINAL file (VLC plays without blocking our copy)
        self.stop_playback()
        media = self.instance.media_new(str(f))
        self.player.set_media(media)
        self.player.play()
        self.status_var.set("▶ Playing. Use 1..6 hotkeys or click a category.")

    # ---------- Actions ----------
    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.status_var.set("⏸ Paused")
        else:
            self.player.play()
            self.status_var.set("▶ Playing")

    def stop_playback(self):
        try:
            if self.player.is_playing():
                self.player.stop()
        except Exception:
            pass

    def copy_to_category(self, category_slug):
        if self.idx >= len(self.files):
            return
        src = self.files[self.idx]
        dest_folder = LIBRARY_ROOT / category_slug
        dest = dest_folder / src.name

        # collision handling
        if dest.exists():
            stem, suf = src.stem, src.suffix
            i = 1
            while (dest_folder / f"{stem}_{i}{suf}").exists():
                i += 1
            dest = dest_folder / f"{stem}_{i}{suf}"

        try:
            shutil.copy2(src, dest)  # COPY (not move) => zero lock issues
            self.copied_log.add(src.resolve())
            self.status_var.set(f"✅ Copied to {category_slug}.")
        except Exception as e:
            messagebox.showerror("Copy failed", str(e))
            return

        # advance to next
        self.idx += 1
        self.load_current()

    def skip_file(self):
        if self.idx < len(self.files):
            self.idx += 1
            self.status_var.set("⏭ Skipped.")
            self.load_current()

    def cleanup_copied(self):
        """Delete originals only for files we already copied successfully."""
        if not self.copied_log:
            messagebox.showinfo("Cleanup", "Nothing to delete yet.")
            return
        count = 0
        for p in list(self.copied_log):
            try:
                if Path(p).exists():
                    os.remove(p)
                self.copied_log.discard(p)
                count += 1
            except Exception:
                pass
        messagebox.showinfo("Cleanup", f"Deleted {count} original file(s).")

    def on_close(self):
        try:
            self.stop_playback()
        except Exception:
            pass
        self.destroy()


def main():
    app = AudioSorter()
    app.mainloop()

if __name__ == "__main__":
    main()
