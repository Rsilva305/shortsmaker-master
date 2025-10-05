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


class VideoCreatorThread(QThread):
    """Background thread for video creation to keep UI responsive"""
    progress = pyqtSignal(int)  # Progress percentage
    status = pyqtSignal(str)    # Status message
    finished = pyqtSignal(bool, str)  # Success flag and message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        """Run video creation in background"""
        try:
            # Update status
            self.status.emit("Initializing video creation...")
            
            # Create videos using your existing function
            total_videos = self.config['number_of_videos']
            
            # We'll modify create_videos to report progress
            ffmpeg.create_videos(
                video_folder=self.config['video_folder'],
                audio_folder=self.config['audio_folder'],
                json_file=self.config['json_file'],
                fonts_dir=self.config['fonts_dir'],
                output_folder=self.config['output_folder'],
                text_source_font=self.config['text_source_font'],
                image_file=self.config['image_file'],
                customer_name=self.config['customer_name'],
                number_of_videos=total_videos,
                fonts=self.config['fonts'],
                progress_callback=self.update_progress,
                use_logo=self.config.get('use_logo', True),
                # TTS parameters
                use_tts=self.config.get('use_tts', False),
                tts_provider=self.config.get('tts_provider', None),
                tts_voice_id=self.config.get('tts_voice_id', None)
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
        self.content_file_mapping = {}
        
        # Load environment variables for API keys
        load_dotenv()
        
        # TTS providers (will be initialized when needed)
        self.tts_providers = {}
        self.current_voices = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ShortsMaker Pro - Professional Video Creator with AI Voices v2.0")
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(1000, 750)
        
        # Set global stylesheet
        self.setStyleSheet("""
            QWidget {
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #333333;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                color: #333333;
            }
            QComboBox {
                color: #333333;
            }
            QLineEdit {
                color: #333333;
            }
            QSpinBox {
                color: #333333;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Add header
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #4CAF50);
                border-radius: 5px;
                padding: 8px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)
        
        header = QLabel("🎬 ShortsMaker Pro with AI Voices")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        subtitle = QLabel("Professional Video Creator with AI Voice Generation")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_widget)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                color: #333333;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #000000;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        tabs.addTab(self.create_content_tab(), "📝 Content")
        tabs.addTab(self.create_generation_tab(), "🎥 Generate Videos")
        main_layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("✅ Ready to create amazing videos with AI voices!")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 12px;
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                color: #2e7d32;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.status_label)
        
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Project Settings Group
        project_group = QGroupBox("📋 Project Settings")
        project_layout = QVBoxLayout()
        
        # Customer Name
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Project/Customer Name:")
        customer_label.setStyleSheet("color: #333333;")
        customer_layout.addWidget(customer_label)
        self.customer_name_input = QLineEdit("my_project")
        self.customer_name_input.setPlaceholderText("Enter customer or project name...")
        self.customer_name_input.setStyleSheet("color: #333333; background-color: white;")
        customer_layout.addWidget(self.customer_name_input)
        project_layout.addLayout(customer_layout)
        
        # Number of Videos
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
        
        # TTS (AI Voice) Settings Group - NEW!
        tts_group = QGroupBox("🎤 AI Voice Generation (Text-to-Speech)")
        tts_layout = QVBoxLayout()
        
        # Enable TTS Checkbox
        self.use_tts_checkbox = QCheckBox("☑️ Generate AI Voice-Over for Videos")
        self.use_tts_checkbox.setStyleSheet("color: #333333; font-weight: bold; font-size: 11pt;")
        self.use_tts_checkbox.setChecked(False)
        self.use_tts_checkbox.stateChanged.connect(self.toggle_tts_controls)
        tts_layout.addWidget(self.use_tts_checkbox)
        
        # TTS Controls Container
        self.tts_controls_widget = QWidget()
        tts_controls_layout = QVBoxLayout(self.tts_controls_widget)
        tts_controls_layout.setContentsMargins(20, 10, 0, 0)
        
        # Provider Selection
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
        
        # API Key Status
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key Status:")
        api_key_label.setStyleSheet("color: #333333;")
        api_key_layout.addWidget(api_key_label)
        
        self.api_key_status_label = QLabel("Checking...")
        self.api_key_status_label.setStyleSheet("color: #666; font-style: italic;")
        api_key_layout.addWidget(self.api_key_status_label)
        api_key_layout.addStretch()
        tts_controls_layout.addLayout(api_key_layout)
        
        # Voice Selection
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Select Voice:")
        voice_label.setStyleSheet("color: #333333; font-weight: bold;")
        voice_layout.addWidget(voice_label)
        
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet("color: #333333; background-color: white;")
        self.voice_combo.setMinimumWidth(300)
        voice_layout.addWidget(self.voice_combo)
        
        # Test Voice Button
        self.test_voice_btn = QPushButton("🔊 Test Voice")
        self.test_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.test_voice_btn.clicked.connect(self.test_voice)
        voice_layout.addWidget(self.test_voice_btn)
        
        voice_layout.addStretch()
        tts_controls_layout.addLayout(voice_layout)
        
        # Info label
        info_label = QLabel("💡 Tip: AI voices will replace background audio. Choose a voice that matches your content!")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f0f8ff; border-radius: 4px;")
        info_label.setWordWrap(True)
        tts_controls_layout.addWidget(info_label)
        
        tts_layout.addWidget(self.tts_controls_widget)
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # Initially disable TTS controls
        self.tts_controls_widget.setEnabled(False)
        
        # Resource Folders Group
        folders_group = QGroupBox("📁 Resource Folders")
        folders_layout = QVBoxLayout()
        
        # Video Folder
        video_label = QLabel("Background Videos:")
        video_label.setStyleSheet("font-weight: bold; color: #333333;")
        folders_layout.addWidget(video_label)
        self.video_folder_input = self.create_folder_selector_compact(
            str(self.project_dir / "videos")
        )
        folders_layout.addLayout(self.video_folder_input)
        
        # Audio Folder
        audio_label = QLabel("Background Audio:")
        audio_label.setStyleSheet("font-weight: bold; color: #333333;")
        folders_layout.addWidget(audio_label)
        self.audio_folder_input = self.create_folder_selector_compact(
            str(self.project_dir / "audio")
        )
        folders_layout.addLayout(self.audio_folder_input)
        
        # Logo File
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
        
        self.logo_file_input = self.create_file_selector_compact(
            str(self.project_dir / "sources" / "logo.png"),
            "Images (*.png *.jpg *.jpeg)"
        )
        folders_layout.addLayout(self.logo_file_input)
        
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        # Initialize TTS on startup
        self.check_api_keys()
        
        layout.addStretch()
        return tab
    
    def toggle_tts_controls(self, state):
        """Enable/disable TTS controls based on checkbox"""
        enabled = (state == 2)  # Qt.Checked = 2
        self.tts_controls_widget.setEnabled(enabled)
        
        if enabled:
            self.status_label.setText("🎤 AI Voice-Over enabled! Select a provider and voice.")
            self.check_api_keys()
            self.on_provider_changed()
        else:
            self.status_label.setText("✅ Ready to create videos (without AI voices)")
    
    def check_api_keys(self):
        """Check if API keys are available in .env file"""
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        cartesia_key = os.getenv('CARTESIA_API_KEY')
        
        if elevenlabs_key:
            self.api_key_status_label.setText("✅ ElevenLabs: Connected")
            self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.api_key_status_label.setText("⚠️ Add ELEVENLABS_API_KEY to .env file")
            self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
    
    def on_provider_changed(self):
        """Handle provider selection change"""
        provider_text = self.tts_provider_combo.currentText()
        
        if "ElevenLabs" in provider_text:
            self.load_voices_for_provider("elevenlabs")
        elif "Cartesia" in provider_text:
            self.load_voices_for_provider("cartesia")
    
    def load_voices_for_provider(self, provider_name):
        """Load available voices for the selected provider"""
        self.voice_combo.clear()
        self.voice_combo.addItem("Loading voices...")
        self.test_voice_btn.setEnabled(False)
        
        try:
            # Get API key
            if provider_name == "elevenlabs":
                api_key = os.getenv('ELEVENLABS_API_KEY')
                if not api_key:
                    self.voice_combo.clear()
                    self.voice_combo.addItem("⚠️ No API key found in .env")
                    self.api_key_status_label.setText("⚠️ Add ELEVENLABS_API_KEY to .env file")
                    self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                    return
                
                # Create provider
                if 'elevenlabs' not in self.tts_providers:
                    self.tts_providers['elevenlabs'] = ElevenLabsTTS(api_key=api_key)
                
                provider = self.tts_providers['elevenlabs']
                self.api_key_status_label.setText("✅ ElevenLabs: Connected")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                
            else:  # cartesia
                api_key = os.getenv('CARTESIA_API_KEY')
                if not api_key:
                    self.voice_combo.clear()
                    self.voice_combo.addItem("⚠️ No API key found in .env")
                    self.api_key_status_label.setText("⚠️ Add CARTESIA_API_KEY to .env file")
                    self.api_key_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                    return
                
                # Create provider
                if 'cartesia' not in self.tts_providers:
                    self.tts_providers['cartesia'] = CartesiaTTS(api_key=api_key)
                
                provider = self.tts_providers['cartesia']
                self.api_key_status_label.setText("✅ Cartesia: Connected")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Get voices
            voices = provider.get_available_voices()
            self.current_voices = voices
            
            # Populate combo box
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
        """Test the selected voice by generating a sample"""
        if self.voice_combo.currentIndex() < 0:
            return
        
        try:
            self.test_voice_btn.setEnabled(False)
            self.test_voice_btn.setText("🔄 Generating...")
            
            # Get selected provider and voice
            provider_text = self.tts_provider_combo.currentText()
            provider_name = "elevenlabs" if "ElevenLabs" in provider_text else "cartesia"
            voice_id = self.voice_combo.currentData()
            voice_name = self.voice_combo.currentText().split(" - ")[0]
            
            # Get provider
            provider = self.tts_providers.get(provider_name)
            if not provider:
                raise Exception("Provider not initialized")
            
            # Generate test audio
            test_text = f"Hello! This is a test of the {voice_name} voice. This is how your videos will sound with AI narration!"
            output_path = f"test_voice_{provider_name}.mp3"
            
            self.status_label.setText(f"🎤 Generating test audio with {voice_name}...")
            
            provider.generate_audio(
                text=test_text,
                voice_id=voice_id,
                output_path=output_path
            )
            
            self.status_label.setText(f"✅ Test audio created! Listen to: {output_path}")
            
            # Try to play it (Windows only)
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
    
    def create_folder_selector_compact(self, default_path):
        """Create compact folder selection widgets"""
        layout = QHBoxLayout()
        
        input_field = QLineEdit(default_path)
        input_field.setReadOnly(True)
        input_field.setStyleSheet("background-color: #f9f9f9; color: #333333;")
        layout.addWidget(input_field)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setMaximumWidth(100)
        browse_btn.setStyleSheet("color: #333333; background-color: #f0f0f0;")
        browse_btn.clicked.connect(lambda: self.browse_folder(input_field))
        layout.addWidget(browse_btn)
        
        # Map to proper attribute names
        if "videos" in default_path.lower():
            self.background_videos_field = input_field
        elif "audio" in default_path.lower():
            self.audio_files_field = input_field
        
        return layout
    
    def create_file_selector_compact(self, default_path, file_filter):
        """Create compact file selection widgets"""
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
        """Enable or disable logo input based on checkbox"""
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
    
    def browse_folder(self, input_field):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            input_field.setText(folder)
    
    def browse_file(self, input_field, file_filter):
        """Open file browser dialog"""
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if file:
            input_field.setText(file)
    
    def create_content_tab(self):
        """Create the content selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Content Selection Group
        content_group = QGroupBox("📚 Content Selection")
        content_layout = QVBoxLayout()
        
        # Dropdown and refresh
        type_layout = QHBoxLayout()
        type_label = QLabel("Content Type:")
        type_label.setStyleSheet("color: #333333;")
        type_layout.addWidget(type_label)
        
        self.content_type = QComboBox()
        self.content_type.setMinimumWidth(300)
        self.content_type.setStyleSheet("color: #333333; background-color: white;")
        self.load_content_files()
        self.content_type.currentTextChanged.connect(self.on_content_type_changed)
        type_layout.addWidget(self.content_type)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.setToolTip("Reload content file list")
        refresh_btn.setStyleSheet("color: #333333; background-color: #f0f0f0;")
        refresh_btn.clicked.connect(self.load_content_files)
        type_layout.addWidget(refresh_btn)
        
        browse_btn = QPushButton("📁")
        browse_btn.setMaximumWidth(40)
        browse_btn.setToolTip("Browse for a custom JSON file")
        browse_btn.setStyleSheet("color: #333333; background-color: #f0f0f0;")
        browse_btn.clicked.connect(self.browse_custom_json)
        type_layout.addWidget(browse_btn)
        
        type_layout.addStretch()
        content_layout.addLayout(type_layout)
        
        # Current file path
        path_layout = QHBoxLayout()
        path_label = QLabel("File:")
        path_label.setStyleSheet("color: #333333;")
        path_layout.addWidget(path_label)
        self.selected_json_file_field = QLineEdit()
        self.selected_json_file_field.setReadOnly(True)
        self.selected_json_file_field.setStyleSheet("background-color: #f0f0f0; color: #666666;")
        path_layout.addWidget(self.selected_json_file_field)
        content_layout.addLayout(path_layout)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Preview Area
        preview_group = QGroupBox("📖 Content Preview")
        preview_layout = QVBoxLayout()
        
        preview_controls = QHBoxLayout()
        preview_btn = QPushButton("🔍 Preview Content")
        preview_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 5px;")
        preview_btn.clicked.connect(self.preview_content)
        preview_controls.addWidget(preview_btn)
        
        self.preview_info_label = QLabel("Select a content type and click Preview")
        self.preview_info_label.setStyleSheet("color: #666; font-style: italic;")
        preview_controls.addWidget(self.preview_info_label)
        preview_controls.addStretch()
        
        preview_layout.addLayout(preview_controls)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(250)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                color: #333333;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Quick Actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("📁 Open Content Folder")
        open_folder_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 8px;")
        open_folder_btn.clicked.connect(self.open_content_folder)
        actions_layout.addWidget(open_folder_btn)
        
        create_file_btn = QPushButton("➕ Create New Content File")
        create_file_btn.setStyleSheet("color: #333333; background-color: #f0f0f0; padding: 8px;")
        create_file_btn.clicked.connect(self.show_create_content_help)
        actions_layout.addWidget(create_file_btn)
        
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return tab
    
    def load_content_files(self):
        """Dynamically load all JSON files from verses_data folder"""
        verses_data_folder = self.project_dir / "sources" / "verses_data"
        
        if not verses_data_folder.exists():
            verses_data_folder.mkdir(parents=True, exist_ok=True)
        
        self.content_type.clear()
        json_files = list(verses_data_folder.glob("*.json"))
        
        if not json_files:
            self.content_type.addItem("⚠️ No content files found - Create one!")
            if hasattr(self, 'status_label'):
                self.status_label.setText("⚠️ No JSON files found in sources/verses_data folder.")
            return
        
        self.content_file_mapping = {}
        
        for json_file in sorted(json_files):
            display_name = self.create_display_name(json_file.name)
            self.content_type.addItem(display_name)
            self.content_file_mapping[display_name] = str(json_file)
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"✅ Found {len(json_files)} content file(s)!")
        
        if self.content_type.count() > 0 and hasattr(self, 'selected_json_file_field'):
            first_item = self.content_type.itemText(0)
            if first_item in self.content_file_mapping:
                self.selected_json_file_field.setText(self.content_file_mapping[first_item])
                if hasattr(self, 'preview_text'):
                    self.preview_content()
    
    def create_display_name(self, filename):
        """Convert filename to friendly display name"""
        name = filename.replace('.json', '')
        name = name.replace('_', ' ').replace('-', ' ')
        name = ' '.join(word.capitalize() for word in name.split())
        return name
    
    def on_content_type_changed(self, content_type):
        """Handle content type selection changes"""
        if content_type.startswith("⚠️"):
            return
        
        if hasattr(self, 'content_file_mapping') and content_type in self.content_file_mapping:
            file_path = self.content_file_mapping[content_type]
            
            if hasattr(self, 'selected_json_file_field'):
                self.selected_json_file_field.setText(file_path)
                self.preview_content()
    
    def open_content_folder(self):
        """Open the verses_data folder in File Explorer"""
        verses_data_folder = self.project_dir / "sources" / "verses_data"
        
        if not verses_data_folder.exists():
            verses_data_folder.mkdir(parents=True, exist_ok=True)
        
        import subprocess
        subprocess.Popen(f'explorer "{verses_data_folder}"')
    
    def show_create_content_help(self):
        """Show help dialog for creating new content files"""
        help_text = """
📝 Creating New Content Files

1. Open the content folder (click "Open Content Folder" button)

2. Create a new file with a .json extension
   Example: my_quotes.json

3. Use this format:

{
    "verses": [
        "Your first quote here",
        "Your second quote here",
        "Your third quote here"
    ],
    "references": [
        "Source 1",
        "Source 2",
        "Source 3"
    ]
}

4. Save the file

5. Click the 🔄 button to refresh the list

6. Your new content will appear in the dropdown!

💡 Tips:
• Use descriptive filenames (e.g., fitness_motivation.json)
• Make sure quotes and references have the same count
• Test with JSONLint.com if you get errors
        """
        
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #333333;
                font-size: 10pt;
            }
            QMessageBox QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Create New Content")
        msg_box.setText(help_text)
        msg_box.exec()
    
    def browse_custom_json(self):
        """Browse for a custom JSON file"""
        file, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Content JSON File", 
            str(self.project_dir / "sources" / "verses_data"),
            "JSON Files (*.json)"
        )
        if file and hasattr(self, 'selected_json_file_field'):
            self.selected_json_file_field.setText(file)
            if hasattr(self, 'preview_info_label'):
                self.preview_info_label.setText("Custom file selected")
            self.preview_content()
    
    def preview_content(self):
        """Preview the selected content"""
        if not hasattr(self, 'selected_json_file_field'):
            return
            
        try:
            json_file = self.selected_json_file_field.text()
            
            if not json_file or json_file.startswith("⚠️"):
                if hasattr(self, 'preview_text'):
                    self.preview_text.setText("⚠️ Please select a content file first.")
                return
            
            if not os.path.exists(json_file):
                if hasattr(self, 'preview_text'):
                    self.preview_text.setText(f"⚠️ File not found: {json_file}")
                return
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            verses = data.get('verses', [])
            refs = data.get('references', [])
            
            if not verses:
                if hasattr(self, 'preview_text'):
                    self.preview_text.setText("⚠️ This file contains no verses.")
                return
            
            preview = f"📊 Total Items: {len(verses)}\n"
            preview += f"📁 File: {os.path.basename(json_file)}\n"
            preview += "=" * 70 + "\n\n"
            
            for i in range(min(3, len(verses))):
                preview += f"#{i+1} {refs[i] if i < len(refs) else 'No reference'}\n"
                preview += f"{verses[i][:200]}{'...' if len(verses[i]) > 200 else ''}\n\n"
            
            if len(verses) > 3:
                preview += "=" * 70 + "\n"
                preview += f"... and {len(verses) - 3} more items\n"
            
            if hasattr(self, 'preview_text'):
                self.preview_text.setText(preview)
            
            if hasattr(self, 'preview_info_label'):
                self.preview_info_label.setText(f"✅ Loaded {len(verses)} items")
                self.preview_info_label.setStyleSheet("color: #4CAF50; font-style: italic; font-weight: bold;")
            
        except Exception as e:
            if hasattr(self, 'preview_text'):
                self.preview_text.setText(f"❌ Error loading content: {str(e)}")
    
    def create_generation_tab(self):
        """Create the video generation tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quick Summary
        summary_group = QGroupBox("📊 Generation Summary")
        summary_layout = QVBoxLayout()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(120)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f0f8ff;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
                color: #333333;
            }
        """)
        self.summary_text.setText("Configure your settings in the Settings and Content tabs, then click Generate Videos below.")
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Generation Controls
        controls_group = QGroupBox("🎬 Generation Controls")
        controls_layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎬 Generate Videos")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.generate_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setMaximumWidth(120)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(button_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Progress Group
        progress_group = QGroupBox("📈 Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                font-size: 12pt;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to start")
        self.progress_label.setStyleSheet("font-size: 11pt; padding: 5px; color: #333333;")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Output Log Group
        log_group = QGroupBox("📋 Output Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border-radius: 5px;
                padding: 10px;
            }
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
        """Open the output folder in File Explorer"""
        customer_name = self.customer_name_input.text()
        output_path = self.project_dir / "customers" / customer_name
        
        if output_path.exists():
            import subprocess
            subprocess.Popen(f'explorer "{output_path}"')
        else:
            msg_box = QMessageBox(self)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #333333;
                    font-size: 10pt;
                }
            """)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Folder Not Found")
            msg_box.setText(f"Output folder doesn't exist yet.\n\nPath: {output_path}")
            msg_box.exec()
    
    def start_generation(self):
        """Start video generation process"""
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
        """Validate all inputs before generation"""
        video_folder = self.background_videos_field.text()
        if not os.path.exists(video_folder):
            self.show_styled_message("Warning", f"Video folder not found: {video_folder}", QMessageBox.Icon.Warning)
            return False
        
        audio_folder = self.audio_files_field.text()
        if not os.path.exists(audio_folder):
            self.show_styled_message("Warning", f"Audio folder not found: {audio_folder}", QMessageBox.Icon.Warning)
            return False
        
        video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')]
        if not video_files:
            self.show_styled_message("Warning", "No MP4 files in video folder!", QMessageBox.Icon.Warning)
            return False
        
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
        if not audio_files:
            self.show_styled_message("Warning", "No MP3 files in audio folder!", QMessageBox.Icon.Warning)
            return False
        
        return True
    
    def show_styled_message(self, title, message, icon=QMessageBox.Icon.Information):
        """Show a styled message box"""
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #333333;
                font-size: 10pt;
            }
            QMessageBox QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
        """)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def get_configuration(self):
        """Get all configuration settings"""
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
        
        # TTS settings
        use_tts = self.use_tts_checkbox.isChecked()
        tts_provider = None
        tts_voice_id = None
        
        if use_tts:
            provider_text = self.tts_provider_combo.currentText()
            tts_provider = "elevenlabs" if "ElevenLabs" in provider_text else "cartesia"
            tts_voice_id = self.voice_combo.currentData()
        
        return {
            'video_folder': self.background_videos_field.text(),
            'audio_folder': self.audio_files_field.text(),
            'json_file': self.selected_json_file_field.text(),
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
        """Update generation summary"""
        content_type = self.content_type.currentText()
        json_file = self.selected_json_file_field.text()
        
        item_count = "Unknown"
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    item_count = len(data.get('verses', []))
        except:
            pass
        
        logo_status = "✓ Enabled" if self.use_logo_checkbox.isChecked() else "✗ Disabled"
        
        # TTS status
        tts_status = "✗ Disabled"
        if self.use_tts_checkbox.isChecked():
            provider = self.tts_provider_combo.currentText()
            voice = self.voice_combo.currentText()
            tts_status = f"✓ Enabled ({provider.split(' ')[0]}: {voice.split(' - ')[0]})"
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              🎬 GENERATION CONFIGURATION                      ║
╚══════════════════════════════════════════════════════════════╝

👤 Customer/Project: {self.customer_name_input.text()}
🎥 Videos to Create: {self.num_videos_input.value()}
📝 Content Type: {content_type}
📊 Available Content: {item_count} items

📁 Resources:
   • Videos: {os.path.basename(self.background_videos_field.text())}
   • Audio: {os.path.basename(self.audio_files_field.text())}
   • Logo: {logo_status}
   • AI Voice: {tts_status}

✅ Ready to generate!
        """
        self.summary_text.setText(summary.strip())
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update status message"""
        self.progress_label.setText(message)
        self.log_text.append(message)
    
    def generation_finished(self, success, message):
        """Handle generation completion"""
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
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    
    window = ShortsMakerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()