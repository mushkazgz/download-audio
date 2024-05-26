import os
import google.auth
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
import json

# Definir el alcance que necesitamos para la API de YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_info(json.load(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def download_audio(video_id, creds, output_path):
    try:
        youtube = build('youtube', 'v3', credentials=creds)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if not response['items']:
            print("No se encontró el video.")
            return

        video_title = response['items'][0]['snippet']['title']
        print(f"Descargando audio de '{video_title}'...")

        # Descargar el audio usando pytube
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            print("No se encontró un stream de solo audio.")
            return

        # Crear el directorio de salida si no existe
        os.makedirs(output_path, exist_ok=True)

        # Descargar y guardar el audio
        safe_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        audio_stream.download(output_path, filename=f"{safe_title}.mp3")

        print("Audio descargado exitosamente.")
    except HttpError as e:
        print("Ocurrió un error al llamar a la API de YouTube:", e)
    except Exception as e:
        print("Ocurrió un error al descargar el audio:", e)

if __name__ == "__main__":
    video_id = input("Por favor, introduce el ID del video de YouTube: ")
    output_path = r"/home/gilgamesh/josemanuel/DescargasNoisyogui"  # Ajusta esta ruta según sea necesario

    creds = authenticate()
    download_audio(video_id, creds, output_path)
