import time
import requests
import os
from datetime import datetime

class SongGenerator:
    def __init__(self, base_url='https://suno-api-eight-weld.vercel.app'):
        self.base_url = base_url

    def _make_request(self, endpoint, method='GET', payload=None):
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=payload, headers=headers)
        
        return response.json()

    def generate_audio(self, prompt, make_instrumental=False, wait_audio=False):
        payload = {
            "prompt": prompt,
            "make_instrumental": make_instrumental,
            "wait_audio": wait_audio
        }
        return self._make_request('/api/generate', 'POST', payload)

    def custom_generate_audio(self, payload):
        return self._make_request('/api/custom_generate', 'POST', payload)

    def extend_audio(self, payload):
        return self._make_request('/api/extend_audio', 'POST', payload)

    def get_audio_information(self, audio_ids):
        return self._make_request(f'/api/get?ids={audio_ids}')

    def get_quota_information(self):
        return self._make_request('/api/get_limit')

    def get_clip(self, clip_id):
        return self._make_request(f'/api/clip?id={clip_id}')

    def generate_whole_song(self, clip_id):
        payload = {"clip_id": clip_id}
        return self._make_request('/api/concat', 'POST', payload)

    def generate_lyrics(self, prompt):
        payload = {"prompt": prompt}
        return self._make_request('/api/generate_lyrics', 'POST', payload)

    def wait_for_audio(self, ids, max_attempts=60, sleep_time=5):
        for _ in range(max_attempts):
            data = self.get_audio_information(ids)

            print(f"Streaming data length: {len(data)}")
            #print(f"Streaming data: {data}")

            if all(item["status"] == 'streaming' for item in data):
                return data
            time.sleep(sleep_time)
        raise TimeoutError("Audio generation timed out")

    def download_audio(self, url, filename):
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
        else:
            raise Exception(f"Failed to download audio: HTTP {response.status_code}")

    def generate_song(self, prompt, make_instrumental=True, output_dir='generated_songs'):
        # Generate initial audio
        data = self.generate_audio(prompt, make_instrumental)

        print(f"Length of data: {len(data)}")
        
        # Wait for audio to be ready
        ids = ",".join(item['id'] for item in data)

        print(f"Ids: {ids}")
        

        audio_info = self.wait_for_audio(ids)

        print(f"Audio info length: {len(audio_info)}")
        #print(f"Audio info: {audio_info}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Download and save audio files
        mp3_files = []
        for i, item in enumerate(audio_info):
            filename = os.path.join(output_dir, f"generated_song_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{i+1}.mp3")
            mp3_file = self.download_audio(item['audio_url'], filename)
            mp3_files.append(mp3_file)
        
        return mp3_files

# Example usage
if __name__ == '__main__':
    generator = SongGenerator()
    
    prompt = "A catchy pop song about summer love, with upbeat rhythm and cheerful vocals. The lyrics should describe a perfect day at the beach with a new romance."
    
    print("Generating song...")
    try:
        mp3_files = generator.generate_song(prompt)
        print("Song generated successfully!")
        print("Generated MP3 files:")
        for file in mp3_files:
            print(file)
    except TimeoutError:
        print("Song generation timed out")
    except Exception as e:
        print(f"An error occurred: {str(e)}")