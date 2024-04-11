import asyncio
import functools
import os
import sys
from os.path import join as ospath_join
from openai import OpenAI, AsyncOpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, set_api_key, voices
from elevenlabs.api.error import RateLimitError
from utils.initialize import fetch_auth_data, fetch_voice_id


# using this temporarily to observe async loop behavior
main_looping_counter = 0
narrator_looping_counter = 0


sys_messages = {
    "ATTENBOROUGH" : (
        "You are Sir David Attenborough. Narrate the picture of the human as "
        "if it is a nature documentary. Make it snarky and funny. Don't "
        "repeat yourself. Make it short. If I do anything remotely "
        "interesting, make a big deal about it!"
    ),
    
    "SCOTTISH" : (
        "You are Scottish actor James McAvoy, but way more "
        "cheeky and hilarious Scottish comedian. "
        " Narrate the picture of the human "
        " as if it's a satirical documentary. Make it snarky and "
        "funny. Don't repeat yourself. Keep it short, only 1 sentence; "
        "the sentence should read in less than 12 seconds. "
        "If I do anything remotely interesting, make a big deal about it!"
        "Lastly, if there were previous messages, you must try to "
        "tie in previous context when appropriate, so it sounds like you "
        "have a whole story planned."
    )
}


urlsafe_b64encode = base64.urlsafe_b64encode
b64encode = base64.b64encode
urandom = os.urandom
makedirs = os.makedirs


set_api_key(fetch_auth_data("elevenlabs_auth"))

client = AsyncOpenAI(api_key=fetch_auth_data("openai_auth"))
chat_completion_create = client.chat.completions.create


#def encode_image(image_path):
async def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            #time.sleep(0.1)
            await asyncio.sleep(0.1)


#def play_audio(text):
async def play_audio(text, loop):
    t0 = time.time()
    audio = await loop.run_in_executor(
        None,
        functools.partial(
            generate, text, voice=fetch_voice_id()
        )
    )
    #audio = generate(text, voice=fetch_voice_id())
    t1 = time.time()
    print(f'[play_audio] generate audio took: {round(t1 - t0, 3)} sec.')

    unique_id = b64encode(urandom(30)).decode("utf-8").rstrip("=")
    dir_path = ospath_join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = ospath_join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    t0 = time.time()
    await loop.run_in_executor(None, play, audio)
    t1 = time.time()
    print(f'[play_audio] play audio took: {round(t1 - t0, 3)} sec.')
    #play(audio)


def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]


#def analyze_image(base64_image, script):
async def analyze_image(base64_image, script):
    #response = chat_completion_create(
    response = await chat_completion_create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": sys_messages["SCOTTISH"],
            },
        ]
        + script
        + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


# quick micro-optimization func.
def create_line(line: str):
    return [{"role": "assistant", "content": line}]
        
# main looping component for narrator
async def narrator_loop(loop):
    script = []
    
    # temporary micro-optimizations -- dev work
    cwd = os.getcwd()
    
    global narrator_looping_counter
    
    while True:
        narrator_looping_counter += 1
        print(f'--- narrator_loop() count: {narrator_looping_counter}')
    
        # path to your image
        image_path = ospath_join(cwd, "./frames/frame.jpg")

        # getting the base64 encoding
        base64_image = await encode_image(image_path)

        # analyze posture
        print("👀 David is watching...")
        t0 = time.time()
        analysis = await analyze_image(base64_image, script=script)
        t1 = time.time()
        print(f'Image analysis time: {round(t1 - t0, 3)} sec.')

        print(f"🎙️ David says:\n{analysis}\n")

        print('About to play audio...')
        t0 = time.time()
        try:
            await play_audio(analysis, loop)
        except RateLimitError as e:
            print(f'{type(e).__name__}: {e}', file=sys.stderr)
        except Exception as e:
            print(f'[ERROR]: {type(e).__name__}: {e}')
        t1 = time.time()
        print(f'Time to process+play audio: {round(t1 - t0, 3)} sec.')

        script += create_line(analysis)

        print('[narrator_loop] Sleeping 3 seconds')
        await asyncio.sleep(3)


#def main():
async def main(loop):
    # we have the 'asyncio.ensure_future()' call again here,
    # so that the 'narrator_loop()' gets registered to run (again) in async
    print('Starting loop')
    asyncio.ensure_future(narrator_loop(loop))
    
    global main_looping_counter
    main_looping_counter += 1
    print(f'--- main() loop: {main_looping_counter}')
    
    #await asyncio.sleep(3)


if __name__ == "__main__":

    # we call 'asyncio.ensure_future()' first here, to register
    # the 'main()' function to be run in async
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main(loop))
    
    # we run the loop indefinitely, which indefinitely runs
    # the 'main' function that calls the primary looping
    # component: the 'narrator_loop()'
    loop.run_forever()
