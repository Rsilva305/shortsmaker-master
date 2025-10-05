"""
Audio Utilities - Helper functions for handling audio and video sync
This solves the "audio longer than video" problem!
"""

import subprocess
import os
from typing import Tuple, List


def get_audio_duration(audio_file: str) -> float:
    """
    Get the length of an audio file in seconds
    
    Args:
        audio_file: Path to the audio file (MP3, WAV, etc.)
        
    Returns:
        Duration in seconds (like 12.5 seconds)
        
    Example:
        get_audio_duration("audio/verse1.mp3") → 15.3
    """
    try:
        # Use ffprobe to get the duration
        ffprobe_command = [
            'ffprobe', 
            '-i', audio_file,
            '-show_entries', 'format=duration',
            '-v', 'quiet',
            '-of', 'csv=p=0'
        ]
        
        result = subprocess.check_output(ffprobe_command)
        duration = float(result.decode('utf-8').strip())
        
        return duration
        
    except Exception as e:
        print(f"❌ Error getting audio duration: {str(e)}")
        return 0.0


def get_video_duration(video_file: str) -> float:
    """
    Get the length of a video file in seconds
    
    Args:
        video_file: Path to the video file (MP4, etc.)
        
    Returns:
        Duration in seconds
        
    Example:
        get_video_duration("videos/nature1.mp4") → 30.0
    """
    try:
        # Use ffprobe to get the duration
        ffprobe_command = [
            'ffprobe',
            '-i', video_file,
            '-show_entries', 'format=duration',
            '-v', 'quiet',
            '-of', 'csv=p=0'
        ]
        
        result = subprocess.check_output(ffprobe_command)
        duration = float(result.decode('utf-8').strip())
        
        return duration
        
    except Exception as e:
        print(f"❌ Error getting video duration: {str(e)}")
        return 0.0


def loop_video_to_duration(video_file: str, target_duration: float, output_file: str) -> str:
    """
    Loop a video to match a target duration
    
    This solves: "Audio is 45 seconds, but video is only 30 seconds"
    Solution: Loop the video to make it 45+ seconds
    
    Args:
        video_file: Original video file
        target_duration: How long you need it to be (in seconds)
        output_file: Where to save the looped video
        
    Returns:
        Path to the looped video
        
    Example:
        loop_video_to_duration("nature.mp4", 45.0, "nature_looped.mp4")
        → Creates a 45-second video by looping nature.mp4
    """
    try:
        # Get how long the original video is
        original_duration = get_video_duration(video_file)
        
        if original_duration == 0:
            raise Exception("Could not get video duration")
        
        # Calculate how many times we need to loop
        times_to_loop = int(target_duration / original_duration) + 1
        
        print(f"🔄 Looping video {times_to_loop} times to reach {target_duration:.1f} seconds...")
        
        # Create the ffmpeg command to loop the video
        # This creates a list like: "file 'video.mp4'\nfile 'video.mp4'\nfile 'video.mp4'"
        concat_list = os.path.join(os.path.dirname(output_file), 'concat_list.txt')
        with open(concat_list, 'w') as f:
            for i in range(times_to_loop):
                # Use absolute path to avoid issues
                abs_video_path = os.path.abspath(video_file).replace('\\', '/')
                f.write(f"file '{abs_video_path}'\n")
        
        # Use ffmpeg to concatenate the video with itself
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-t', str(target_duration),  # Trim to exact duration
            '-c', 'copy',  # Copy without re-encoding (fast!)
            '-y',  # Overwrite if exists
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up the temporary file
        if os.path.exists(concat_list):
            os.remove(concat_list)
        
        print(f"   ✅ Looped video saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error looping video: {str(e)}")
        raise


def mix_audio_files(voice_audio: str, background_music: str, output_file: str, 
                    voice_volume: float = 1.0, music_volume: float = 0.3) -> str:
    """
    Mix AI voice with background music
    
    This creates a nice blend where you can hear the voice clearly,
    with music playing softly in the background.
    
    Args:
        voice_audio: Path to the AI voice audio
        background_music: Path to the background music
        output_file: Where to save the mixed audio
        voice_volume: Volume of the voice (0.0 to 1.0, default: 1.0 = full volume)
        music_volume: Volume of the music (0.0 to 1.0, default: 0.3 = 30% volume)
        
    Returns:
        Path to the mixed audio file
        
    Example:
        mix_audio_files(
            "voice.mp3",        # AI voice
            "background.mp3",    # Music
            "final.mp3",         # Output
            voice_volume=1.0,    # Voice at full volume
            music_volume=0.2     # Music at 20% (quiet background)
        )
    """
    try:
        print(f"🎵 Mixing voice and background music...")
        print(f"   Voice volume: {voice_volume * 100:.0f}%")
        print(f"   Music volume: {music_volume * 100:.0f}%")
        
        # Get durations
        voice_duration = get_audio_duration(voice_audio)
        music_duration = get_audio_duration(background_music)
        
        # If music is shorter than voice, we'll loop it
        looped_music = None
        if music_duration < voice_duration:
            print(f"   🔄 Looping background music to match voice length...")
            # Calculate how many loops we need
            loops = int(voice_duration / music_duration) + 1
            
            # Create concat file for music
            music_concat = os.path.join(os.path.dirname(output_file) or '.', 'music_concat.txt')
            with open(music_concat, 'w') as f:
                for i in range(loops):
                    abs_music_path = os.path.abspath(background_music).replace('\\', '/')
                    f.write(f"file '{abs_music_path}'\n")
            
            # Create looped music
            looped_music = os.path.join(os.path.dirname(output_file) or '.', 'music_looped.mp3')
            subprocess.check_call([
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', music_concat,
                '-t', str(voice_duration), '-c', 'copy', '-y', looped_music
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            background_music = looped_music
            if os.path.exists(music_concat):
                os.remove(music_concat)
        
        # Mix the audio files
        # This uses ffmpeg's filter_complex to blend the audio
        ffmpeg_command = [
            'ffmpeg',
            '-i', voice_audio,        # Input 1: Voice
            '-i', background_music,   # Input 2: Music
            '-filter_complex',
            f'[0:a]volume={voice_volume}[a1];'     # Set voice volume
            f'[1:a]volume={music_volume}[a2];'     # Set music volume
            f'[a1][a2]amix=inputs=2:duration=first:dropout_transition=2',  # Mix them
            '-ac', '2',  # Stereo output
            '-y',        # Overwrite if exists
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up looped music if we created it
        if looped_music and os.path.exists(looped_music):
            os.remove(looped_music)
        
        print(f"   ✅ Mixed audio saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error mixing audio: {str(e)}")
        raise


def prepare_video_for_audio(video_file: str, audio_duration: float, output_file: str) -> str:
    """
    Prepare a video to match audio length
    
    This is the SMART function that decides what to do:
    - If video is shorter: Loop it
    - If video is longer: Trim it
    - If they're close: Use as-is
    
    Args:
        video_file: Original video
        audio_duration: How long the audio is
        output_file: Where to save the adjusted video
        
    Returns:
        Path to the adjusted video
    """
    video_duration = get_video_duration(video_file)
    
    # If they're within 1 second, don't bother adjusting
    if abs(video_duration - audio_duration) < 1.0:
        print("   ✅ Video and audio lengths are close enough!")
        return video_file
    
    # If video is shorter, loop it
    if video_duration < audio_duration:
        print(f"   📹 Video ({video_duration:.1f}s) is shorter than audio ({audio_duration:.1f}s)")
        return loop_video_to_duration(video_file, audio_duration, output_file)
    
    # If video is longer, trim it
    else:
        print(f"   ✂️ Video ({video_duration:.1f}s) is longer than audio ({audio_duration:.1f}s)")
        print(f"   Trimming video to {audio_duration:.1f} seconds...")
        
        ffmpeg_command = [
            'ffmpeg',
            '-i', video_file,
            '-t', str(audio_duration),
            '-c', 'copy',
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"   ✅ Trimmed video saved!")
        return output_file


def add_audio_delay(input_audio: str, output_audio: str, delay_seconds: float = 1.0) -> str:
    """
    Add silence at the beginning of audio to sync with text appearance
    NO fade-out - let the speaker finish naturally!
    
    Args:
        input_audio: Path to the original audio file
        output_audio: Path to save the processed audio
        delay_seconds: Seconds of silence to add at start (default: 1.0)
        
    Returns:
        Path to the processed audio file
        
    Example:
        add_audio_delay("voice.mp3", "voice_synced.mp3", delay_seconds=1.0)
        → Creates audio with 1 second silence at start
    """
    try:
        print(f"   ⏱️ Adding {delay_seconds}s delay to sync with text...")
        
        # Use ffmpeg to add delay
        # adelay adds silence at the beginning (in milliseconds)
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_audio,
            '-af', f'adelay={int(delay_seconds * 1000)}|{int(delay_seconds * 1000)}',
            '-y',
            output_audio
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"   ✅ Audio synced with {delay_seconds}s delay!")
        return output_audio
        
    except Exception as e:
        print(f"❌ Error adding delay to audio: {str(e)}")
        raise