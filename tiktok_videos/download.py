import os
import gdown
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Get service account file path from environment variable
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Check if the service account file exists
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(
        f"Google service account file not found: {SERVICE_ACCOUNT_FILE}. "
        "Please set the GOOGLE_SERVICE_ACCOUNT_FILE environment variable or "
        "place the service account JSON file in the project root."
    )

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)


def fetch_video_ids_from_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType='video/mp4'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    video_ids = [item['id'] for item in items]
    return video_ids


def download_videos(tag, output_dir):
    folders = {
        "#AI - #MachineLearning - #TechInnovation": "1vlFJcJYQ7Ca5NmkEB_Mz7eodD7SulUBt",
        "#Foodie - #RecipeOfTheDay - #CookingHacks": "1GsfEPqd-irGjbcbjl5i5HHErP88PBCTV",
        "#MakeupTutorial - #BeautyHacks - #SkincareRoutine": "12c8B8fhkJMhFOYt22Yg-EkdqFPLuu9nI",
        "#OOTD - #FashionInspo - #StyleTips": "1PcbHTuSpe-F0BZR6u1FwOLhQOt7jngK4",
        "#TravelVlog - #HiddenGems - #TravelTips": "1CDCg6ed_gDwXxVA9wCb964OlyoM167y3"
    }

    folder_id = None
    for folder_name, fid in folders.items():
        if f"#{tag}" in folder_name.split(" - "):
            folder_id = fid
            break

    if not folder_id:
        return []

    video_ids = fetch_video_ids_from_folder(folder_id)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

        video_files = []
        for i, video_id in enumerate(video_ids):
            if i <= 2:
                video_url = f"https://drive.google.com/uc?id={video_id}"
                output_path = os.path.join(output_dir, f'video_{i + 1}.mp4')
                gdown.download(video_url, output_path, quiet=False)
                video_files.append(output_path)
            else:
                break
    else:
        video_files = [os.path.join(output_dir, f) for f in os.listdir(
            output_dir) if f.endswith('.mp4')]

    return video_files
