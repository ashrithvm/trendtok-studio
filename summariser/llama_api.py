import os
from groq import Groq


def llama_api(desc: str) -> str:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")

    client = Groq(api_key=api_key)

    response_idea = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a TikTok trend idea generator which can come up with a new trend idea. Your response should include a title starting with 'Trend Idea:', followed by a concise description starting with 'Trend Concept:'."
            },
            {
                "role": "user",
                "content": desc["tags"],
            },
        ],
        max_tokens=250,
    )

    response_song = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a tiktok trend generator which can take tags and generate audio cues to be given to a Music generator model. Your response includes only the audio description for a 5 second clip. It is very concise."},
            {"role": "user", "content": desc["tags"]},
        ],
    )

    return response_idea.choices[0].message.content, response_song.choices[0].message.content
