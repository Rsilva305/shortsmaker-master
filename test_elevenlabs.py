"""
Test ElevenLabs Voice Generation
This will create a test audio file to make sure everything works!
"""

from providers.elevenlabs_tts import ElevenLabsTTS

# PASTE YOUR API KEY HERE (between the quotes)
API_KEY = "sk_7b6d94b99b13d7366818b7a6599976d97fb53acdc89c10d5"  # ← PUT YOUR REAL KEY HERE!

def test_elevenlabs():
    """Test if ElevenLabs works!"""
    
    print("=" * 60)
    print("🎤 TESTING ELEVENLABS")
    print("=" * 60)
    
    # Step 1: Create the voice generator
    print("\n1️⃣ Creating ElevenLabs voice generator...")
    tts = ElevenLabsTTS(api_key=API_KEY)
    print("   ✅ Voice generator created!")
    
    # Step 2: Check if API key works
    print("\n2️⃣ Checking if your API key works...")
    if tts.validate_api_key():
        print("   ✅ API key is valid!")
    else:
        print("   ❌ API key doesn't work! Check if you copied it correctly.")
        return
    
    # Step 3: Get available voices
    print("\n3️⃣ Getting available voices...")
    voices = tts.get_available_voices()
    print(f"   ✅ Found {len(voices)} voices!")
    print("\n   First 5 voices:")
    for voice in voices[:5]:
        print(f"      • {voice['name']}: {voice['description']}")
    
    # Step 4: Estimate duration
    test_text = "This is a test of the ElevenLabs voice generator. If you can hear this, it's working perfectly!"
    print(f"\n4️⃣ Estimating audio duration...")
    duration = tts.estimate_duration(test_text)
    print(f"   ✅ Estimated duration: {duration:.1f} seconds")
    
    # Step 5: Generate test audio
    print(f"\n5️⃣ Generating test audio...")
    print(f"   Text: \"{test_text}\"")
    
    output_path = "test_audio.mp3"
    
    try:
        result_path = tts.generate_audio(
            text=test_text,
            voice_id=voices[0]['id'],  # Use the first available voice
            output_path=output_path
        )
        
        print(f"\n   ✅ SUCCESS! Audio file created!")
        print(f"   📁 Location: {result_path}")
        print(f"\n   🎧 Go listen to {output_path} to hear your AI voice!")
        
    except Exception as e:
        print(f"\n   ❌ ERROR: {str(e)}")
        return
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    # Check if API key was set
    if API_KEY == "sk_your_api_key_here":
        print("❌ ERROR: You need to put your real API key in this file!")
        print("   Open test_elevenlabs.py and replace 'sk_your_api_key_here' with your actual key")
    else:
        test_elevenlabs()