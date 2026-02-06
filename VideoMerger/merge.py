import os
import re
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips, CompositeAudioClip

# Configuration
VIDEO_DIR = "VideoMerger/videos"
AUDIO_DIR = "VideoMerger/audio"
OUTPUT_FILE = "VideoMerger/output_merged.mp4"

def get_sorted_files(directory, extensions):
    """
    Scans a directory for files with specific extensions.
    Sorts them based on the leading number in the filename (e.g., '1_clip.mp4').
    """
    files = []
    if not os.path.exists(directory):
        os.makedirs(directory)
        return []

    for f in os.listdir(directory):
        if f.lower().endswith(extensions):
            # Extract number prefix (supports "1_", "1.", "1 ", "1-")
            match = re.match(r"^(\d+)[\._\-\s]", f)
            if match:
                order = int(match.group(1))
                files.append((order, os.path.join(directory, f)))
            else:
                print(f"Warning: Skipping {f} (No numerical prefix like '1_' or '1.')")
    
    # Sort by number
    files.sort(key=lambda x: x[0])
    return [f[1] for f in files]

def main():
    print("--- VideoMerger Tool ---")

    # 1. Get Files
    video_files = get_sorted_files(VIDEO_DIR, ('.mp4', '.mov', '.avi', '.mkv'))
    audio_files = get_sorted_files(AUDIO_DIR, ('.mp3', '.wav', '.m4a', '.aac'))

    if not video_files:
        print(f"No valid video files found in {VIDEO_DIR}. Make sure they start with a number (e.g., '1_video.mp4').")
        return

    print(f"Videos found: {len(video_files)}")
    print(f"Audios found: {len(audio_files)}")

    try:
        # 2. Process Videos
        print("Loading video clips...")
        video_clips = [VideoFileClip(f) for f in video_files]
        final_video = concatenate_videoclips(video_clips)

        # 3. Process Audio (if any)
        final_audio = final_video.audio # Start with original video audio
        
        if audio_files:
            print("Loading and concatenating audio tracks...")
            audio_clips = [AudioFileClip(f) for f in audio_files]
            combined_external_audio = concatenate_audioclips(audio_clips)
            
            # Mix: Original Video Audio + External Audio
            # We composite them. If video has no audio, we just use external.
            if final_audio:
                final_audio = CompositeAudioClip([final_audio, combined_external_audio])
            else:
                final_audio = combined_external_audio
            
            # CRITICAL: Trim audio to match video duration
            final_audio = final_audio.with_duration(final_video.duration)

        # 4. Set final audio to video
        final_video.audio = final_audio

        # 5. Export
        print(f"Exporting to {OUTPUT_FILE}...")
        final_video.write_videofile(OUTPUT_FILE, codec="libx264", audio_codec="aac")
        
        print("\nDone! Merged video saved.")

    except Exception as e:
        print(f"Error processing keys: {e}")
    finally:
        # Cleanup clips to release resources
        if 'video_clips' in locals():
            for clip in video_clips: clip.close()
        if 'audio_clips' in locals():
            for clip in audio_clips: clip.close()

if __name__ == "__main__":
    main()
