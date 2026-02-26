import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import moviepy.editor as mp
from groq import Groq


def transcribe_audio_from_video(video_file: str) -> str:
    """
    Transcribe audio from a video file using Groq Whisper.
    Returns empty string on any failure (no audio track, API error, etc).
    Temp WAV file is always cleaned up.
    """
    name = video_file.split('.')[0].split('/')[-1]
    audio_path = f"temp_audio{name}.wav"

    try:
        video = mp.VideoFileClip(video_file)
        if video.audio is None:
            print(f"No audio track in {video_file}")
            return ''

        video.audio.write_audiofile(audio_path, logger=None)

        api_key = os.getenv('GROQ_API_KEY')
        client = Groq(api_key=api_key)

        with open(audio_path, 'rb') as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()),
                model='whisper-large-v3-turbo',
                language='en',
                response_format='text'
            )

        # response_format='text' returns a plain string
        return transcription if isinstance(transcription, str) else transcription.text

    except Exception as e:
        print(f"Transcription failed for {video_file}: {e}")
        return ''

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def llama_api_summary_tag(desc: str, tag: str = '') -> str:
    """
    Summarize text and extract hashtag keywords using Groq (Llama 3.1 8B).
    The tag anchors the LLM to the correct category and filters out song lyrics.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")

    client = Groq(api_key=api_key)

    category_context = f" The content is from videos in the #{tag} category." if tag else ""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are analyzing transcriptions from short-form videos.{category_context} "
                    "Ignore all song lyrics, music, and background audio — focus only on spoken "
                    "tutorial, instructional, or informational content relevant to the category. "
                    "Summarize the relevant content in less than 80 words. "
                    "Give the top tags/keywords for this summarized text (at least one tag for each sentence) "
                    "along with the summarized text."
                ),
            },
            {"role": "user", "content": desc},
        ],
    )

    return response.choices[0].message.content


def text_cleaning(input_text: str):
    """
    Extract summary and tags from LLM response.
    Returns (summary_text, tags_text). Either may be empty if delimiters not found.
    """
    summary_start = "Here is a summary of the text in under 80 words:\n\n"
    summary_end = "\n\nTop tags/keywords:\n\n"
    tags_start = "\n\nTop tags/keywords:\n\n"

    summary_text = input_text[
        input_text.find(summary_start) + len(summary_start): input_text.find(summary_end)
    ].strip()

    tags_text = input_text[input_text.find(tags_start) + len(tags_start):].strip()
    tags_text = tags_text.replace("* ", "").replace("\n*", "\n").strip()

    return summary_text, tags_text


def t4_api(video_files: List[str], metadata_texts: List[str] = None, tag: str = '') -> Dict:
    """
    Transcribe videos and extract trend tags with a 3-layer fallback:

    Layer 1 — Groq Whisper transcription of video audio (best quality)
    Layer 2 — yt-dlp metadata (video titles/descriptions) if transcription fails
    Layer 3 — Raw search tag if no content available at all
    """
    if metadata_texts is None:
        metadata_texts = []

    all_transcriptions = []

    with ThreadPoolExecutor() as executor:
        future_to_video = {
            executor.submit(transcribe_audio_from_video, vf): vf
            for vf in video_files
        }
        for future in as_completed(future_to_video):
            result = future.result()
            if result.strip():
                print(f"Transcription for {future_to_video[future]}:\n{result}\n")
                all_transcriptions.append(result)

    # Layer 1: use transcriptions
    if all_transcriptions:
        content = "\n\n".join(all_transcriptions)
    # Layer 2: fall back to yt-dlp video metadata
    elif metadata_texts:
        print("No transcriptions succeeded — using video metadata as fallback")
        content = "\n\n".join(metadata_texts)
    # Layer 3: fall back to the search tag itself
    elif tag:
        print("No metadata available — using search tag as fallback")
        content = f"TikTok trending content related to: #{tag}"
    else:
        content = "trending TikTok content"

    summary_tag = llama_api_summary_tag(content, tag=tag)
    summary_text, tags_text = text_cleaning(summary_tag)

    return {
        "summary": summary_text,
        "tags": tags_text if tags_text else content,
        "search_tag": tag,
    }
