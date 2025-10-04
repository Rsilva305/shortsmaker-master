"""
ElevenLabs TTS Provider
This connects to ElevenLabs and generates realistic AI voices!
"""

from typing import List, Dict
import os
from elevenlabs.client import ElevenLabs

from providers.base_tts import BaseTTSProvider


class ElevenLabsTTS(BaseTTSProvider):
    """
    ElevenLabs voice generator!
    This creates super realistic AI voices for your videos.
    """
    
    def __init__(self, api_key: str):
        """
        Set up ElevenLabs with your API key
        
        Args:
            api_key: Your ElevenLabs API key (starts with 'sk_')
        """
        super().__init__(api_key)
        self.provider_name = "ElevenLabs"
        
        # Create the ElevenLabs client (this is what talks to their service)
        self.client = ElevenLabs(api_key=api_key)
    
    def generate_audio(self, text: str, voice_id: str, output_path: str, **kwargs) -> str:
        """
        Turn text into speech and save it as an audio file!
        
        Args:
            text: What you want the voice to say
            voice_id: Which voice to use
            output_path: Where to save the MP3 file
            **kwargs: Optional settings
        
        Returns:
            The path where the audio was saved
        """
        
        # Get settings from kwargs
        model = kwargs.get('model', 'eleven_multilingual_v2')
        
        try:
            print(f"🎤 Generating audio with ElevenLabs...")
            print(f"   Voice: {voice_id}")
            print(f"   Text length: {len(text)} characters")
            
            # Make the folder if it doesn't exist (only if there's a folder path)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # THIS IS THE MAGIC! Generate the audio using the new API
            # The new ElevenLabs SDK uses text_to_speech.convert()
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=model
            )
            
            # Save it to a file
            # The new API returns an iterator of audio chunks
            with open(output_path, 'wb') as audio_file:
                for chunk in audio_generator:
                    if chunk:
                        audio_file.write(chunk)
            
            print(f"   ✅ Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ ERROR generating audio: {str(e)}")
            raise Exception(f"ElevenLabs audio generation failed: {str(e)}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get all the voices you can use with your account
        
        Returns:
            List of voices with their info
        """
        try:
            # Ask ElevenLabs for all available voices using the new API
            voices_response = self.client.voices.get_all()
            
            voices_list = []
            for voice in voices_response.voices:
                voices_list.append({
                    'id': voice.voice_id,
                    'name': voice.name,
                    'description': voice.description if voice.description else f"{voice.name} voice"
                })
            
            return voices_list
            
        except Exception as e:
            print(f"❌ Error getting voices: {str(e)}")
            # Return some common default voices if we can't get the list
            return [
                {'id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Rachel', 'description': 'Calm, warm female voice'},
                {'id': 'pNInz6obpgDQGcFmaJgB', 'name': 'Adam', 'description': 'Deep, authoritative male voice'},
            ]
    
    def estimate_duration(self, text: str) -> float:
        """
        Estimate how long the audio will be
        
        Args:
            text: The text that will be spoken
            
        Returns:
            Estimated duration in seconds
        """
        # Count words
        word_count = len(text.split())
        
        # Average speaking speed: 150 words per minute = 2.5 words per second
        words_per_second = 2.5
        
        # Calculate duration
        duration = word_count / words_per_second
        
        # Add a little buffer for pauses
        duration += 0.5
        
        return duration
    
    def get_character_count(self, text: str) -> int:
        """
        Count characters (useful for tracking your API usage!)
        
        Args:
            text: The text to count
            
        Returns:
            Number of characters
        """
        return len(text)
    
    def get_cost_estimate(self, text: str) -> Dict[str, float]:
        """
        Estimate how much this will cost
        
        Returns:
            Dictionary with character count and estimated cost
        """
        char_count = self.get_character_count(text)
        
        # Cost estimation based on ElevenLabs pricing
        cost_per_1000_chars = 0.18
        estimated_cost = (char_count / 1000) * cost_per_1000_chars
        
        return {
            'characters': char_count,
            'estimated_cost_usd': round(estimated_cost, 4)
        }