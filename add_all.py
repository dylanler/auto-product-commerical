import os
from datetime import datetime
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class VideoAudioCombiner:
    def __init__(self, video_directory, audio_file):
        self.video_directory = video_directory
        self.audio_file = audio_file
        self.output_directory = "final_video"
        self.ending_video = "simplycodes_ending.mp4"
    
    def process(self):
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Get all video files and sort them
        video_files = self._get_sorted_video_files()
        
        # Load video clips and ensure consistent properties
        video_clips = []
        target_resolution = None
        target_fps = None

        for vf in video_files:
            clip = VideoFileClip(os.path.join(self.video_directory, vf))
            
            if target_resolution is None:
                target_resolution = clip.size
                target_fps = clip.fps
            
            # Resize and set fps if necessary
            if clip.size != target_resolution or clip.fps != target_fps:
                clip = clip.resize(target_resolution)
                clip = clip.set_fps(target_fps)
            
            video_clips.append(clip)

        # Add the ending video
        ending_clip = VideoFileClip(os.path.join(self.video_directory, self.ending_video))
        if ending_clip.size != target_resolution or ending_clip.fps != target_fps:
            ending_clip = ending_clip.resize(target_resolution)
            ending_clip = ending_clip.set_fps(target_fps)
        video_clips.append(ending_clip)

        final_video = concatenate_videoclips(video_clips)
        
        # Calculate total video duration
        total_duration = sum(clip.duration for clip in video_clips)
        
        # Load and cut audio
        audio = AudioFileClip(self.audio_file).subclip(0, total_duration)
        
        # Set audio to final video
        final_video = final_video.set_audio(audio)
        
        # Generate output filename
        output_filename = f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(self.output_directory, output_filename)
        
        # Write final video
        final_video.write_videofile(output_path)
        
        # Close clips
        final_video.close()
        for clip in video_clips:
            clip.close()
        audio.close()
        
        print(f"Final video saved to: {output_path}")
    
    def _get_sorted_video_files(self):
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
        video_files = [f for f in os.listdir(self.video_directory) if f.lower().endswith(video_extensions) and f != self.ending_video]
        return sorted(video_files)

# Usage example:
# combiner = VideoAudioCombiner("/path/to/video/directory", "/path/to/audio/file.mp3")
# combiner.process()
