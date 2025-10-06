"""
File Organizer — responsive + Windows-friendly.
- Plays a temp preview copy so the original file isn't locked by the player.
- Moves originals to library/audio|video/<category>.
- Move and preview-copy are both done in background threads to avoid UI freezes.
"""

import sys
import shutil
import uuid
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QFileDialog, QMessageBox,
    QGroupBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


# ---------------- background workers ---------------- #

class MoveWorker(QObject):
    finished = pyqtSignal(bool, str)  # success, error

    def __init__(self, src: Path, dst: Path):
        super().__init__()
        self.src = Path(src)
        self.dst = Path(dst)

    def run(self):
        try:
            self.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(self.src), str(self.dst))
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class PreviewWorker(QObject):
    finished = pyqtSignal(bool, str, str)  # success, error, preview_path

    def __init__(self, src: Path, preview_dir: Path):
        super().__init__()
        self.src = Path(src)
        self.preview_dir = Path(preview_dir)

    def run(self):
        try:
            self.preview_dir.mkdir(exist_ok=True)
            preview_path = self.preview_dir / f"{uuid.uuid4().hex}{self.src.suffix}"
            shutil.copy2(str(self.src), str(preview_path))
            self.finished.emit(True, "", str(preview_path))
        except Exception as e:
            self.finished.emit(False, str(e), "")


# ------------------------------- Main Window ---------------------------------- #

class FileOrganizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📁 ShortsMaker File Organizer - Quick & Easy!")
        self.setGeometry(100, 100, 900, 650)
        self.setMinimumSize(800, 560)

        # State
        self.files_to_organize: list[Path] = []
        self.current_index: int = 0
        self.organizing_type: str | None = None  # 'video' or 'audio'
        self.library_path = Path("library")
        self.media_root = {"video": "video", "audio": "audio"}  # exact folder names

        # Preview cache
        self.preview_dir = Path.cwd() / ".preview_cache"
        self.current_preview: Path | None = None

        # Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.85)
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        # Worker threads
        self._move_thread: QThread | None = None
        self._move_worker: MoveWorker | None = None
        self._preview_thread: QThread | None = None
        self._preview_worker: PreviewWorker | None = None
        self._preview_inflight = False

        self.init_ui()

    # ============================= UI SETUP ============================= #

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        header = QLabel("📁 File Organizer")
        f = QFont("Arial", 13); f.setWeight(QFont.Weight.Medium)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("QLabel { color: #2196F3; padding: 4px; }")
        main.addWidget(header)

        instructions = QLabel(
            "👋 Click 'Organize Videos' or 'Organize Audio' to begin.\n"
            "Each file will play/show — then click where it belongs."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #aaa; font-size: 10pt; padding: 4px;")
        main.addWidget(instructions)

        start_group = QGroupBox("🚀 Get Started")
        start_group.setStyleSheet("""
            QGroupBox { border: 1px solid #3a3a3a; border-radius: 6px; margin-top: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #bbb; font-size: 9.5pt; }
        """)
        start_row = QHBoxLayout(); start_row.setSpacing(8); start_group.setLayout(start_row)

        start_video_btn = QPushButton("📹 Organize Videos")
        start_video_btn.setMinimumHeight(44)
        start_video_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        start_video_btn.setStyleSheet("""
            QPushButton { background-color:#4CAF50; color:white; font-size:12pt; font-weight:700; border-radius:8px; padding:6px 10px; }
            QPushButton:hover { background-color:#45a049; }
        """)
        start_video_btn.clicked.connect(lambda: self.start_organizing('video'))

        start_audio_btn = QPushButton("🎵 Organize Audio")
        start_audio_btn.setMinimumHeight(44)
        start_audio_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        start_audio_btn.setStyleSheet("""
            QPushButton { background-color:#2196F3; color:white; font-size:12pt; font-weight:700; border-radius:8px; padding:6px 10px; }
            QPushButton:hover { background-color:#1976D2; }
        """)
        start_audio_btn.clicked.connect(lambda: self.start_organizing('audio'))

        start_row.addWidget(start_video_btn)
        start_row.addWidget(start_audio_btn)
        main.addWidget(start_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border:1px solid #444; border-radius:5px; text-align:center; font-weight:600; font-size:10.5pt; background:#222; }
            QProgressBar::chunk { background-color:#4CAF50; }
        """)
        main.addWidget(self.progress_bar)

        self.file_info_label = QLabel("Ready to organize!")
        self.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_info_label.setStyleSheet("""
            QLabel { font-size:12pt; font-weight:700; padding:8px; background:#f0f8ff; border-radius:5px; border:2px solid #2196F3; color:#222; }
        """)
        main.addWidget(self.file_info_label)

        self.video_widget.setMinimumHeight(240)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setStyleSheet("background-color:black; border-radius:5px;")
        main.addWidget(self.video_widget, stretch=1)

        controls = QHBoxLayout(); controls.setSpacing(8)
        self.play_btn = QPushButton("▶ Play"); self.play_btn.setEnabled(False); self.play_btn.setMinimumHeight(28)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_btn)

        self.skip_btn = QPushButton("⏭ Skip (Keep Original Location)")
        self.skip_btn.setEnabled(False); self.skip_btn.setMinimumHeight(28)
        self.skip_btn.clicked.connect(self.skip_file)
        controls.addWidget(self.skip_btn)
        main.addLayout(controls)

        self.category_group = QGroupBox("📂 Where does this file belong?")
        self.category_group.setStyleSheet("""
            QGroupBox { border:1px solid #3a3a3a; border-radius:6px; margin-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; left:8px; padding:2px 4px; color:#bbb; font-size:9.5pt; }
        """)
        self.category_layout = QVBoxLayout(); self.category_layout.setSpacing(8)
        self.category_group.setLayout(self.category_layout)

        self.category_scroll = QScrollArea()
        self.category_scroll.setWidget(self.category_group)
        self.category_scroll.setWidgetResizable(True)
        self.category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.category_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.category_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.category_scroll.setMinimumHeight(180)

        self.category_group.setVisible(False)
        self.category_scroll.setVisible(False)
        main.addWidget(self.category_scroll, stretch=1)

        self.status_label = QLabel("👆 Click a button above to start!")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size:10.5pt; color:#999; padding:6px;")
        main.addWidget(self.status_label)

    # ========================= ORGANIZING FLOW ========================= #

    def start_organizing(self, file_type: str):
        self.organizing_type = file_type
        folder = QFileDialog.getExistingDirectory(self, f"Select folder with {file_type} files to organize", str(Path.cwd()))
        if not folder:
            return

        exts = ['.mp4', '.mov', '.avi', '.mkv'] if file_type == 'video' else ['.mp3', '.wav', '.m4a']
        self.files_to_organize = []
        for ext in exts:
            self.files_to_organize.extend(Path(folder).glob(f"*{ext}"))

        if not self.files_to_organize:
            QMessageBox.warning(self, "No Files Found", f"No {file_type} files found in selected folder!")
            return

        self.current_index = 0
        self.update_progress()

        self.setup_category_buttons()
        self.category_group.setVisible(True)
        self.category_scroll.setVisible(True)

        self.load_current_file()
        self.status_label.setText(f"✅ Loaded {len(self.files_to_organize)} files! Let's organize!")

    def setup_category_buttons(self):
        # Clear
        while self.category_layout.count():
            item = self.category_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
            else:
                sub = item.layout()
                if sub:
                    while sub.count():
                        si = sub.takeAt(0)
                        sw = si.widget()
                        if sw:
                            sw.setParent(None)

        # Categories
        if self.organizing_type == 'video':
            categories = [
                ('💪 Gym', 'gym', 'Workouts, training, fitness'),
                ('💰 Luxury', 'luxury', 'Cars, money, mansions, success'),
                ('🌲 Nature', 'nature', 'Peaceful nature, sunsets, mountains'),
                ('🏙️ Urban', 'urban', 'City life, streets, hustle'),
                ('✝️ Spiritual', 'spiritual', 'Churches, religious imagery'),
                ('🎨 Abstract', 'abstract', 'Abstract patterns, motion graphics'),
                ('📦 Generic', 'generic', 'Works for anything'),
            ]
        else:
            categories = [
                ('💪 Gym', 'gym', 'Pumped up workout music'),
                ('💰 Luxury', 'luxury', 'Powerful success music'),
                ('😌 Calm', 'calm', 'Peaceful meditation music'),
                ('😊 Uplifting', 'uplifting', 'Positive happy vibes'),
                ('🎭 Dramatic', 'dramatic', 'Epic powerful music'),
                ('📦 Generic', 'generic', 'Neutral background music'),
            ]

        # Two per row
        for i, (label, folder, desc) in enumerate(categories):
            if i % 2 == 0:
                row = QHBoxLayout(); row.setSpacing(8)
                self.category_layout.addLayout(row)

            btn = QPushButton(f"{label}\n{desc}")
            btn.setMinimumHeight(54)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#2196F3; color:white; font-size:11pt; font-weight:700;
                    border-radius:8px; padding:8px; text-align:center;
                }
                QPushButton:hover { background-color:#1976D2; }
            """)
            btn.clicked.connect(lambda checked=False, f=folder: self.move_to_category(f))
            row.addWidget(btn)

    # ---- preview management ----

    def _cleanup_preview(self):
        try:
            self.media_player.stop()
            self.media_player.setSource(QUrl())
        except Exception:
            pass
        if self.current_preview and self.current_preview.exists():
            try:
                os.remove(self.current_preview)
            except Exception:
                pass
        self.current_preview = None

    def load_current_file(self):
        """Start background copy for preview; UI stays responsive."""
        if self.current_index >= len(self.files_to_organize):
            self.finish_organizing()
            return

        src = self.files_to_organize[self.current_index]
        self.file_info_label.setText(f"📄 {src.name}\nFile {self.current_index + 1} of {len(self.files_to_organize)}")

        # Clean last preview and disable actions while we prepare
        self._cleanup_preview()
        self.play_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.status_label.setText("⏳ Preparing preview...")

        # Kick off preview copy in background
        self._preview_inflight = True
        self._preview_thread = QThread()
        self._preview_worker = PreviewWorker(src, self.preview_dir)
        self._preview_worker.moveToThread(self._preview_thread)
        self._preview_thread.started.connect(self._preview_worker.run)
        self._preview_worker.finished.connect(self._on_preview_ready)
        self._preview_worker.finished.connect(self._preview_thread.quit)
        self._preview_worker.finished.connect(self._preview_worker.deleteLater)
        self._preview_thread.finished.connect(self._preview_thread.deleteLater)
        self._preview_thread.start()

    def _on_preview_ready(self, success: bool, error: str, preview_path: str):
        self._preview_inflight = False
        if not success:
            self.status_label.setText(f"⚠️ Preview error: {error}")
            # Allow skip / try again
            self.play_btn.setEnabled(False)
            self.skip_btn.setEnabled(True)
            return

        self.current_preview = Path(preview_path)
        self.media_player.setSource(QUrl.fromLocalFile(preview_path))
        self.audio_output.setMuted(False)
        self.media_player.play()
        self.play_btn.setText("⏸ Pause")
        self.play_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.status_label.setText("▶ Playing preview")

    # ============================= ACTIONS ============================= #

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶ Play")
        else:
            self.audio_output.setMuted(False)
            self.media_player.play()
            self.play_btn.setText("⏸ Pause")

    def move_to_category(self, category: str):
        """Move original in background; preview keeps playing temp file."""
        if self._preview_inflight:
            # avoid starting a move while preview is copying
            return
        if self.current_index >= len(self.files_to_organize):
            return

        src = self.files_to_organize[self.current_index]

        base_root = self.media_root[self.organizing_type]  # 'audio' or 'video'
        dest_folder = self.library_path / base_root / category
        dest_folder.mkdir(parents=True, exist_ok=True)

        base = src.stem
        dest = dest_folder / src.name
        counter = 1
        while dest.exists():
            dest = dest_folder / f"{base}_{counter}{src.suffix}"
            counter += 1

        # Disable the category buttons briefly
        self.play_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.status_label.setText("⏳ Moving file...")

        self._move_thread = QThread()
        self._move_worker = MoveWorker(src, dest)
        self._move_worker.moveToThread(self._move_thread)
        self._move_thread.started.connect(self._move_worker.run)
        self._move_worker.finished.connect(self._on_move_finished)
        self._move_worker.finished.connect(self._move_thread.quit)
        self._move_worker.finished.connect(self._move_worker.deleteLater)
        self._move_thread.finished.connect(self._move_thread.deleteLater)
        self._move_thread.start()

    def _on_move_finished(self, success: bool, error: str):
        if not success:
            QMessageBox.warning(self, "Move Error", error)
            self.play_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
            return

        self.status_label.setText("✅ Moved.")
        # Advance to next file immediately; preview keeps playing old temp until next ready
        self.current_index += 1
        self.update_progress()
        self.load_current_file()

    def skip_file(self):
        if self._preview_inflight:
            return
        self.status_label.setText("⏭ Skipped (kept in original location)")
        self.current_index += 1
        self.update_progress()
        self.load_current_file()

    def update_progress(self):
        if not self.files_to_organize:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0/0 files organized (0%)")
            return
        progress = int((self.current_index / len(self.files_to_organize)) * 100)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(
            f"{self.current_index}/{len(self.files_to_organize)} files organized ({progress}%)"
        )

    def finish_organizing(self):
        self._cleanup_preview()
        self.play_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.category_group.setVisible(False)
        self.category_scroll.setVisible(False)

        self.file_info_label.setText("🎉 ALL DONE!")
        self.file_info_label.setStyleSheet("""
            QLabel { font-size:15pt; font-weight:800; padding:16px;
                     background:#e8f5e9; border-radius:5px; border:3px solid #4CAF50; color:#2e7d32; }
        """)
        self.status_label.setText(
            f"✅ Organized {len(self.files_to_organize)} {self.organizing_type} files!\n"
            "You can now close this window or organize more files."
        )
        QMessageBox.information(
            self, "Success!",
            f"🎉 Successfully organized {len(self.files_to_organize)} {self.organizing_type} files!\n\n"
            f"They're now in: library/{self.media_root[self.organizing_type]}/"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FileOrganizerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
