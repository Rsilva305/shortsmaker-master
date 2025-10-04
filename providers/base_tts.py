"""
Base TTS Provider - Blueprint for all voice services
This is like a recipe card that says what every voice service needs to do
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseTTSProvider(ABC):
    """
    This is the BLUEPRINT for voice services.
    Every voice service (ElevenLabs, Cartesia, etc.) will follow this pattern.
    
    Think of it like a job description - it says "you must be able to do these things"
    """
    
    def __init__(self, api_key: str):
        """
        When you create a voice service, you need to give it an API key
        (API key is like a password to use the service)
        
        Args:
            api_key: Your secret key from ElevenLabs, Cartesia, etc.
        """
        self.api_key = api_key
        self.provider_name = "Base Provider"
    
    @abstractmethod
    def generate_audio(self, text: str, voice_id: str, output_path: str, **kwargs) -> str:
        """
        THIS IS THE MAIN JOB: Turn text into speech!
        
        Args:
            text: The words you want spoken (like "Hello, welcome to my channel")
            voice_id: Which voice to use (like "Rachel" or "calm-male-voice")
            output_path: Where to save the audio file (like "C:/audio/verse1.mp3")
            **kwargs: Extra settings (speed, pitch, etc.)
            
        Returns:
            str: The path where the audio was saved
            
        Example:
            generate_audio(
                text="Be strong and courageous", 
                voice_id="rachel",
                output_path="C:/audio/verse1.mp3"
            )
            → Returns: "C:/audio/verse1.mp3" (file is created!)
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get a list of all voices you can use
        
        Returns:
            A list of voices, each with 'id', 'name', and 'description'
            
        Example return:
            [
                {
                    'id': 'voice_abc123',
                    'name': 'Rachel',
                    'description': 'Calm, warm female voice'
                },
                {
                    'id': 'voice_xyz789',
                    'name': 'Adam',
                    'description': 'Deep, authoritative male voice'
                }
            ]
        """
        pass
    
    @abstractmethod
    def estimate_duration(self, text: str) -> float:
        """
        Figure out how long the audio will be (in seconds)
        This helps us know if we need to loop the video!
        
        Args:
            text: The text that will be spoken
            
        Returns:
            float: Number of seconds (like 12.5 seconds)
            
        Example:
            estimate_duration("Be kind") → 2.3 seconds
            estimate_duration("Long bible verse here...") → 45.8 seconds
        """
        pass
    
    def validate_api_key(self) -> bool:
        """
        Check if your API key actually works
        
        Returns:
            True if the key works, False if it doesn't
            
        This tries to get voices - if that works, your key is good!
        """
        try:
            voices = self.get_available_voices()
            return len(voices) > 0
        except:
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this voice service (like "ElevenLabs" or "Cartesia")"""
        return self.provider_name
    
    def supports_streaming(self) -> bool:
        """
        Can this service generate audio bit-by-bit as it speaks?
        (Most don't, so we default to False)
        """
        return False
    
    def get_default_voice(self) -> str:
        """
        Get a good default voice to use
        Returns the first available voice
        """
        voices = self.get_available_voices()
        return voices[0]['id'] if voices else None