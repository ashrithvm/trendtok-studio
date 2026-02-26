from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, url_for, session, send_from_directory
from flask_bootstrap import Bootstrap
from music_gen.api import gen_api
from summariser.llama_api import llama_api
from tiktok_to_text.api import t4_api
from tiktok_videos.download import download_videos
from animate_text.api import generate_image
import json
import os
import shutil

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-dev-key-change-in-production')
Bootstrap(app)

# Clear downloaded video cache on every startup so searches always fetch fresh content
_video_cache = os.path.join(os.path.dirname(__file__), 'static', 'video')
if os.path.exists(_video_cache):
    shutil.rmtree(_video_cache)
os.makedirs(_video_cache, exist_ok=True)


@app.route('/')
def home():
    trending_tags = ["MakeupTutorial", "BeautyHacks", "SkincareRoutine",  "TravelVlog", "HiddenGems",
                     "TravelTips", "Foodie", "RecipeOfTheDay", "CookingHacks", "OOTD", "FashionInspo",
                     "StyleTips", "AI", "MachineLearning", "TechInnovation"]

    return render_template('index.html', trending_tags=trending_tags)


def extract_value_from_json(json_string):
    try:
        data = json.loads(json_string)
        if isinstance(data, list) and len(data) > 0 and "value" in data[0]:
            return data[0]["value"]
        else:
            return None
    except json.JSONDecodeError:
        return None


@app.route('/search', methods=['POST'])
def search():
    search_tags = extract_value_from_json(request.form.get('search_tags'))

    if not search_tags:
        return redirect(url_for('home'))

    output_dir = os.path.join('static', 'video', search_tags)

    # Download videos — yt-dlp primary, Google Drive fallback
    video_files, metadata_texts = download_videos(search_tags, output_dir)

    video_urls = [url_for('static', filename=os.path.join(
        'video', search_tags, os.path.basename(video))) for video in video_files]

    session['video_urls'] = [os.path.abspath(v) for v in video_files]
    session['metadata_texts'] = metadata_texts
    session['search_tag'] = search_tags
    return render_template('video.html', video_urls=video_urls)


@ app.route('/generate_idea', methods=['POST'])
def generate_idea():
    video_urls = session.get('video_urls', [])
    metadata_texts = session.get('metadata_texts', [])
    search_tag = session.get('search_tag', '')

    text_summary = t4_api(video_urls, metadata_texts=metadata_texts, tag=search_tag)

    # Get the idea and song descriptions from the Llama API
    idea_description, song_description = llama_api(text_summary)

    print("Idea Description:", idea_description)
    print("Song Description:", song_description)

    # Extract the "Trend Name"
    trend_name_start = idea_description.find(
        "Trend Idea:") + len("Trend Idea:")
    trend_name_end = idea_description.find("Trend Concept:")
    trend_name = idea_description[trend_name_start:trend_name_end].strip().strip(
        '"')

    print("Trend Name:", trend_name)

    # Extract Trend Concept (everything between "Trend Concept:" and "Twist Idea:")
    video_idea_start = idea_description.find("Trend Concept:") + len("Trend Concept:")
    twist_idea_marker = idea_description.find("Twist Idea:")
    video_idea_raw = idea_description[video_idea_start:twist_idea_marker if twist_idea_marker != -1 else None].strip()
    formatted_video_idea = '\n'.join(line.strip() for line in video_idea_raw.split('\n'))

    # Extract Twist Idea name and concept
    twist_name = ''
    twist_concept = ''
    if twist_idea_marker != -1:
        twist_name_start = twist_idea_marker + len("Twist Idea:")
        twist_concept_marker = idea_description.find("Twist Concept:")
        twist_name = idea_description[twist_name_start:twist_concept_marker if twist_concept_marker != -1 else None].strip().strip('"')
        if twist_concept_marker != -1:
            twist_concept = idea_description[twist_concept_marker + len("Twist Concept:"):].strip()

    print("Trend Name:", trend_name)
    print("Trend Idea:", formatted_video_idea)
    print("Twist Name:", twist_name)
    print("Twist Concept:", twist_concept)

    session['idea'] = trend_name
    session['tags'] = text_summary["tags"]
    session['song_description'] = song_description
    session['concept'] = formatted_video_idea

    return jsonify(
        idea=trend_name,
        concept=formatted_video_idea,
        twist_name=twist_name,
        twist_concept=twist_concept
    )


@ app.route('/generate_media', methods=['POST'])
def generate_media():
    song_description = session.get('song_description', '')
    tags = session.get('tags', '')

    if not song_description or not tags:
        return jsonify(error="Missing data for generating media"), 400

    # Generate the image using the tags
    output_img_path = os.path.join('static', 'gen_img', f"{tags[0]}.png")
    generate_image(tags, output_img_path)
    img_url = url_for('static', filename=f'gen_img/{tags[0]}.png')

    # Generate the audio using the song description
    output_file_path = gen_api(song_description, 'new_audio', 6)

    audio_url = url_for(
        'static', filename=f'audio/{os.path.basename(output_file_path)}')

    return jsonify(audio_url=audio_url, img_url=img_url)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)
