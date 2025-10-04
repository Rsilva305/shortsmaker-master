import os
import pickle
import random
import subprocess
import re
import sys
import time
import json_handler
import verse_handler
import Fonts
import cv2


def create_dirs(output_folder, customer_name, posts=True):
    """Create necessary output directories"""
    output_path = f"{output_folder}/{customer_name}"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    if not os.path.exists(f"{output_path}/verse_images"):
        os.makedirs(f"{output_path}/verse_images")
    
    if posts and not os.path.exists(f"{output_path}/post_images"):
        os.makedirs(f"{output_path}/post_images")
    
    return output_path


def create_videos(video_folder, audio_folder, json_file, fonts_dir, output_folder, 
                  text_source_font, image_file: str, customer_name, number_of_videos, 
                  fonts: Fonts, posts=False, progress_callback=None, use_logo=True):
    """
    Create multiple videos with progress tracking
    
    Args:
        progress_callback: Optional function(current, total) to report progress
        use_logo: Boolean to enable/disable logo overlay (default: True)
    """
    # Load content data
    json_data = json_handler.get_data(json_file)
    verses: str = json_data[0]
    refs: str = json_data[1]

    # Validate number of videos
    if number_of_videos == -1:
        number_of_videos = len(verses) - 1
    
    if number_of_videos > len(verses):
        print(f"⚠️ Warning: Requested {number_of_videos} videos but only {len(verses)} quotes available.")
        print(f"Creating {len(verses)} videos instead.")
        number_of_videos = len(verses)
    
    # Initialize timing
    run_time_average = 0
    if number_of_videos > 1:
        start_time_total = time.time()

    # Prepare random selections
    videos_num = list()
    audios_num = list()
    fonts_num = list()

    # Get lists of files
    video_files = [f"{video_folder}/{file}" for file in os.listdir(video_folder) if file.endswith(".mp4")]
    audio_files = [f"{audio_folder}/{file}" for file in os.listdir(audio_folder) if file.endswith(".mp3")]
    
    if not video_files:
        raise Exception(f"No MP4 video files found in {video_folder}")
    if not audio_files:
        raise Exception(f"No MP3 audio files found in {audio_folder}")
    
    # Create random but distributed selections
    random_for_video = random.randint(0, len(video_files) - 1)
    random_for_audio = random.randint(0, len(audio_files) - 1)
    random_for_font = random.randint(0, len(fonts.fonts_path) - 1)
    
    for i in range(number_of_videos):
        videos_num.append((random_for_video + i) % len(video_files))
        audios_num.append((random_for_audio + i) % len(audio_files))
        fonts_num.append((random_for_font + i) % len(fonts.fonts_path))
    
    random.shuffle(videos_num)
    random.shuffle(audios_num)
    random.shuffle(fonts_num)

    # Create output directory
    output_path = create_dirs(output_folder, customer_name, posts)

    # Data for spreadsheet
    spreadsheet_col1 = list()
    spreadsheet_col2 = list()
    spreadsheet_col3 = list()

    # Estimate runtime
    avg_runtime = get_avg_runtime('runtime.pk')
    if avg_runtime != -1:
        estimated_runtime = round(avg_runtime * number_of_videos, 2)
        print(f"\033[0;32m⏱️ Estimated run time: {round(estimated_runtime, 2)} seconds\033[0m")
        if round(estimated_runtime, 2) > 60:
            print(f"\033[0;32m   = {round(estimated_runtime / 60, 2)} minutes\033[0m")
        if round(estimated_runtime / 60, 2) > 60:
            print(f"\033[0;32m   = {round((estimated_runtime / 60) / 60, 2)} hours\033[0m")
        print(f"\033[0;32m   for {number_of_videos} videos!\033[0m")

    # Create each video
    for i in range(number_of_videos):
        start_time = time.time()
        
        # Report progress
        if progress_callback:
            progress_callback(i + 1, number_of_videos)
        
        print(f"\n{'='*50}")
        print(f"🎬 Creating Video #{i+1}/{number_of_videos}")
        print(f"{'='*50}")

        text_verse = verses[i]
        text_source = refs[i]

        # Select resources
        random_video_num = videos_num[0]
        del videos_num[0]
        video_file = video_files[random_video_num]

        random_font_num = fonts_num[0]
        del fonts_num[0]
        font_file = fonts.fonts_path[random_font_num]
        font_size = fonts.fonts_size[random_font_num]
        font_chars = fonts.fonts_chars_limit[random_font_num]

        random_audio_num = audios_num[0]
        del audios_num[0]
        audio_file = audio_files[random_audio_num]

        # Create filename
        text_source_for_image = text_source.replace(":", "").rstrip('\n')
        text_source_for_name = text_source_for_image.replace(' ', '')
        file_name = f"/{i}-{text_source_for_name}_{random_video_num}_{random_audio_num}_{random_font_num}.mp4"

        # Create the video
        print(f"📝 Quote: {text_source}")
        print(f"🎥 Video: {os.path.basename(video_file)}")
        print(f"🎵 Audio: {os.path.basename(audio_file)}")
        print(f"✍️ Font: {os.path.basename(font_file)}")
        if use_logo:
            print(f"🖼️ Logo: {os.path.basename(image_file)}")
        else:
            print(f"🖼️ Logo: Disabled")
        
        create_video(
            text_verse=text_verse, 
            text_source=text_source, 
            text_source_font=text_source_font,
            text_source_for_image=text_source_for_image,
            video_file=video_file, 
            audio_file=audio_file, 
            image_file=image_file,
            font_file=font_file, 
            font_size=font_size, 
            font_chars=font_chars,
            posts=posts,
            output_path=output_path, 
            file_name=file_name,
            use_logo=use_logo
        )

        # Record for spreadsheet
        spreadsheet_col1.append(file_name.strip("/"))
        spreadsheet_col2.append(text_source)
        spreadsheet_col3.append(text_verse)

        # Calculate timing
        end_time = time.time()
        run_time = end_time - start_time
        run_time_average += run_time
        
        print(f"\033[0;32m✅ DONE #{i+1}, Run time: {round(run_time, 2)} seconds!\033[0m")
        print(f"📁 Output: {output_path}")

    # Create spreadsheet
    verse_handler.add_sheets(
        video_names=spreadsheet_col1, 
        customer_name=customer_name, 
        output_path=output_path,
        refs=spreadsheet_col2, 
        verses=spreadsheet_col3
    )

    # Final statistics
    if number_of_videos > 1:
        run_time_average /= number_of_videos
        update_avg_runtime(filename='runtime.pk', curr_runtime=run_time_average)
        end_time_total = time.time()
        run_time_total = end_time_total - start_time_total
        
        print(f"\n{'='*60}")
        print(f"\033[0;32m🎉 SUCCESS! Created {number_of_videos} videos for {customer_name}!")
        print(f"⏱️ Total run time: {round(run_time_total, 2)} seconds = {round(run_time_total / 60, 2)} minutes")
        print(f"📊 Average per video: {round(run_time_average, 2)} seconds")
        print(f"📁 Output folder: {output_path}")
        print(f"📋 Spreadsheet: {output_path}/{customer_name}.csv")
        print(f"{'='*60}\033[0m\n")


def create_video(text_verse, text_source, text_source_font, text_source_for_image, 
                 video_file: str, audio_file, image_file, font_file, font_size, 
                 font_chars, output_path, file_name, posts=True, use_logo=True):
    """Create a single video with all overlays
    
    Args:
        use_logo: Boolean to enable/disable logo overlay (default: True)
    """
    
    # Layout coordinates
    image_y = 0
    image_text_source_y = 800

    # Get video dimensions
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', video_file],
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
    )
    video_size = re.findall('\d+', result.stdout.decode())[0:2]
    video_width, video_height = map(int, video_size)

    # Get video duration
    ffprobe_command = f'ffprobe -i "{video_file}" -show_entries format=duration -v quiet -of csv="p=0"'
    video_duration = subprocess.check_output(ffprobe_command, shell=True)
    video_duration = float(video_duration.decode('utf-8').strip())

    # Timing
    text_start_time = 1
    text_color = (255, 255, 255, 255)
    font_color = "white"

    # Create quote image
    created_verse_image_data = verse_handler.create_image(
        text_verse, 
        font_file, 
        font_size, 
        font_chars,
        (int(video_width), int(video_height / 2)), 
        output_path,
        text_source_for_image, 
        text_color=text_color
    )
    created_verse_image = created_verse_image_data[0]
    verse_height = created_verse_image_data[1]

    # Calculate text position
    text2_y: int = image_text_source_y + verse_height + 75

    # Adjust if text overlaps logo (only if logo is used)
    if use_logo and text2_y > 1200:
        diff = text2_y - 1200
        text2_y = 1200
        image_text_source_y -= diff

    # Escape special characters for ffmpeg
    text_source = text_source.replace(':', '\\:')
    output_folder = output_path
    output_path += f"/{file_name}"
    
    # Build ffmpeg command - WITH or WITHOUT logo
    if use_logo:
        # Original command with logo overlay
        ffmpeg_command = (
            f'ffmpeg -loglevel error -stats -y '
            f'-loop 1 -i "{image_file}" '
            f'-i "{audio_file}" '
            f'-i "{video_file}" '
            f'-i "{created_verse_image}" '
            f'-r 24 -filter_complex '
            f'"[2:v][0:v]overlay=(W-w)/2:{image_y}[v1]; '
            f'[v1]drawtext=fontfile=\'{text_source_font}\':'
            f'text=\'{text_source}\':'
            f'x=(w-text_w)/2:y={text2_y}:'
            f'fontsize=42:fontcolor={font_color}:'
            f'enable=\'between(t,{text_start_time},{video_duration})\'[v2]; '
            f'[v2][3:v]overlay=(W-w)/2:{image_text_source_y}:'
            f'enable=\'between(t,{text_start_time},{video_duration})\'[v3]" '
            f'-t {video_duration} -map "[v3]" -map 1 '
            f'-c:v libx264 -preset veryfast -crf 18 "{output_path}"'
        )
    else:
        # Simplified command WITHOUT logo overlay
        ffmpeg_command = (
            f'ffmpeg -loglevel error -stats -y '
            f'-i "{audio_file}" '
            f'-i "{video_file}" '
            f'-i "{created_verse_image}" '
            f'-r 24 -filter_complex '
            f'"[1:v]drawtext=fontfile=\'{text_source_font}\':'
            f'text=\'{text_source}\':'
            f'x=(w-text_w)/2:y={text2_y}:'
            f'fontsize=42:fontcolor={font_color}:'
            f'enable=\'between(t,{text_start_time},{video_duration})\'[v1]; '
            f'[v1][2:v]overlay=(W-w)/2:{image_text_source_y}:'
            f'enable=\'between(t,{text_start_time},{video_duration})\'[v2]" '
            f'-t {video_duration} -map "[v2]" -map 0 '
            f'-c:v libx264 -preset veryfast -crf 18 "{output_path}"'
        )

    # Execute ffmpeg
    try:
        subprocess.check_call(ffmpeg_command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating video: {e}")
        raise

    # Create post images if requested
    if posts:
        verse_handler.create_post_images(
            video_path=output_path, 
            output_folder=f"{output_folder}/post_images"
        )


def get_avg_runtime(filename: str):
    """Load average runtime from pickle file"""
    try:
        with open(filename, 'rb') as fi:
            return pickle.load(fi)
    except (EOFError, FileNotFoundError):
        return -1


def update_avg_runtime(curr_runtime: float, filename: str):
    """Update average runtime in pickle file"""
    old_runtime = get_avg_runtime(filename)
    
    if old_runtime == -1:
        new_runtime = curr_runtime
    else:
        new_runtime = (old_runtime + curr_runtime) / 2

    with open(filename, 'wb') as fi:
        pickle.dump(new_runtime, fi)