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
        concat_list = os.path.join(os.path.dirname(output_file), 'concat_list.txt')
        with open(concat_list, 'w') as f:
            for i in range(times_to_loop):
                abs_video_path = os.path.abspath(video_file).replace('\\', '/')
                f.write(f"file '{abs_video_path}'\n")
        
        # Use ffmpeg to concatenate the video with itself
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-t', str(target_duration),
            '-c', 'copy',
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(concat_list):
            os.remove(concat_list)
        
        print(f"   ✅ Looped video saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error looping video: {str(e)}")
        raise


def pad_audio_with_silence(input_audio: str, output_audio: str, 
                           start_delay: float, total_duration: float) -> str:
    """
    Pad audio with silence before and after to match target duration
    
    This ensures the voice audio is the same length as the video/music
    
    Args:
        input_audio: Original audio file
        output_audio: Where to save padded audio
        start_delay: Seconds of silence at the beginning
        total_duration: Total duration of output
        
    Returns:
        Path to the padded audio
        
    Example:
        Voice is 5 seconds, we want it to start at 1s in a 10s video:
        pad_audio_with_silence("voice.mp3", "padded.mp3", start_delay=1.0, total_duration=10.0)
        Result: 1s silence + 5s voice + 4s silence = 10s total
    """
    try:
        voice_duration = get_audio_duration(input_audio)
        
        # Calculate padding needed
        # total = start_delay + voice_duration + end_padding
        # So: end_padding = total - start_delay - voice_duration
        
        print(f"   🔇 Padding audio: {start_delay}s silence before, total {total_duration}s")
        
        # Use ffmpeg to add silence padding
        # adelay adds silence at start
        # then we pad the end to reach total duration
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_audio,
            '-af', f'adelay={int(start_delay * 1000)}|{int(start_delay * 1000)},apad=whole_dur={int(total_duration * 1000)}ms',
            '-y',
            output_audio
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"   ✅ Padded audio created ({total_duration}s total)")
        return output_audio
        
    except Exception as e:
        print(f"❌ Error padding audio: {str(e)}")
        raise


def mix_voice_and_music(voice_audio: str, background_music: str, output_file: str,
                        video_duration: float, voice_delay: float = 1.0,
                        voice_volume: float = 1.0, music_volume: float = 0.15) -> str:
    """
    Mix AI voice with background music - PROPERLY!
    
    Music starts immediately, voice starts after delay, music fades at end.
    Both streams are same length for reliable mixing!
    
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
        
        voice_duration = get_audio_duration(voice_audio)
        music_duration = get_audio_duration(background_music)
        
        # Step 1: Pad voice to match video duration (with delay at start)
        padded_voice = os.path.join(os.path.dirname(output_file) or '.', 'voice_padded.mp3')
        pad_audio_with_silence(
            input_audio=voice_audio,
            output_audio=padded_voice,
            start_delay=voice_delay,
            total_duration=video_duration
        )
        
        # Step 2: Prepare music (loop if needed, trim to video duration, add fade)
        prepared_music = os.path.join(os.path.dirname(output_file) or '.', 'music_prepared.mp3')
        
        # Loop music if needed
        if music_duration < video_duration:
            loops_needed = int(video_duration / music_duration) + 1
            print(f"   🔄 Looping background music {loops_needed} times...")
            
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
        
        # Add fade to music at end
        fade_start = video_duration - 1.5
        
        subprocess.check_call([
            'ffmpeg',
            '-i', background_music,
            '-af', f'volume={music_volume},afade=t=out:st={fade_start}:d=1.5',
            '-t', str(video_duration),
            '-y',
            prepared_music
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Step 3: Mix the two streams (both are now same length!)
        ffmpeg_command = [
            'ffmpeg',
            '-i', prepared_music,      # Music (full video duration with fade)
            '-i', padded_voice,         # Voice (full video duration with delay built-in)
            '-filter_complex',
            f'[0:a]volume=1.0[music];'  # Music already has volume applied
            f'[1:a]volume={voice_volume}[voice];'
            f'[music][voice]amix=inputs=2:duration=first',  # Both same length, so this is safe
            '-t', str(video_duration),
            '-y',
            output_file
        ]
        
        subprocess.check_call(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up temp files
        for temp_file in [padded_voice, prepared_music]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
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