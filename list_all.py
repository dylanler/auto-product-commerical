import os
from lumaai import LumaAI
from dotenv import load_dotenv

class LumaVideoGenerator:
    def __init__(self):
        load_dotenv()
        self.client = LumaAI(
            auth_token=os.environ.get("LUMA_API_TOKEN"),
        )

    def list_all_videos(self, limit=100, offset=0):
        print(f"Listing videos (limit: {limit}, offset: {offset})...")
        generations = self.client.generations.list(limit=limit, offset=offset)
        
        video_list = []
        for gen in generations:
            # Check if gen is a tuple and unpack it if necessary
            if isinstance(gen, tuple):
                gen = gen[0]  # Assume the first element contains the generation data
            
            # Now proceed with the existing logic
            if hasattr(gen, 'state') and gen.state == "completed" and hasattr(gen, 'assets'):
                video_url = None
                if isinstance(gen.assets, dict):
                    video_url = gen.assets.get("video")
                elif hasattr(gen.assets, 'video'):
                    video_url = gen.assets.video
                
                if video_url:
                    video_list.append({
                        "id": gen.id,
                        "prompt": gen.prompt,
                        "video_url": video_url,
                        "created_at": gen.created_at
                    })
        
        print(f"Found {len(video_list)} completed videos.")
        return video_list

# Example usage
if __name__ == "__main__":
    generator = LumaVideoGenerator()
    
    # List all videos
    all_videos = generator.list_all_videos()
    for video in all_videos:
        print(f"ID: {video['id']}")
        print(f"Prompt: {video['prompt']}")
        print(f"Video URL: {video['video_url']}")
        print(f"Created at: {video['created_at']}")
        print("---")