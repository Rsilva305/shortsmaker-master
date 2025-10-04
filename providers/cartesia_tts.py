"""
Cartesia TTS Provider
Cartesia provides ultra-fast, low-latency AI voices!
Known for: Speed, natural sound, and emotional control
"""

from typing import List, Dict
import os
from cartesia import Cartesia

from providers.base_tts import BaseTTSProvider


class CartesiaTTS(BaseTTSProvider):
    """
    Cartesia voice generator!
    Super fast generation with natural-sounding voices
    """
    
    def __init__(self, api_key: str):
        """
        Set up Cartesia with your API key
        
        Args:
            api_key: Your Cartesia API key
        """
        super().__init__(api_key)
        self.provider_name = "Cartesia"
        
        # Create the Cartesia client
        self.client = Cartesia(api_key=api_key)
        
        # Default model (Cartesia's best English model)
        self.default_model = "sonic-english"
    
    def generate_audio(self, text: str, voice_id: str, output_path: str, **kwargs) -> str:
        """
        Turn text into speech using Cartesia!
        
        Args:
            text: What you want the voice to say
            voice_id: Which voice to use (Cartesia voice ID)
            output_path: Where to save the audio file
            **kwargs: Optional settings:
                - model: Which model to use (default: "sonic-english")
        
        Returns:
            The path where the audio was saved
        """
        
        # Get settings
        model = kwargs.get('model', self.default_model)
        
        try:
            print(f"🎤 Generating audio with Cartesia...")
            print(f"   Voice: {voice_id}")
            print(f"   Text length: {len(text)} characters")
            print(f"   Model: {model}")
            
            # Make the folder if it doesn't exist (only if there's a folder path)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # THIS IS THE MAGIC! Generate the audio using Cartesia's API
            # Cartesia returns a generator, so we need to collect all chunks
            audio_generator = self.client.tts.bytes(
                model_id=model,
                transcript=text,
                voice={"mode": "id", "id": voice_id},
                output_format={
                    "container": "mp3",
                    "encoding": "mp3",
                    "sample_rate": 44100
                },
                language="en"
            )
            
            # Collect all audio chunks from the generator
            audio_data = b""
            for chunk in audio_generator:
                # Each chunk is a dictionary with 'audio' key
                if isinstance(chunk, dict) and 'audio' in chunk:
                    audio_data += chunk['audio']
                elif isinstance(chunk, bytes):
                    audio_data += chunk
            
            # Save the complete audio to a file
            with open(output_path, 'wb') as audio_file:
                audio_file.write(audio_data)
            
            print(f"   ✅ Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ ERROR generating audio: {str(e)}")
            import traceback
            traceback.print_exc()  # This will show us more details
            raise Exception(f"Cartesia audio generation failed: {str(e)}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get all available Cartesia voices
        
        Returns:
            List of voices with their info
        """
        try:
            # Get voices from Cartesia
            voices_response = self.client.voices.list()
            
            voices_list = []
            for voice in voices_response:
                # Cartesia voice objects have different structure
                voice_dict = voice if isinstance(voice, dict) else voice.__dict__
                
                voices_list.append({
                    'id': voice_dict.get('id', ''),
                    'name': voice_dict.get('name', 'Unknown'),
                    'description': voice_dict.get('description', f"{voice_dict.get('name', 'Voice')} - Cartesia voice")
                })
            
            return voices_list
            
        except Exception as e:
            print(f"❌ Error getting voices: {str(e)}")
            # Return some popular Cartesia voices as fallback
            return [
                {
                    'id': 'a0e99841-438c-4a64-b679-ae501e7d6091',
                    'name': 'Barbershop Man',
                    'description': 'Friendly, conversational male voice'
                },
                {
                    'id': '79a125e8-cd45-4c13-8a67-188112f4dd22',
                    'name': 'British Lady',
                    'description': 'Professional British female voice'
                },
                {
                    'id': '5619d38c-cf51-4d8e-9575-48f61a280413',
                    'name': 'Calm Lady',
                    'description': 'Soothing, gentle female voice'
                },
                {
                    'id': '421b3369-f63f-4b03-8980-37a44df1d4e8',
                    'name': 'Friendly Sidekick',
                    'description': 'Energetic, upbeat voice'
                },
            ]
    
    def estimate_duration(self, text: str) -> float:
        """
        Estimate how long the audio will be
        
        Cartesia speaks at about 160 words per minute (slightly faster than average)
        
        Args:
            text: The text that will be spoken
            
        Returns:
            Estimated duration in seconds
        """
        # Count words
        word_count = len(text.split())
        
        # Cartesia is known for natural, slightly faster speech
        # 160 words per minute = 2.67 words per second
        words_per_second = 2.67
        
        # Calculate duration
        duration = word_count / words_per_second
        
        # Add a small buffer
        duration += 0.4
        
        return duration
    
    def get_character_count(self, text: str) -> int:
        """
        Count characters for tracking usage
        
        Args:
            text: The text to count
            
        Returns:
            Number of characters
        """
        return len(text)
    
    def supports_streaming(self) -> bool:
        """
        Cartesia supports streaming (it's one of their key features!)
        This means audio starts playing while it's still being generated
        """
        return True
    
    def get_cost_estimate(self, text: str) -> Dict[str, float]:
        """
        Estimate how much this will cost
        
        Returns:
            Dictionary with character count and estimated cost
        """
        char_count = self.get_character_count(text)
        
        # Cartesia pricing (approximate, check their website for current rates)
        # They charge by character
        cost_per_1000_chars = 0.15  # Approximate
        estimated_cost = (char_count / 1000) * cost_per_1000_chars
        
        return {
            'characters': char_count,
            'estimated_cost_usd': round(estimated_cost, 4)
        }