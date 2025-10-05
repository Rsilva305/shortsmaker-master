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
    
    CRITICAL FIX: Removes audio from looped video to prevent conflicts!
    
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
        
        # Create the concat list file
        concat_list = os.path.join(os.path.dirname(output_file), 'concat_list.txt')
        with open(concat_list, 'w') as f:
            for i in range(times_to_loop):
                abs_video_path = os.path.abspath(video_file).replace('\\', '/')
                f.write(f"file '{abs_video_path}'\n")
        
        # CRITICAL FIX: Use -an to remove audio from the looped video!
        # This prevents audio conflicts when we add our own audio later
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-t', str(target_duration),
            '-an',  # ← THIS IS THE FIX! Remove audio from video
            '-c:v', 'copy',  # Copy video without re-encoding (fast)
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up the concat list file
        if os.path.exists(concat_list):
            os.remove(concat_list)
        
        print(f"   ✅ Looped video saved (audio removed for clean mixing)")
        return output_file
        
    except Exception as e:
        print(f"❌ Error looping video: {str(e)}")
        raise


def mix_voice_and_music(voice_audio: str, background_music: str, output_file: str,
                        video_duration: float, voice_delay: float = 1.0,
                        voice_volume: float = 1.0, music_volume: float = 0.15) -> str:
    """
    Mix AI voice with background music - PROPERLY!
    
    Music starts immediately, voice starts after delay, music fades at end.
    
    Args:
        voice_audio: Path to the AI voice audio
        background_music: Path to the background music
        output_file: Where to save the mixed audio
        video_duration: Total duration of the video
        voice_delay: Seconds to delay the voice (default: 1.0)
        voice_volume: Volume of the voice (0.0 to 1.0, default: 1.0)
        music_volume: Volume of the music (0.0 to 1.0, default: 0.15)
        
    Returns:
        Path to the mixed audio file
    """
    try:
        print(f"🎵 Mixing voice and background music (smart sync)...")
        print(f"   Voice starts at: {voice_delay}s (synced with text)")
        print(f"   Music starts at: 0s (immediate)")
        print(f"   Total duration: {video_duration:.1f}s")
        
        # Get voice duration
        voice_duration = get_audio_duration(voice_audio)
        music_duration = get_audio_duration(background_music)
        
        # Step 1: PAD the voice audio to match video duration
        # This creates: [silence] + [voice] + [silence] = full video length
        padded_voice = os.path.join(os.path.dirname(output_file) or '.', 'voice_padded.mp3')
        
        # Calculate how much silence we need after the voice
        silence_after = video_duration - voice_delay - voice_duration
        
        print(f"   🔇 Padding audio: {voice_delay}s silence before, total {video_duration:.1f}s")
        
        # Create padded voice using adelay (adds silence before) and apad (adds silence after)
        pad_command = [
            'ffmpeg',
            '-i', voice_audio,
            '-af', f'adelay={int(voice_delay * 1000)}|{int(voice_delay * 1000)},apad=whole_dur={video_duration}',
            '-y',
            padded_voice
        ]
        
        subprocess.check_call(pad_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"   ✅ Padded audio created ({video_duration:.1f}s total)")
        
        # Step 2: LOOP and PREPARE the background music to match video duration
        if music_duration < video_duration:
            loops_needed = int(video_duration / music_duration) + 1
            
            music_concat = os.path.join(os.path.dirname(output_file) or '.', 'music_concat.txt')
            with open(music_concat, 'w') as f:
                for i in range(loops_needed):
                    abs_music_path = os.path.abspath(background_music).replace('\\', '/')
                    f.write(f"file '{abs_music_path}'\n")
            
            looped_music = os.path.join(os.path.dirname(output_file) or '.', 'music_looped.mp3')
            subprocess.check_call([
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', music_concat,
                '-t', str(video_duration), '-c', 'copy', '-y', looped_music
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            background_music = looped_music
            if os.path.exists(music_concat):
                os.remove(music_concat)
        
        # Step 3: Calculate fade duration (last 1.5 seconds)
        fade_start = video_duration - 1.5
        
        # Step 4: MIX the two EQUAL-LENGTH audio streams
        # Both are now exactly video_duration seconds long!
        ffmpeg_command = [
            'ffmpeg',
            '-i', background_music,  # Music (full length)
            '-i', padded_voice,      # Voice (full length, padded)
            '-filter_complex',
            # Add fade to music at end, adjust volumes, then mix
            f'[0:a]volume={music_volume},afade=t=out:st={fade_start}:d=1.5[music];'
            f'[1:a]volume={voice_volume}[voice];'
            f'[music][voice]amix=inputs=2:duration=first:dropout_transition=0',
            '-t', str(video_duration),
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temporary files
        if os.path.exists(padded_voice):
            os.remove(padded_voice)
        if 'music_looped.mp3' in background_music and os.path.exists(background_music):
            os.remove(background_music)
        
        print(f"   ✅ Perfect mix! Music plays throughout, voice starts at {voice_delay}s")
        return output_file
        
    except Exception as e:
        print(f"❌ Error mixing audio: {str(e)}")
        raise


def prepare_background_music(music_file: str, output_file: str, target_duration: float) -> str:
    """
    Prepare background music for the full video duration with fade at end
    
    Args:
        music_file: Original music file
        output_file: Where to save processed music
        target_duration: How long the video will be
        
    Returns:
        Path to the processed music
    """
    try:
        music_duration = get_audio_duration(music_file)
        
        # Loop if needed
        if music_duration < target_duration:
            loops_needed = int(target_duration / music_duration) + 1
            
            music_concat = os.path.join(os.path.dirname(output_file) or '.', 'music_concat.txt')
            with open(music_concat, 'w') as f:
                for i in range(loops_needed):
                    abs_music_path = os.path.abspath(music_file).replace('\\', '/')
                    f.write(f"file '{abs_music_path}'\n")
            
            looped_music = os.path.join(os.path.dirname(output_file) or '.', 'music_temp.mp3')
            subprocess.check_call([
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', music_concat,
                '-t', str(target_duration), '-c', 'copy', '-y', looped_music
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            music_file = looped_music
            if os.path.exists(music_concat):
                os.remove(music_concat)
        
        # Add fade at end
        fade_start = target_duration - 1.5
        
        ffmpeg_command = [
            'ffmpeg',
            '-i', music_file,
            '-af', f'afade=t=out:st={fade_start}:d=1.5',
            '-t', str(target_duration),
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temp file
        if 'music_temp.mp3' in music_file and os.path.exists(music_file):
            os.remove(music_file)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error preparing background music: {str(e)}")
        raise


def prepare_video_for_audio(video_file: str, audio_duration: float, output_file: str) -> str:
    """
    Prepare a video to match audio length
    
    This is the SMART function that decides what to do:
    - If video is shorter: Loop it
    - If video is longer: Trim it
    - If they're close: Use as-is
    
    CRITICAL FIX: Always removes audio from adjusted videos!
    
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
        print(f"   📹 Video ({video_duration:.1f}s) is shorter than target ({audio_duration:.1f}s)")
        return loop_video_to_duration(video_file, audio_duration, output_file)
    
    # If video is longer, trim it
    else:
        print(f"   ✂️ Video ({video_duration:.1f}s) is longer than target ({audio_duration:.1f}s)")
        print(f"   Trimming video to {audio_duration:.1f} seconds...")
        
        # CRITICAL FIX: Use -an to remove audio when trimming!
        # This prevents audio conflicts when we add our own audio later
        ffmpeg_command = [
            'ffmpeg',
            '-i', video_file,
            '-t', str(audio_duration),
            '-an',  # ← THIS IS THE FIX! Remove audio from trimmed video
            '-c:v', 'copy',  # Copy video without re-encoding (fast)
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"   ✅ Trimmed video saved (audio removed for clean mixing)")
        return output_file