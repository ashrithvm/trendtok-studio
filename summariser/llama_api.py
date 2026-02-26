import os
from groq import Groq


def llama_api(desc: str) -> str:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")

    client = Groq(api_key=api_key)

    search_tag = desc.get("search_tag", "")
    category_line = f"Category: #{search_tag}\n" if search_tag else ""
    user_content = f"{category_line}Keywords:\n{desc['tags']}"

    response_idea = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a TikTok trend idea generator. Given a content category and keywords from trending videos, "
                    "give the user two ideas:\n"
                    "1. Trending — what top creators in this category are doing right now, framed as a direct "
                    "actionable suggestion to the user (use 'you'). 2 sentences max.\n"
                    "2. Unique Twist — a creative, differentiated angle that stands out from the current trend "
                    "in the same category. 2 sentences max.\n"
                    "Use this EXACT format, no extra text:\n"
                    "Trend Idea: [name]\n"
                    "Trend Concept: [concept]\n"
                    "Twist Idea: [name]\n"
                    "Twist Concept: [concept]"
                )
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        max_tokens=220,
    )

    response_song = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate audio descriptions for a music generation model. "
                    "Given a content category and keywords, describe the mood and sound of a 5-second background clip. "
                    "Be very concise — one sentence only."
                )
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=60,
    )

    return response_idea.choices[0].message.content, response_song.choices[0].message.content
