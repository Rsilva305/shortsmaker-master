"""
ShortsMaker Pro - Modern GUI Application
Create professional quote videos for social media
"""

import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QSpinBox, QComboBox, QProgressBar, QTextEdit,
                             QFileDialog, QGroupBox, QMessageBox, QTabWidget)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon
from pathlib import Path

# Import your existing modules (we'll update these next)
import ffmpeg
from Fonts import Fonts


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
                progress_callback=self.update_progress
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
        self.content_file_mapping = {}  # Initialize mapping
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ShortsMaker Pro - Video Creator")
        self.setGeometry(100, 100, 900, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add header
        header = QLabel("🎬 ShortsMaker Pro")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Create tabs for different sections
        tabs = QTabWidget()
        tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        tabs.addTab(self.create_content_tab(), "📝 Content")
        tabs.addTab(self.create_generation_tab(), "🎥 Generate Videos")
        main_layout.addWidget(tabs)
        
        # Status bar at bottom
        self.status_label = QLabel("Ready to create amazing videos!")
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9;")
        main_layout.addWidget(self.status_label)
        
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Project Settings Group
        project_group = QGroupBox("Project Settings")
        project_layout = QVBoxLayout()
        
        # Customer Name
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Customer/Project Name:"))
        self.customer_name_input = QLineEdit("my_project")
        customer_layout.addWidget(self.customer_name_input)
        project_layout.addLayout(customer_layout)
        
        # Number of Videos
        videos_layout = QHBoxLayout()
        videos_layout.addWidget(QLabel("Number of Videos:"))
        self.num_videos_input = QSpinBox()
        self.num_videos_input.setMinimum(1)
        self.num_videos_input.setMaximum(1000)
        self.num_videos_input.setValue(10)
        videos_layout.addWidget(self.num_videos_input)
        project_layout.addLayout(videos_layout)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        # Folders Group
        folders_group = QGroupBox("Resource Folders")
        folders_layout = QVBoxLayout()
        
        # Video Folder
        self.video_folder_input = self.create_folder_selector(
            "Background Videos:", 
            str(self.project_dir / "videos")
        )
        folders_layout.addLayout(self.video_folder_input)
        
        # Audio Folder
        self.audio_folder_input = self.create_folder_selector(
            "Audio Files:", 
            str(self.project_dir / "audio")
        )
        folders_layout.addLayout(self.audio_folder_input)
        
        # Logo/Image File
        self.logo_file_input = self.create_file_selector(
            "Logo Image:", 
            str(self.project_dir / "sources" / "logo.png"),
            "Images (*.png *.jpg *.jpeg)"
        )
        folders_layout.addLayout(self.logo_file_input)
        
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        layout.addStretch()
        return tab
    
    def create_content_tab(self):
        """Create the content selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Content Type Selection
        content_group = QGroupBox("Content Type")
        content_layout = QVBoxLayout()
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Select Content Type:"))
        self.content_type = QComboBox()
        
        # Dynamically load all JSON files from verses_data folder
        self.load_content_files()
        
        self.content_type.currentTextChanged.connect(self.on_content_type_changed)
        type_layout.addWidget(self.content_type)
        
        # Add refresh button to reload file list
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.clicked.connect(self.load_content_files)
        refresh_btn.setToolTip("Reload the list of available content files")
        type_layout.addWidget(refresh_btn)
        
        content_layout.addLayout(type_layout)
        
        # JSON File selector (shows currently selected file)
        self.json_file_layout = self.create_file_selector(
            "Selected JSON File:",
            str(self.project_dir / "sources" / "verses_data" / "love_data.json"),
            "JSON Files (*.json)"
        )
        content_layout.addLayout(self.json_file_layout)
        
        # Browse for custom file button
        browse_custom_layout = QHBoxLayout()
        browse_custom_btn = QPushButton("📁 Browse for Different File...")
        browse_custom_btn.clicked.connect(self.browse_custom_json)
        browse_custom_layout.addWidget(browse_custom_btn)
        content_layout.addLayout(browse_custom_layout)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Preview Area
        preview_group = QGroupBox("Content Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        preview_btn = QPushButton("📖 Preview Content")
        preview_btn.clicked.connect(self.preview_content)
        preview_layout.addWidget(preview_btn)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
        return tab
    
    def create_generation_tab(self):
        """Create the video generation tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Summary
        summary_group = QGroupBox("Generation Summary")
        summary_layout = QVBoxLayout()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to start")
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Generation Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎬 Generate Videos")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.generate_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Output Log
        log_group = QGroupBox("Output Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return tab
    
    def create_folder_selector(self, label_text, default_path):
        """Helper to create folder selection widgets"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        
        input_field = QLineEdit(default_path)
        layout.addWidget(input_field)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self.browse_folder(input_field))
        layout.addWidget(browse_btn)
        
        # Store reference to input field
        setattr(self, f"{label_text.lower().replace(' ', '_').replace(':', '')}_field", input_field)
        
        return layout
    
    def create_file_selector(self, label_text, default_path, file_filter):
        """Helper to create file selection widgets"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        
        input_field = QLineEdit(default_path)
        layout.addWidget(input_field)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self.browse_file(input_field, file_filter))
        layout.addWidget(browse_btn)
        
        # Store reference to input field
        setattr(self, f"{label_text.lower().replace(' ', '_').replace(':', '')}_field", input_field)
        
        return layout
    
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
    
    def load_content_files(self):
        """Dynamically load all JSON files from verses_data folder"""
        verses_data_folder = self.project_dir / "sources" / "verses_data"
        
        # Create folder if it doesn't exist
        if not verses_data_folder.exists():
            verses_data_folder.mkdir(parents=True, exist_ok=True)
            print(f"Created verses_data folder at: {verses_data_folder}")
        
        # Clear existing items
        self.content_type.clear()
        
        # Find all JSON files
        json_files = list(verses_data_folder.glob("*.json"))
        
        if not json_files:
            # No files found - add a message
            self.content_type.addItem("⚠️ No content files found - Create one!")
            # Only update status if it exists (might not exist during initial UI creation)
            if hasattr(self, 'status_label'):
                self.status_label.setText("⚠️ No JSON files found in sources/verses_data folder. Please add content files.")
            print("⚠️ No JSON files found in sources/verses_data folder.")
            return
        
        # Create a mapping to store file paths
        self.content_file_mapping = {}
        
        # Add each file to dropdown
        for json_file in sorted(json_files):
            # Create a friendly display name from filename
            display_name = self.create_display_name(json_file.name)
            self.content_type.addItem(display_name)
            self.content_file_mapping[display_name] = str(json_file)
        
        # Update status (only if status label exists)
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"✅ Found {len(json_files)} content file(s). Ready to create videos!")
        print(f"✅ Found {len(json_files)} content file(s)!")
        
        # Select first item and update path (only if UI is fully created)
        if self.content_type.count() > 0 and hasattr(self, 'selected_json_file_field'):
            first_item = self.content_type.itemText(0)
            if first_item in self.content_file_mapping:
                self.selected_json_file_field.setText(self.content_file_mapping[first_item])
                # Preview after everything is set up
                if hasattr(self, 'preview_text'):
                    self.preview_content()
    
    def create_display_name(self, filename):
        """Convert filename to friendly display name"""
        # Remove .json extension
        name = filename.replace('.json', '')
        
        # Replace underscores and dashes with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name
    
    def on_content_type_changed(self, content_type):
        """Handle content type selection changes"""
        # Check if this is a valid content type
        if content_type.startswith("⚠️"):
            return
        
        # Get the file path from mapping
        if hasattr(self, 'content_file_mapping') and content_type in self.content_file_mapping:
            file_path = self.content_file_mapping[content_type]
            
            # Only update field if it exists (might not during initial UI creation)
            if hasattr(self, 'selected_json_file_field'):
                self.selected_json_file_field.setText(file_path)
                
                # Auto-preview when selection changes
                self.preview_content()
    
    def browse_custom_json(self):
        """Browse for a custom JSON file anywhere on the computer"""
        file, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Content JSON File", 
            str(self.project_dir / "sources" / "verses_data"),
            "JSON Files (*.json)"
        )
        if file and hasattr(self, 'selected_json_file_field'):
            self.selected_json_file_field.setText(file)
            # Update the dropdown to show "Custom File"
            if hasattr(self, 'content_type'):
                # Don't change the dropdown, just update the path
                pass
            # Preview the content
            self.preview_content()
    
    def preview_content(self):
        """Preview the selected content"""
        # Don't preview if field doesn't exist yet (during initial UI creation)
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
                    self.preview_text.setText(f"⚠️ File not found: {json_file}\n\nPlease check the file path or use 'Browse for Different File' button.")
                return
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            verses = data.get('verses', [])
            refs = data.get('references', [])
            
            if not verses:
                if hasattr(self, 'preview_text'):
                    self.preview_text.setText("⚠️ This file contains no verses. Please check the JSON format.")
                return
            
            preview = f"📊 Total Items: {len(verses)}\n"
            preview += f"📁 File: {os.path.basename(json_file)}\n"
            preview += "=" * 60 + "\n\n"
            preview += "Sample Content (first 3):\n"
            preview += "=" * 60 + "\n\n"
            
            for i in range(min(3, len(verses))):
                preview += f"#{i+1}: {refs[i] if i < len(refs) else 'No reference'}\n"
                preview += f"{verses[i][:150]}{'...' if len(verses[i]) > 150 else ''}\n\n"
            
            if len(verses) > 3:
                preview += f"... and {len(verses) - 3} more items\n"
            
            if hasattr(self, 'preview_text'):
                self.preview_text.setText(preview)
            
        except json.JSONDecodeError as e:
            if hasattr(self, 'preview_text'):
                self.preview_text.setText(f"❌ Error: Invalid JSON format\n\n{str(e)}\n\nPlease check your JSON file syntax.")
        except Exception as e:
            if hasattr(self, 'preview_text'):
                self.preview_text.setText(f"❌ Error loading content: {str(e)}")
    
    def start_generation(self):
        """Start video generation process"""
        try:
            # Validate inputs
            if not self.validate_inputs():
                return
            
            # Update summary
            self.update_summary()
            
            # Prepare configuration
            config = self.get_configuration()
            
            # Create and start worker thread
            self.worker = VideoCreatorThread(config)
            self.worker.progress.connect(self.update_progress)
            self.worker.status.connect(self.update_status)
            self.worker.finished.connect(self.generation_finished)
            
            # Update UI
            self.generate_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.log_text.clear()
            self.log_text.append("🚀 Starting video generation...\n")
            
            # Start generation
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start generation: {str(e)}")
    
    def validate_inputs(self):
        """Validate all inputs before generation"""
        # Check folders exist
        video_folder = self.background_videos_field.text()
        if not os.path.exists(video_folder):
            QMessageBox.warning(self, "Warning", f"Video folder not found: {video_folder}")
            return False
        
        audio_folder = self.audio_files_field.text()
        if not os.path.exists(audio_folder):
            QMessageBox.warning(self, "Warning", f"Audio folder not found: {audio_folder}")
            return False
        
        # Check if folders have files
        video_files = [f for f in os.listdir(video_folder) if f.endswith('.mp4')]
        if not video_files:
            QMessageBox.warning(self, "Warning", "No MP4 files found in video folder!")
            return False
        
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
        if not audio_files:
            QMessageBox.warning(self, "Warning", "No MP3 files found in audio folder!")
            return False
        
        return True
    
    def get_configuration(self):
        """Get all configuration settings"""
        # Setup fonts (using your existing font configuration)
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
        
        return {
            'video_folder': self.background_videos_field.text(),
            'audio_folder': self.audio_files_field.text(),
            'json_file': self.selected_json_file_field.text(),
            'fonts_dir': str(self.project_dir / 'sources/fonts'),
            'output_folder': str(self.project_dir / 'customers'),
            'text_source_font': str(self.project_dir / 'sources/MouldyCheeseRegular-WyMWG.ttf').replace(':', '\\:'),
            'image_file': self.logo_image_field.text(),
            'customer_name': self.customer_name_input.text(),
            'number_of_videos': self.num_videos_input.value(),
            'fonts': fonts
        }
    
    def update_summary(self):
        """Update generation summary"""
        summary = f"""
📋 Generation Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Customer: {self.customer_name_input.text()}
🎥 Videos to create: {self.num_videos_input.value()}
📝 Content type: {self.content_type.currentText()}
🎬 Video folder: {os.path.basename(self.background_videos_field.text())}
🎵 Audio folder: {os.path.basename(self.audio_files_field.text())}

✅ All settings validated - Ready to generate!
        """
        self.summary_text.setText(summary)
    
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
            QMessageBox.information(self, "Success", message)
        else:
            self.log_text.append(f"\n❌ {message}")
            QMessageBox.critical(self, "Error", message)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))
    
    window = ShortsMakerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()