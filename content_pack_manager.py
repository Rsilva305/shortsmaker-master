"""
Content Pack Manager - SIMPLE VERSION!
Just put your JSON files in the pack folder and it loads them ALL!
"""

import os
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class ContentPack:
    """
    Represents a single content pack
    
    SIMPLE: Just loads ALL .json files from the pack folder!
    """
    
    def __init__(self, pack_path: str):
        """
        Load a content pack from a folder
        
        Args:
            pack_path: Path to the pack folder (like "content_packs/christianity/faith")
        """
        self.pack_path = Path(pack_path)
        self.info = {}
        self.quotes = []
        self.references = []
        
        # Load the pack info
        self.load_pack_info()
        
        # Load ALL quote files in this folder
        self.load_all_quotes_in_folder()
    
    def load_pack_info(self):
        """Load pack_config.json if it exists"""
        config_file = self.pack_path / "pack_config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.info = json.load(f)
        else:
            # Create basic info from folder name
            self.info = {
                'pack_name': self.pack_path.name.title(),
                'category': self.pack_path.parent.name.title(),
                'subcategory': self.pack_path.name.title(),
                'resources': {}
            }
    
    def load_all_quotes_in_folder(self):
        """
        Load ALL .json files in the pack folder (except pack_config.json)
        
        This is SIMPLE - just finds every JSON file and loads it!
        """
        print(f"\n📦 Loading pack: {self.pack_path.name}")
        
        # Find all JSON files in this folder
        all_json_files = list(self.pack_path.glob("*.json"))
        
        # Remove pack_config.json from the list
        quote_files = [f for f in all_json_files if f.name != "pack_config.json"]
        
        if not quote_files:
            print(f"   ⚠️ No quote files found in {self.pack_path}")
            return
        
        # Load each file
        total_loaded = 0
        for json_file in quote_files:
            loaded = self.load_single_quotes_file(json_file)
            if loaded > 0:
                total_loaded += loaded
                print(f"   ✅ Loaded {loaded} quotes from {json_file.name}")
        
        print(f"   📊 Total: {total_loaded} quotes from {len(quote_files)} file(s)")
    
    def load_single_quotes_file(self, json_file: Path) -> int:
        """
        Load quotes from a single JSON file
        
        Args:
            json_file: Path object to the JSON file
            
        Returns:
            Number of quotes loaded
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_quotes = data.get('verses', [])
            file_refs = data.get('references', [])
            
            if not file_quotes:
                print(f"   ⚠️ No 'verses' found in {json_file.name}")
                return 0
            
            # Append to existing quotes (combining multiple files)
            self.quotes.extend(file_quotes)
            self.references.extend(file_refs)
            
            return len(file_quotes)
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON in {json_file.name}: {str(e)}")
            return 0
        except Exception as e:
            print(f"   ❌ Error reading {json_file.name}: {str(e)}")
            return 0
    
    def get_video_files(self) -> List[str]:
        """
        Get video files from specified folders OR from pack's videos/ folder
        
        Priority:
        1. Check pack_config.json for video_folders
        2. If not specified, check for videos/ subfolder in pack
        3. If not found, return empty list
        """
        # First, check if pack_config specifies folders
        video_folders = self.info.get('resources', {}).get('video_folders', [])
        
        all_videos = []
        
        if video_folders:
            # Use specified folders
            for folder in video_folders:
                folder_path = Path(folder)
                if folder_path.exists() and folder_path.is_dir():
                    videos = list(folder_path.glob("*.mp4"))
                    videos.extend(folder_path.glob("*.mov"))
                    videos.extend(folder_path.glob("*.avi"))
                    all_videos.extend([str(v) for v in videos])
                    if videos:
                        print(f"   📹 Found {len(videos)} videos in {folder_path.name}/")
        else:
            # Check for videos/ subfolder in the pack itself
            pack_videos_folder = self.pack_path / "videos"
            if pack_videos_folder.exists() and pack_videos_folder.is_dir():
                videos = list(pack_videos_folder.glob("*.mp4"))
                videos.extend(pack_videos_folder.glob("*.mov"))
                videos.extend(pack_videos_folder.glob("*.avi"))
                all_videos.extend([str(v) for v in videos])
                if videos:
                    print(f"   📹 Found {len(videos)} videos in pack's videos/ folder")
        
        return all_videos
    
    def get_audio_files(self) -> List[str]:
        """
        Get audio files from specified folders OR from pack's audio/ folder
        
        Priority:
        1. Check pack_config.json for audio_folders
        2. If not specified, check for audio/ subfolder in pack
        3. If not found, return empty list
        """
        # First, check if pack_config specifies folders
        audio_folders = self.info.get('resources', {}).get('audio_folders', [])
        
        all_audio = []
        
        if audio_folders:
            # Use specified folders
            for folder in audio_folders:
                folder_path = Path(folder)
                if folder_path.exists() and folder_path.is_dir():
                    audio = list(folder_path.glob("*.mp3"))
                    audio.extend(folder_path.glob("*.wav"))
                    audio.extend(folder_path.glob("*.m4a"))
                    all_audio.extend([str(a) for a in audio])
                    if audio:
                        print(f"   🎵 Found {len(audio)} audio files in {folder_path.name}/")
        else:
            # Check for audio/ subfolder in the pack itself
            pack_audio_folder = self.pack_path / "audio"
            if pack_audio_folder.exists() and pack_audio_folder.is_dir():
                audio = list(pack_audio_folder.glob("*.mp3"))
                audio.extend(pack_audio_folder.glob("*.wav"))
                audio.extend(pack_audio_folder.glob("*.m4a"))
                all_audio.extend([str(a) for a in audio])
                if audio:
                    print(f"   🎵 Found {len(audio)} audio files in pack's audio/ folder")
        
        return all_audio
    
    def get_display_name(self) -> str:
        """Get a nice display name like 'Christianity → Faith'"""
        category = self.info.get('category', 'Unknown')
        subcategory = self.info.get('subcategory', 'Unknown')
        return f"{category} → {subcategory}"
    
    def get_quote_count(self) -> int:
        """How many quotes are in this pack?"""
        return len(self.quotes)
    
    def get_resource_summary(self) -> Dict[str, int]:
        """Get a summary of available resources"""
        return {
            'quotes': len(self.quotes),
            'videos': len(self.get_video_files()),
            'audio': len(self.get_audio_files())
        }
    
    def get_quotes_and_references(self, randomize: bool = True, count: int = None) -> Tuple[List[str], List[str]]:
        """
        Get quotes and references from this pack
        
        Args:
            randomize: Should we shuffle them?
            count: How many do we need?
            
        Returns:
            Tuple of (quotes, references)
        """
        import random
        
        if not self.quotes:
            return [], []
        
        if randomize:
            quotes_copy = self.quotes.copy()
            refs_copy = self.references.copy()
            
            combined = list(zip(quotes_copy, refs_copy))
            random.shuffle(combined)
            quotes_shuffled, refs_shuffled = zip(*combined) if combined else ([], [])
            quotes_shuffled = list(quotes_shuffled)
            refs_shuffled = list(refs_shuffled)
            
            if count and count > len(quotes_shuffled):
                times_to_repeat = (count // len(quotes_shuffled)) + 1
                
                all_quotes = []
                all_refs = []
                
                for i in range(times_to_repeat):
                    combined = list(zip(self.quotes.copy(), self.references.copy()))
                    random.shuffle(combined)
                    q, r = zip(*combined) if combined else ([], [])
                    all_quotes.extend(q)
                    all_refs.extend(r)
                
                return all_quotes[:count], all_refs[:count]
            
            return quotes_shuffled, refs_shuffled
        
        else:
            if count:
                times_to_repeat = (count // len(self.quotes)) + 1
                repeated_quotes = self.quotes * times_to_repeat
                repeated_refs = self.references * times_to_repeat
                return repeated_quotes[:count], repeated_refs[:count]
            
            return self.quotes.copy(), self.references.copy()


class ContentPackManager:
    """Manages ALL content packs"""
    
    def __init__(self, content_packs_folder: str = "content_packs"):
        """Initialize the manager"""
        self.content_packs_folder = Path(content_packs_folder)
        self.packs: Dict[str, ContentPack] = {}
        self.scan_packs()
    
    def scan_packs(self):
        """Scan the content_packs folder and find all packs"""
        if not self.content_packs_folder.exists():
            print(f"⚠️ Warning: {self.content_packs_folder} folder not found!")
            print(f"Creating it now...")
            self.content_packs_folder.mkdir(parents=True, exist_ok=True)
            return
        
        print(f"\n🔍 Scanning for content packs in {self.content_packs_folder}...")
        
        # Find all pack folders (2 levels: category/subcategory)
        for category_folder in self.content_packs_folder.iterdir():
            if category_folder.is_dir():
                for pack_folder in category_folder.iterdir():
                    if pack_folder.is_dir():
                        # Any folder with JSON files is a pack!
                        json_files = list(pack_folder.glob("*.json"))
                        
                        if json_files:
                            pack_key = f"{category_folder.name}/{pack_folder.name}"
                            self.packs[pack_key] = ContentPack(str(pack_folder))
                            
                            pack = self.packs[pack_key]
                            resources = pack.get_resource_summary()
                            print(f"   ✅ {resources['quotes']} quotes, {resources['videos']} videos, {resources['audio']} audio")
        
        print(f"\n✅ Total packs loaded: {len(self.packs)}\n")
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = set()
        for pack in self.packs.values():
            categories.add(pack.info.get('category', 'Unknown'))
        return sorted(list(categories))
    
    def get_topics_in_category(self, category: str) -> List[Dict[str, str]]:
        """Get all topics in a category"""
        topics = []
        for pack_key, pack in self.packs.items():
            if pack.info.get('category', '') == category:
                resources = pack.get_resource_summary()
                topics.append({
                    'key': pack_key,
                    'name': pack.info.get('subcategory', pack_key.split('/')[-1]),
                    'display_name': pack.get_display_name(),
                    'quote_count': resources['quotes'],
                    'video_count': resources['videos'],
                    'audio_count': resources['audio'],
                    'description': pack.info.get('description', '')
                })
        
        return sorted(topics, key=lambda x: x['name'])
    
    def get_pack(self, pack_key: str) -> Optional[ContentPack]:
        """Get a specific pack by its key"""
        return self.packs.get(pack_key)
    
    def get_all_packs(self) -> Dict[str, ContentPack]:
        """Get all loaded packs"""
        return self.packs


if __name__ == "__main__":
    print("🔍 Testing Content Pack Manager...\n")
    manager = ContentPackManager()
    
    print(f"\n📊 Found {len(manager.packs)} content packs!\n")
    
    for pack_key, pack in manager.packs.items():
        resources = pack.get_resource_summary()
        print(f"{pack.get_display_name()}")
        print(f"   Quotes: {resources['quotes']}")
        print(f"   Videos: {resources['videos']}")
        print(f"   Audio: {resources['audio']}\n")