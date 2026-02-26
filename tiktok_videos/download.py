import os
import gdown
import yt_dlp
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

FOLDERS = {
    "#AI - #MachineLearning - #TechInnovation": "1vlFJcJYQ7Ca5NmkEB_Mz7eodD7SulUBt",
    "#Foodie - #RecipeOfTheDay - #CookingHacks": "1GsfEPqd-irGjbcbjl5i5HHErP88PBCTV",
    "#MakeupTutorial - #BeautyHacks - #SkincareRoutine": "12c8B8fhkJMhFOYt22Yg-EkdqFPLuu9nI",
    "#OOTD - #FashionInspo - #StyleTips": "1PcbHTuSpe-F0BZR6u1FwOLhQOt7jngK4",
    "#TravelVlog - #HiddenGems - #TravelTips": "1CDCg6ed_gDwXxVA9wCb964OlyoM167y3"
}

# Drive client is optional — only needed for the fallback
drive_service = None
if os.path.exists(SERVICE_ACCOUNT_FILE):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Warning: Could not initialize Google Drive client: {e}")


def _download_via_ytdlp(tag, output_dir, max_videos=5):
    """
    Download up to max_videos YouTube Shorts for a hashtag using yt-dlp.
    Returns (video_files, metadata_texts).
    metadata_texts contains title + description strings for each video,
    used as fallback content when audio transcription fails.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'mp4/18/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': os.path.join(output_dir, 'video_%(autonumber)03d.mp4'),
        'playlistend': max_videos,
        'quiet': True,
        'no_warnings': True,
    }

    url = f'https://www.youtube.com/results?search_query=%23{tag}+shorts'
    metadata_texts = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if info and 'entries' in info:
            for entry in (info['entries'] or [])[:max_videos]:
                if not entry:
                    continue
                parts = []
                if entry.get('title'):
                    parts.append(entry['title'])
                if entry.get('description'):
                    parts.append(entry['description'])
                if parts:
                    metadata_texts.append(' '.join(parts))

        video_files = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith('.mp4')
        ])

        if not video_files and os.path.exists(output_dir):
            os.rmdir(output_dir)

        return video_files, metadata_texts

    except Exception as e:
        print(f"yt-dlp failed for #{tag}: {e}")
        if os.path.exists(output_dir) and not os.listdir(output_dir):
            os.rmdir(output_dir)
        return [], []


def _download_via_drive(tag, output_dir, max_videos=3):
    """
    Fallback: download videos from Google Drive using the service account.
    Returns list of local file paths.
    """
    if not drive_service:
        print("Google Drive client not available — no fallback possible")
        return []

    folder_id = None
    for folder_name, fid in FOLDERS.items():
        if f"#{tag}" in folder_name.split(" - "):
            folder_id = fid
            break

    if not folder_id:
        print(f"No Drive folder mapped for #{tag}")
        return []

    query = f"'{folder_id}' in parents and mimeType='video/mp4'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    video_ids = [item['id'] for item in results.get('files', [])]

    if not video_ids:
        return []

    os.makedirs(output_dir, exist_ok=True)
    video_files = []
    for i, video_id in enumerate(video_ids[:max_videos]):
        output_path = os.path.join(output_dir, f'video_{i + 1}.mp4')
        gdown.download(f"https://drive.google.com/uc?id={video_id}", output_path, quiet=False)
        video_files.append(output_path)

    return video_files


def download_videos(tag, output_dir):
    """
    Download videos for a tag with automatic fallback.

    Primary:  yt-dlp  → live TikTok videos for the hashtag
    Fallback: Google Drive → pre-uploaded videos

    Returns:
        (video_files, metadata_texts)
        video_files    — list of local MP4 paths
        metadata_texts — list of title/description strings from yt-dlp (empty on Drive fallback)
    """
    # Return cached videos if the directory already has MP4s
    if os.path.exists(output_dir):
        cached = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith('.mp4')
        ])
        if cached:
            return cached, []

    # Try yt-dlp first
    video_files, metadata_texts = _download_via_ytdlp(tag, output_dir)
    if video_files:
        print(f"yt-dlp: downloaded {len(video_files)} videos for #{tag}")
        return video_files, metadata_texts

    # Fall back to Google Drive
    print(f"yt-dlp failed for #{tag} — falling back to Google Drive")
    video_files = _download_via_drive(tag, output_dir)
    return video_files, []
