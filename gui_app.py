"""
ShortsMaker Pro - Modern GUI Application with AI Voice Generation
Create professional quote videos for social media with AI voices!
"""

import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QSpinBox, QComboBox, QProgressBar, QTextEdit,
                             QFileDialog, QGroupBox, QMessageBox, QTabWidget, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon
from pathlib import Path
from dotenv import load_dotenv

# Import your existing modules
import ffmpeg
from Fonts import Fonts

# Import TTS providers
from providers.elevenlabs_tts import ElevenLabsTTS
from providers.cartesia_tts import CartesiaTTS

# Import content pack manager (NEW!)
from content_pack_manager import ContentPackManager


class VideoCreatorThread(QThread):
    """Background thread for video creation to keep UI responsive"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        """Run video creation in background"""
        try:
            self.status.emit("Initializing video creation...")
            total_videos = self.config['number_of_videos']
            
            ffmpeg.create_videos(
                video_folder=self.config['video_folder'],
                audio_folder=self.config['audio_folder'],
                fonts_dir=self.config['fonts_dir'],
                output_folder=self.config['output_folder'],
                text_source_font=self.config['text_source_font'],
                image_file=self.config['image_file'],
                customer_name=self.config['customer_name'],
                number_of_videos=total_videos,
                fonts=self.config['fonts'],
                progress_callback=self.update_progress,
                use_logo=self.config.get('use_logo', True),
                use_tts=self.config.get('use_tts', False),
                tts_provider=self.config.get('tts_provider', None),
                tts_voice_id=self.config.get('tts_voice_id', None),
                content_pack=self.config.get('content_pack', None),
                randomize=self.config.get('randomize', True)
            )
            
            self.finished.emit(True, f"Successfully created {total_videos} videos!")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def update_progress(self, current, total):
        """Callback for progress updates"""
        percentage = int((current / total) * 100)
        self.progress.emit(percentage)
        self.status.emit(f"Creating video {current} of {total}...")


class ShortsMakerGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.project_dir = Path.cwd()
        load_dotenv()
        self.tts_providers = {}
        self.current_voices = []
        self.pack_manager = ContentPackManager()
        self.selected_pack_key = ""
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ShortsMaker Pro - Professional Video Creator with AI Voices v2.0")
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(1000, 750)
        
        self.setStyleSheet("""
            QWidget { color: #333333; font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel { color: #333333; }
            QGroupBox { color: #333333; font-weight: bold; border: 2px solid #ddd; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { color: #333333; subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { color: #333333; }
            QComboBox { color: #333333; }
            QLineEdit { color: #333333; }
            QSpinBox { color: #333333; }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #4CAF50); border-radius: 5px; padding: 8px; }
        """)
        header_layout = QHBoxLayout(header_widget)
        
        header = QLabel("🎬 ShortsMaker Pro")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        subtitle = QLabel("AI Video Creator")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_widget)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 2px solid #ddd; border-radius: 5px; padding: 10px; background-color: white; }
            QTabBar::tab { background-color: #f0f0f0; border: 1px solid #ddd; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; font-weight: bold; color: #333333; }
            QTabBar::tab:selected { background-color: white; border-bottom-color: white; color: #000000; }
            QTabBar::tab:hover { background-color: #e0e0e0; }
        """)
        
        tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        tabs.addTab(self.create_content_tab(), "📝 Content")
        tabs.addTab(self.create_generation_tab(), "🎥 Generate Videos")
        main_layout.addWidget(tabs)
        
        self.status_label = QLabel("✅ Ready to create amazing videos with AI voices!")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("""
            QLabel { padding: 12px; background-color: #e8f5e9; border: 2px solid #4CAF50; border-radius: 5px; color: #2e7d32; font-weight: bold; }
        """)
        main_layout.addWidget(self.status_label)
    
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        project_group = QGroupBox("📋 Project Settings")
        project_layout = QVBoxLayout()
        
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Project/Customer Name:")
        customer_label.setStyleSheet("color: #333333;")
        customer_layout.addWidget(customer_label)
        self.customer_name_input = QLineEdit("my_project")
        self.customer_name_input.setPlaceholderText("Enter customer or project name...")
        self.customer_name_input.setStyleSheet("color: #333333; background-color: white;")
        customer_layout.addWidget(self.customer_name_input)
        project_layout.addLayout(customer_layout)
        
        videos_layout = QHBoxLayout()
        videos_label = QLabel("Number of Videos:")
        videos_label.setStyleSheet("color: #333333;")
        videos_layout.addWidget(videos_label)
        self.num_videos_input = QSpinBox()
        self.num_videos_input.setMinimum(1)
        self.num_videos_input.setMaximum(1000)
        self.num_videos_input.setValue(10)
        self.num_videos_input.setSuffix(" videos")
        self.num_videos_input.setStyleSheet("color: #333333; background-color: white;")
        videos_layout.addWidget(self.num_videos_input)
        videos_layout.addStretch()
        project_layout.addLayout(videos_layout)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        tts_group = QGroupBox("🎤 AI Voice Generation (Text-to-Speech)")
        tts_layout = QVBoxLayout()
        
        self.use_tts_checkbox = QCheckBox("☑️ Generate AI Voice-Over for Videos")
        self.use_tts_checkbox.setStyleSheet("color: #333333; font-weight: bold; font-size: 11pt;")
        self.use_tts_checkbox.setChecked(False)
        self.use_tts_checkbox.stateChanged.connect(self.toggle_tts_controls)
        tts_layout.addWidget(self.use_tts_checkbox)
        
        self.tts_controls_widget = QWidget()
        tts_controls_layout = QVBoxLayout(self.tts_controls_widget)
        tts_controls_layout.setContentsMargins(20, 10, 0, 0)
        
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Voice Provider:")
        provider_label.setStyleSheet("color: #333333; font-weight: bold;")
        provider_layout.addWidget(provider_label)
        
        self.tts_provider_combo = QComboBox()
        self.tts_provider_combo.addItem("ElevenLabs (48 voices)")
        self.tts_provider_combo.addItem("Cartesia (295 voices)")
        self.tts_provider_combo.setStyleSheet("color: #333333; background-color: white;")
        self.tts_provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.tts_provider_combo)
        provider_layout.addStretch()
        tts_controls_layout.addLayout(provider_layout)
        
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key Status:")
        api_key_label.setStyleSheet("color: #333333;")
        api_key_layout.addWidget(api_key_label)
        
        self.api_key_status_label = QLabel("Checking...")
        self.api_key_status_label.setStyleSheet("color: #666; font-style: italic;")
        api_key_layout.addWidget(self.api_key_status_label)
        api_key_layout.addStretch()
        tts_controls_layout.addLayout(api_key_layout)
        
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Select Voice:")
        voice_label.setStyleSheet("color: #333333; font-weight: bold;")
        voice_layout.addWidget(voice_label)
        
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet("color: #333333; background-color: white;")
        self.voice_combo.setMinimumWidth(300)
        voice_layout.addWidget(self.voice_combo)
        
        self.test_voice_btn = QPushButton("🔊 Test Voice")
        self.test_voice_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.test_voice_btn.clicked.connect(self.test_voice)
        voice_layout.addWidget(self.test_voice_btn)
        voice_layout.addStretch()
        tts_controls_layout.addLayout(voice_layout)
        
        info_label = QLabel("💡 Tip: AI voices will replace background audio. Choose a voice that matches your content!")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f0f8ff; border-radius: 4px;")
        info_label.setWordWrap(True)
        tts_controls_layout.addWidget(info_label)
        
        tts_layout.addWidget(self.tts_controls_widget)
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        self.tts_controls_widget.setEnabled(False)
        
        folders_group = QGroupBox("📁 Resource Folders")
        folders_layout = QVBoxLayout()
        
        logo_section = QHBoxLayout()
        logo_label = QLabel("Logo/Watermark Image:")
        logo_label.setStyleSheet("font-weight: bold; color: #333333;")
        logo_section.addWidget(logo_label)
        
        self.use_logo_checkbox = QCheckBox("Use Logo/Watermark")
        self.use_logo_checkbox.setChecked(True)
        self.use_logo_checkbox.setStyleSheet("color: #333333; font-weight: normal;")
        self.use_logo_checkbox.stateChanged.connect(self.toggle_logo_input)
        logo_section.addWidget(self.use_logo_checkbox)
        logo_section.addStretch()
        folders_layout.addLayout(logo_section)
        
        self.logo_file_input = self.create_file_selector_compact(str(self.project_dir / "sources" / "logo.png"), "Images (*.png *.jpg *.jpeg)")
        folders_layout.addLayout(self.logo_file_input)
        
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        self.check_api_keys()
        layout.addStretch()
        return tab
    
    def toggle_tts_controls(self, state):
        enabled = (state == 2)
        self.tts_controls_widget.setEnabled(enabled)
        if enabled:
            self.status_label.setText("🎤 AI Voice-Over enabled! Select a provider and voice.")
            self.check_api_keys()
            self.on_provider_changed()
        else:
            self.status_label.setText("✅ Ready to create videos (without AI voices)")
    
    def check_api_keys(self):
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        if elevenlabs_key:
            self.api_key_status_label.setText("✅ ElevenLabs: Connected")
            self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.api_key_status_label.setText("⚠️ Add ELEVENLABS_API_KEY to .env file")
            self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
    
    def on_provider_changed(self):
        provider_text = self.tts_provider_combo.currentText()
        if "ElevenLabs" in provider_text:
            self.load_voices_for_provider("elevenlabs")
        elif "Cartesia" in provider_text:
            self.load_voices_for_provider("cartesia")
    
    def load_voices_for_provider(self, provider_name):
        self.voice_combo.clear()
        self.voice_combo.addItem("Loading voices...")
        self.test_voice_btn.setEnabled(False)
        
        try:
            if provider_name == "elevenlabs":
                api_key = os.getenv('ELEVENLABS_API_KEY')
                if not api_key:
                    self.voice_combo.clear()
                    self.voice_combo.addItem("⚠️ No API key found in .env")
                    self.api_key_status_label.setText("⚠️ Add ELEVENLABS_API_KEY to .env file")
                    self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                    return
                
                if 'elevenlabs' not in self.tts_providers:
                    self.tts_providers['elevenlabs'] = ElevenLabsTTS(api_key=api_key)
                
                provider = self.tts_providers['elevenlabs']
                self.api_key_status_label.setText("✅ ElevenLabs: Connected")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                
            else:
                api_key = os.getenv('CARTESIA_API_KEY')
                if not api_key:
                    self.voice_combo.clear()
                    self.voice_combo.addItem("⚠️ No API key found in .env")
                    self.api_key_status_label.setText("⚠️ Add CARTESIA_API_KEY to .env file")
                    self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                    return
                
                if 'cartesia' not in self.tts_providers:
                    self.tts_providers['cartesia'] = CartesiaTTS(api_key=api_key)
                
                provider = self.tts_providers['cartesia']
                self.api_key_status_label.setText("✅ Cartesia: Connected")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            voices = provider.get_available_voices()
            self.current_voices = voices
            
            self.voice_combo.clear()
            for voice in voices:
                display_text = f"{voice['name']} - {voice['description']}"
                self.voice_combo.addItem(display_text, voice['id'])
            
            self.test_voice_btn.setEnabled(True)
            self.status_label.setText(f"✅ Loaded {len(voices)} voices from {provider_name.title()}!")
            
        except Exception as e:
            self.voice_combo.clear()
            self.voice_combo.addItem(f"❌ Error loading voices: {str(e)}")
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def test_voice(self):
        if self.voice_combo.currentIndex() < 0:
            return
        
        try:
            self.test_voice_btn.setEnabled(False)
            self.test_voice_btn.setText("🔄 Generating...")
            
            provider_text = self.tts_provider_combo.currentText()
            provider_name = "elevenlabs" if "ElevenLabs" in provider_text else "cartesia"
            voice_id = self.voice_combo.currentData()
            voice_name = self.voice_combo.currentText().split(" - ")[0]
            
            provider = self.tts_providers.get(provider_name)
            if not provider:
                raise Exception("Provider not initialized")
            
            test_text = f"Hello! This is a test of the {voice_name} voice. This is how your videos will sound with AI narration!"
            output_path = f"test_voice_{provider_name}.mp3"
            
            self.status_label.setText(f"🎤 Generating test audio with {voice_name}...")
            
            provider.generate_audio(text=test_text, voice_id=voice_id, output_path=output_path)
            
            self.status_label.setText(f"✅ Test audio created! Listen to: {output_path}")
            
            try:
                import subprocess
                subprocess.Popen(["start", output_path], shell=True)
            except:
                pass
            
        except Exception as e:
            self.status_label.setText(f"❌ Error testing voice: {str(e)}")
        finally:
            self.test_voice_btn.setEnabled(True)
            self.test_voice_btn.setText("🔊 Test Voice")
    
    def create_file_selector_compact(self, default_path, file_filter):
        layout = QHBoxLayout()
        
        input_field = QLineEdit(default_path)
        input_field.setReadOnly(True)
        input_field.setStyleSheet("background-color: #f9f9f9; color: #333333;")
        layout.addWidget(input_field)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setMaximumWidth(100)
        browse_btn.setStyleSheet("color: #333333; background-color: #f0f0f0;")
        browse_btn.clicked.connect(lambda: self.browse_file(input_field, file_filter))
        layout.addWidget(browse_btn)
        
        if "logo" in default_path.lower():
            self.logo_image_field = input_field
            self.logo_browse_button = browse_btn
        
        return layout
    
    def toggle_logo_input(self, state):
        enabled = (state == 2)
        
        if hasattr(self, 'logo_image_field'):
            self.logo_image_field.setEnabled(enabled)
            if enabled:
                self.logo_image_field.setStyleSheet("background-color: #f9f9f9; color: #333333;")
            else:
                self.logo_image_field.setStyleSheet("background-color: #e0e0e0; color: #999999;")
        
        if hasattr(self, 'logo_browse_button'):
            self.logo_browse_button.setEnabled(enabled)
            if enabled:
                self.logo_browse_button.setStyleSheet("color: #333333; background-color: #f0f0f0;")
            else:
                self.logo_browse_button.setStyleSheet("color: #666666; background-color: #e0e0e0;")
    
    def browse_file(self, input_field, file_filter):
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if file:
            input_field.setText(file)
    
    def create_content_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content_group = QGroupBox("📦 Content Pack Selection")
        content_layout = QVBoxLayout()
        
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #333333; font-weight: bold;")
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(300)
        self.category_combo.setStyleSheet("color: #333333; background-color: white;")
        
        categories = self.pack_manager.get_all_categories()
        for cat in categories:
            self.category_combo.addItem(cat)
        
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        content_layout.addLayout(category_layout)
        
        topic_layout = QHBoxLayout()
        topic_label = QLabel("Topic:")
        topic_label.setStyleSheet("color: #333333; font-weight: bold;")
        topic_layout.addWidget(topic_label)
        
        self.topic_combo = QComboBox()
        self.topic_combo.setMinimumWidth(300)
        self.topic_combo.setStyleSheet("color: #333333; background-color: white;")
        self.topic_combo.currentTextChanged.connect(self.on_topic_changed)
        topic_layout.addWidget(self.topic_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.setToolTip("Reload content packs")
        refresh_btn.setStyleSheet("color: #333333; background-color: #f0f0f0;")
        refresh_btn.clicked.connect(self.refresh_content_packs)
        topic_layout.addWidget(refresh_btn)
        
        topic_layout.addStretch()
        content_layout.addLayout(topic_layout)
        
        self.pack_info_label = QLabel("Select a category and topic")
        self.pack_info_label.setStyleSheet("""
            QLabel { color: #666; padding: 10px; background-color: #f0f8ff; border-radius: 4px; border: 1px solid #ddd; }
        """)
        self.pack_info_label.setWordWrap(True)
        content_layout.addWidget(self.pack_info_label)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        random_group = QGroupBox("🎲 Randomization Options")
        random_layout = QVBoxLayout()
        
        self.randomize_checkbox = QCheckBox("☑️ Shuffle Quotes (Prevents Repeats)")
        self.randomize_checkbox.setChecked(True)
        self.randomize_checkbox.setStyleSheet("color: #333333; font-weight: bold; font-size: 11pt;")
        random_layout.addWidget(self.randomize_checkbox)
        
        info_label = QLabel("💡 Tip: When enabled, quotes are randomly selected without repeating until all are used!")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        info_label.setWordWrap(True)
        random_layout.addWidget(info_label)
        
        random_group.setLayout(random_layout)
        layout.addWidget(random_group)
        
        preview_group = QGroupBox("📖 Content Preview")
        preview_layout = QVBoxLayout()
        
        preview_controls = QHBoxLayout()
        preview_btn = QPushButton("🔍 Preview Content")
        preview_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 5px;")
        preview_btn.clicked.connect(self.preview_pack_content)
        preview_controls.addWidget(preview_btn)
        
        self.preview_info_label = QLabel("Select a pack to preview")
        self.preview_info_label.setStyleSheet("color: #666; font-style: italic;")
        preview_controls.addWidget(self.preview_info_label)
        preview_controls.addStretch()
        
        preview_layout.addLayout(preview_controls)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(250)
        self.preview_text.setStyleSheet("""
            QTextEdit { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 10px; font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt; color: #333333; }
        """)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("📁 Open Content Packs Folder")
        open_folder_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 8px;")
        open_folder_btn.clicked.connect(self.open_content_packs_folder)
        actions_layout.addWidget(open_folder_btn)
        
        create_pack_btn = QPushButton("➕ How to Create New Pack")
        create_pack_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 8px;")
        create_pack_btn.clicked.connect(self.show_create_pack_help)
        actions_layout.addWidget(create_pack_btn)
        
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        if categories:
            self.on_category_changed(categories[0])
        
        layout.addStretch()
        return tab
    
    def on_category_changed(self, category):
        if not category:
            return
        
        self.topic_combo.clear()
        topics = self.pack_manager.get_topics_in_category(category)
        
        for topic in topics:
            display_text = f"{topic['name']} ({topic['quote_count']} quotes)"
            self.topic_combo.addItem(display_text, topic['key'])
        
        if topics:
            self.on_topic_changed(self.topic_combo.itemText(0))
    
    def on_topic_changed(self, topic_text):
        if not topic_text or self.topic_combo.currentIndex() < 0:
            return
        
        pack_key = self.topic_combo.currentData()
        if not pack_key:
            return
        
        self.selected_pack_key = pack_key
        
        pack = self.pack_manager.get_pack(pack_key)
        if not pack:
            return
        
        resources = pack.get_resource_summary()
        info_text = f"""
📦 {pack.get_display_name()}
📝 {resources['quotes']} quotes available
🎥 {resources['videos']} videos available
🎵 {resources['audio']} audio files available
📄 {pack.info.get('description', 'No description')}
        """
        self.pack_info_label.setText(info_text.strip())
        self.pack_info_label.setStyleSheet("""
            QLabel { color: #2e7d32; padding: 10px; background-color: #e8f5e9; border-radius: 4px; border: 2px solid #4CAF50; font-weight: bold; }
        """)
        
        self.preview_pack_content()
    
    def refresh_content_packs(self):
        self.pack_manager = ContentPackManager()
        
        current_category = self.category_combo.currentText()
        self.category_combo.clear()
        categories = self.pack_manager.get_all_categories()
        for cat in categories:
            self.category_combo.addItem(cat)
        
        if current_category in categories:
            self.category_combo.setCurrentText(current_category)
        
        self.status_label.setText("✅ Content packs reloaded!")
    
    def preview_pack_content(self):
        if not self.selected_pack_key:
            self.preview_text.setText("⚠️ Please select a content pack first.")
            return
        
        pack = self.pack_manager.get_pack(self.selected_pack_key)
        if not pack:
            self.preview_text.setText("⚠️ Could not load content pack.")
            return
        
        quotes, refs = pack.get_quotes_and_references(randomize=False, count=3)
        
        if not quotes:
            self.preview_text.setText("⚠️ This pack has no quotes yet. Add a quotes file!")
            return
        
        preview = f"📊 Total Quotes: {pack.get_quote_count()}\n"
        preview += f"📦 Pack: {pack.get_display_name()}\n"
        preview += "=" * 70 + "\n\n"
        
        for i in range(min(3, len(quotes))):
            preview += f"#{i+1} {refs[i]}\n"
            preview += f"{quotes[i][:200]}{'...' if len(quotes[i]) > 200 else ''}\n\n"
        
        if len(quotes) > 3:
            preview += "=" * 70 + "\n"
            preview += f"... and {len(quotes) - 3} more quotes\n"
        
        self.preview_text.setText(preview)
        self.preview_info_label.setText(f"✅ Showing first 3 of {pack.get_quote_count()} quotes")
        self.preview_info_label.setStyleSheet("color: #4CAF50; font-style: italic; font-weight: bold;")
    
    def open_content_packs_folder(self):
        content_packs_folder = self.project_dir / "content_packs"
        
        if not content_packs_folder.exists():
            content_packs_folder.mkdir(parents=True, exist_ok=True)
        
        import subprocess
        subprocess.Popen(f'explorer "{content_packs_folder}"')
    
    def show_create_pack_help(self):
        help_text = """
📦 Creating New Content Packs

1. Open the content_packs folder

2. Create a folder structure like:
   content_packs/[category]/[topic]/

   Example: content_packs/motivation/success/

3. Inside that folder, create pack_config.json

4. Create your quotes file in library/quotes/

5. Click the 🔄 button to reload

💡 Tip: Multiple packs can share the same library resources!
        """
        
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QMessageBox QLabel { color: #333333; font-size: 10pt; }
            QMessageBox QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 4px; min-width: 80px; }
        """)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Create New Content Pack")
        msg_box.setText(help_text)
        msg_box.exec()
    
    def create_generation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        summary_group = QGroupBox("📊 Generation Summary")
        summary_layout = QVBoxLayout()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(120)
        self.summary_text.setStyleSheet("""
            QTextEdit { background-color: #f0f8ff; border: 2px solid #4CAF50; border-radius: 5px; padding: 10px; font-family: 'Segoe UI', Arial; font-size: 10pt; color: #333333; }
        """)
        self.summary_text.setText("Configure your settings in the Settings and Content tabs, then click Generate Videos below.")
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        controls_group = QGroupBox("🎬 Generation Controls")
        controls_layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎬 Generate Videos")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 15px; font-size: 16px; font-weight: bold; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.generate_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setMaximumWidth(120)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 15px; font-size: 16px; font-weight: bold; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        button_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(button_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        progress_group = QGroupBox("📈 Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #ddd; border-radius: 5px; text-align: center; font-weight: bold; font-size: 12pt; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to start")
        self.progress_label.setStyleSheet("font-size: 11pt; padding: 5px; color: #333333;")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        log_group = QGroupBox("📋 Output Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace; font-size: 9pt; border-radius: 5px; padding: 10px; }
        """)
        log_layout.addWidget(self.log_text)
        
        log_controls = QHBoxLayout()
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 5px;")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_controls.addWidget(clear_log_btn)
        
        open_output_btn = QPushButton("📁 Open Output Folder")
        open_output_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 5px;")
        open_output_btn.clicked.connect(self.open_output_folder)
        log_controls.addWidget(open_output_btn)
        
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return tab
    
    def open_output_folder(self):
        customer_name = self.customer_name_input.text()
        output_path = self.project_dir / "customers" / customer_name
        
        if output_path.exists():
            import subprocess
            subprocess.Popen(f'explorer "{output_path}"')
        else:
            msg_box = QMessageBox(self)
            msg_box.setStyleSheet("""
                QMessageBox { background-color: white; }
                QMessageBox QLabel { color: #333333; font-size: 10pt; }
            """)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Folder Not Found")
            msg_box.setText(f"Output folder doesn't exist yet.\n\nPath: {output_path}")
            msg_box.exec()
    
    def start_generation(self):
        try:
            if not self.validate_inputs():
                return
            
            self.update_summary()
            config = self.get_configuration()
            
            self.worker = VideoCreatorThread(config)
            self.worker.progress.connect(self.update_progress)
            self.worker.status.connect(self.update_status)
            self.worker.finished.connect(self.generation_finished)
            
            self.generate_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.log_text.clear()
            self.log_text.append("🚀 Starting video generation...\n")
            
            self.worker.start()
            
        except Exception as e:
            self.show_styled_message("Error", f"Failed to start: {str(e)}", QMessageBox.Icon.Critical)
    
    def validate_inputs(self):
        pack = self.pack_manager.get_pack(self.selected_pack_key)
        if not pack:
            self.show_styled_message("Warning", "Please select a content pack!", QMessageBox.Icon.Warning)
            return False
        
        resources = pack.get_resource_summary()
        if resources['quotes'] == 0:
            self.show_styled_message("Warning", "Selected pack has no quotes!", QMessageBox.Icon.Warning)
            return False
        
        if resources['videos'] == 0:
            self.show_styled_message("Warning", "Selected pack has no videos!", QMessageBox.Icon.Warning)
            return False
        
        if resources['audio'] == 0:
            self.show_styled_message("Warning", "Selected pack has no audio files!", QMessageBox.Icon.Warning)
            return False
        
        return True
    
    def show_styled_message(self, title, message, icon=QMessageBox.Icon.Information):
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QMessageBox QLabel { color: #333333; font-size: 10pt; }
            QMessageBox QPushButton { background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 4px; min-width: 80px; }
        """)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def get_configuration(self):
        fonts_paths = [
            str(self.project_dir / 'sources/fonts/CoffeeJellyUmai.ttf'),
            str(self.project_dir / 'sources/fonts/CourierprimecodeRegular.ttf'),
            str(self.project_dir / 'sources/fonts/FlowersSunday.otf'),
            str(self.project_dir / 'sources/fonts/GreenTeaJelly.ttf'),
            str(self.project_dir / 'sources/fonts/HeyMarch.ttf'),
            str(self.project_dir / 'sources/fonts/LetsCoffee.otf'),
            str(self.project_dir / 'sources/fonts/LikeSlim.ttf'),
            str(self.project_dir / 'sources/fonts/SunnySpellsBasicRegular.ttf'),
            str(self.project_dir / 'sources/fonts/TakeCoffee.ttf'),
            str(self.project_dir / 'sources/fonts/WantCoffee.ttf')
        ]
        fonts_sizes = [95, 70, 65, 85, 75, 50, 75, 87, 50, 65]
        fonts_maxcharsline = [34, 25, 30, 45, 33, 34, 35, 32, 35, 35]
        
        fonts = Fonts(fonts_paths, fonts_sizes, fonts_maxcharsline)
        
        pack = self.pack_manager.get_pack(self.selected_pack_key)
        
        use_tts = self.use_tts_checkbox.isChecked()
        tts_provider = None
        tts_voice_id = None
        
        if use_tts:
            provider_text = self.tts_provider_combo.currentText()
            tts_provider = "elevenlabs" if "ElevenLabs" in provider_text else "cartesia"
            tts_voice_id = self.voice_combo.currentData()
        
        return {
            'video_folder': None,
            'audio_folder': None,
            'content_pack': pack,
            'randomize': self.randomize_checkbox.isChecked(),
            'fonts_dir': str(self.project_dir / 'sources/fonts'),
            'output_folder': str(self.project_dir / 'customers'),
            'text_source_font': str(self.project_dir / 'sources/MouldyCheeseRegular-WyMWG.ttf').replace(':', '\\:'),
            'image_file': self.logo_image_field.text(),
            'use_logo': self.use_logo_checkbox.isChecked(),
            'customer_name': self.customer_name_input.text(),
            'number_of_videos': self.num_videos_input.value(),
            'fonts': fonts,
            'use_tts': use_tts,
            'tts_provider': tts_provider,
            'tts_voice_id': tts_voice_id
        }
    
    def update_summary(self):
        pack = self.pack_manager.get_pack(self.selected_pack_key)
        
        if not pack:
            self.summary_text.setText("⚠️ Please select a content pack first!")
            return
        
        resources = pack.get_resource_summary()
        logo_status = "✓ Enabled" if self.use_logo_checkbox.isChecked() else "✗ Disabled"
        
        tts_status = "✗ Disabled"
        if self.use_tts_checkbox.isChecked():
            provider = self.tts_provider_combo.currentText()
            voice = self.voice_combo.currentText()
            tts_status = f"✓ Enabled ({provider.split(' ')[0]}: {voice.split(' - ')[0]})"
        
        random_status = "✓ ON (No repeats!)" if self.randomize_checkbox.isChecked() else "✗ OFF (Sequential)"
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              🎬 GENERATION CONFIGURATION                      ║
╚══════════════════════════════════════════════════════════════╝

👤 Customer/Project: {self.customer_name_input.text()}
🎥 Videos to Create: {self.num_videos_input.value()}

📦 Content Pack: {pack.get_display_name()}
   📝 {resources['quotes']} quotes
   🎥 {resources['videos']} videos  
   🎵 {resources['audio']} audio files

⚙️ Settings:
   • Logo: {logo_status}
   • AI Voice: {tts_status}
   • Randomization: {random_status}

✅ Ready to generate!
        """
        self.summary_text.setText(summary.strip())
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.progress_label.setText(message)
        self.log_text.append(message)
    
    def generation_finished(self, success, message):
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.log_text.append(f"\n✅ {message}")
            self.show_styled_message("Success", message, QMessageBox.Icon.Information)
        else:
            self.log_text.append(f"\n❌ {message}")
            self.show_styled_message("Error", message, QMessageBox.Icon.Critical)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    
    window = ShortsMakerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()