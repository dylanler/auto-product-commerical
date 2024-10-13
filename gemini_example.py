# Upload the video and print a confirmation.
video_file_name = "example_video.mp4"

print(f"Uploading file...")
video_file = genai.upload_file(path=video_file_name)
print(f"Completed upload: {video_file.uri}")

import time

# Check whether the file is ready to be used.
while video_file.state.name == "PROCESSING":
    print('.', end='')
    time.sleep(10)
    video_file = genai.get_file(video_file.name)

if video_file.state.name == "FAILED":
  raise ValueError(video_file.state.name)


# Create the prompt.
prompt = '''
Describe this video in detail.  
Capture the camera movements, lighting, and any other details.
Identify and label the objects in the video.
If there are humans, describe their clothing, aesthetic, appearance, and actions.
Output the aesthetics and vibe of the video.
'''

# Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

import typing_extensions as typing

class VideoMetadata(typing.TypedDict):
    video_description: str
    objects_in_video: list[str]
    humans_in_video: list[str]
    aesthetics_and_vibe: str


result = model.generate_content(
    prompt,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=list[Recipe]
    ),
)
print(result)

# Make the LLM request.
print("Making LLM inference request...")
response = model.generate_content([video_file, prompt],
                                  request_options={"timeout": 600})

