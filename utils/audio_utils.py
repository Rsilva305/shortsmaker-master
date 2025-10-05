"""
Audio & Video Utilities — robust, Windows-safe helpers
Fixes the MP4 concat/copy failures by re-encoding when looping or trimming.
"""

import subprocess
import os
import math
from typing import Tuple


def _run(cmd: list) -> None:
    """
    Run a subprocess command, raising on failure.
    Suppresses ffmpeg stdout/stderr noise but keeps clear exceptions.
    """
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_audio_duration(audio_file: str) -> float:
    """Return audio duration in seconds (float)."""
    try:
        result = subprocess.check_output(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                "-i", audio_file,
            ]
        )
        return float(result.decode("utf-8").strip())
    except Exception as e:
        print(f"❌ Error getting audio duration: {e}")
        return 0.0


def get_video_duration(video_file: str) -> float:
    """Return video duration in seconds (float)."""
    try:
        result = subprocess.check_output(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                "-i", video_file,
            ]
        )
        return float(result.decode("utf-8").strip())
    except Exception as e:
        print(f"❌ Error getting video duration: {e}")
        return 0.0


def _loop_video_stream_loop(video_file: str, target_duration: float, output_file: str) -> None:
    """
    Loop a video using -stream_loop (re-encode). Works reliably with MP4.
    - Removes source audio (-an) so we can add our own later.
    - Re-encodes with H.264/yuv420p for maximum compatibility.
    """
    original = max(get_video_duration(video_file), 0.0001)
    # stream_loop counts *extra* plays; compute exact number of extras needed
    extras = max(math.ceil(target_duration / original) - 1, 0)

    # If extras is large, we can still set -t to cap precisely at target_duration
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", str(extras),
        "-i", video_file,
        "-t", f"{target_duration:.3f}",
        "-an",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-movflags", "+faststart",
        output_file,
    ]
    _run(cmd)


def _concat_filter_fallback(video_file: str, target_duration: float, output_file: str) -> None:
    """
    Fallback: duplicate the same input twice via filtergraph concat (re-encode),
    then trim to exact target. This avoids demuxer + copy pitfalls.
    """
    # We build: [0:v]split=2[v0][v1]; [v0][v1]concat=n=2:v=1:a=0[cat]
    filtergraph = (
        "[0:v]split=2[v0][v1];"
        "[v0][v1]concat=n=2:v=1:a=0[cat]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_file,
        "-filter_complex", filtergraph,
        "-map", "[cat]",
        "-t", f"{target_duration:.3f}",
        "-an",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-movflags", "+faststart",
        output_file,
    ]
    _run(cmd)


def loop_video_to_duration(video_file: str, target_duration: float, output_file: str) -> str:
    """
    Loop video to at least target_duration seconds, then cap to target.
    Robust on Windows/MP4. Always strips source audio (-an).
    """
    try:
        print(f"🔄 Looping video to reach {target_duration:.1f} seconds...")
        try:
            _loop_video_stream_loop(video_file, target_duration, output_file)
        except Exception:
            # If -stream_loop is not available or fails, use filter fallback
            _concat_filter_fallback(video_file, target_duration, output_file)

        print("   ✅ Looped video saved (audio removed for clean mixing)")
        return output_file

    except Exception as e:
        print(f"❌ Error looping video: {e}")
        raise


def mix_voice_and_music(
    voice_audio: str,
    background_music: str,
    output_file: str,
    video_duration: float,
    voice_delay: float = 1.0,
    voice_volume: float = 1.0,
    music_volume: float = 0.15,
) -> str:
    """
    Mix AI voice with background music:
      - Music starts immediately
      - Voice starts after voice_delay
      - Music fades out in the last 1.5 s
    Outputs exactly video_duration seconds.
    """
    try:
        print("🎵 Mixing voice and background music (smart sync)...")
        print(f"   Voice starts at: {voice_delay}s (synced with text)")
        print("   Music starts at: 0s (immediate)")
        print(f"   Total duration: {video_duration:.1f}s")

        # 1) Pad the voice to full length: [silence_before] + voice + [silence_after] = video_duration
        padded_voice = os.path.join(os.path.dirname(output_file) or ".", "voice_padded.mp3")

        pad_cmd = [
            "ffmpeg",
            "-y",
            "-i", voice_audio,
            "-af", f"adelay={int(voice_delay*1000)}|{int(voice_delay*1000)},apad=whole_dur={video_duration}",
            "-t", f"{video_duration:.3f}",
            padded_voice,
        ]
        _run(pad_cmd)
        print(f"   🔇 Padded audio created ({video_duration:.1f}s total)")

        # 2) Ensure background music covers full duration (loop by concat demuxer is fine for MP3)
        music_duration = get_audio_duration(background_music)
        music_full = background_music
        if music_duration < video_duration:
            loops = max(math.ceil(video_duration / max(music_duration, 0.0001)), 1)
            concat_list = os.path.join(os.path.dirname(output_file) or ".", "music_concat.txt")
            with open(concat_list, "w", encoding="utf-8") as f:
                abs_music = os.path.abspath(background_music).replace("\\", "/")
                for _ in range(loops):
                    f.write(f"file '{abs_music}'\n")

            music_full = os.path.join(os.path.dirname(output_file) or ".", "music_looped.mp3")
            _run([
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_list,
                "-t", f"{video_duration:.3f}",
                "-c", "copy",
                music_full
            ])
            if os.path.exists(concat_list):
                os.remove(concat_list)

        # 3) Fade music at end, mix with padded voice to exact duration
        fade_start = max(video_duration - 1.5, 0.0)
        cmd = [
            "ffmpeg",
            "-y",
            "-i", music_full,
            "-i", padded_voice,
            "-filter_complex",
            f"[0:a]volume={music_volume},afade=t=out:st={fade_start:.3f}:d=1.5[m];"
            f"[1:a]volume={voice_volume}[v];"
            f"[m][v]amix=inputs=2:duration=first:dropout_transition=0",
            "-t", f"{video_duration:.3f}",
            output_file,
        ]
        _run(cmd)

        # cleanup
        if os.path.exists(padded_voice):
            os.remove(padded_voice)
        if music_full.endswith("music_looped.mp3") and os.path.exists(music_full):
            os.remove(music_full)

        print(f"   ✅ Perfect mix! Music plays throughout, voice starts at {voice_delay}s")
        return output_file

    except Exception as e:
        print(f"❌ Error mixing audio: {e}")
        raise


def prepare_background_music(music_file: str, output_file: str, target_duration: float) -> str:
    """
    Make background music exactly target_duration with a 1.5 s fade out.
    """
    try:
        music_duration = get_audio_duration(music_file)
        music_full = music_file

        if music_duration < target_duration:
            loops = max(math.ceil(target_duration / max(music_duration, 0.0001)), 1)
            concat_list = os.path.join(os.path.dirname(output_file) or ".", "music_concat.txt")
            with open(concat_list, "w", encoding="utf-8") as f:
                abs_music = os.path.abspath(music_file).replace("\\", "/")
                for _ in range(loops):
                    f.write(f"file '{abs_music}'\n")

            music_full = os.path.join(os.path.dirname(output_file) or ".", "music_temp.mp3")
            _run([
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_list,
                "-t", f"{target_duration:.3f}",
                "-c", "copy",
                music_full
            ])
            if os.path.exists(concat_list):
                os.remove(concat_list)

        fade_start = max(target_duration - 1.5, 0.0)
        _run([
            "ffmpeg", "-y",
            "-i", music_full,
            "-af", f"afade=t=out:st={fade_start:.3f}:d=1.5",
            "-t", f"{target_duration:.3f}",
            output_file
        ])

        if music_full.endswith("music_temp.mp3") and os.path.exists(music_full):
            os.remove(music_full)

        return output_file

    except Exception as e:
        print(f"❌ Error preparing background music: {e}")
        raise


def prepare_video_for_audio(video_file: str, audio_duration: float, output_file: str) -> str:
    """
    Make video duration match audio_duration:
      - If shorter: loop (re-encode, -an)
      - If longer: trim (re-encode, -an)
      - If close (±1.0 s): leave as-is
    """
    video_duration = get_video_duration(video_file)

    if abs(video_duration - audio_duration) < 1.0:
        print("   ✅ Video and audio lengths are close enough!")
        return video_file

    if video_duration < audio_duration:
        print(f"   📹 Video ({video_duration:.1f}s) is shorter than target ({audio_duration:.1f}s)")
        return loop_video_to_duration(video_file, audio_duration, output_file)

    # Longer → trim (re-encode; still -an so we can add our mixed track later)
    print(f"   ✂️ Video ({video_duration:.1f}s) is longer than target ({audio_duration:.1f}s)")
    print(f"   Trimming video to {audio_duration:.1f} seconds...")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_file,
        "-t", f"{audio_duration:.3f}",
        "-an",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-movflags", "+faststart",
        output_file,
    ]
    _run(cmd)
    print("   ✅ Trimmed video saved (audio removed for clean mixing)")
    return output_file
