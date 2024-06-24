import os
import google.auth
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
import json
import logging
import random

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

def search_lofi_videos(creds):
    """
    Busca videos de música lo-fi en YouTube y devuelve una lista de IDs de videos.
    """
    try:
        youtube = build('youtube', 'v3', credentials=creds)
        request = youtube.search().list(
            part="snippet",
            maxResults=25,
            q="lofi music",
            type="video"
        )
        response = request.execute()
        
        # Obtener los IDs de los videos de la respuesta
        video_ids = [item['id']['videoId'] for item in response['items']]
        return video_ids
    except HttpError as e:
        logging.error(f"Ocurrió un error al llamar a la API de YouTube: {e}")
        return []

def is_live_stream(video_id, creds):
    """
    Comprueba si el video es un streaming en vivo.
    """
    try:
        youtube = build('youtube', 'v3', credentials=creds)
        request = youtube.videos().list(part="snippet,liveStreamingDetails", id=video_id)
        response = request.execute()

        if 'liveStreamingDetails' in response['items'][0]:
            return True
        return False
    except HttpError as e:
        logging.error(f"Ocurrió un error al llamar a la API de YouTube: {e}")
        return False

def download_audio(video_id, creds, output_path):
    """
    Descarga el audio de un video de YouTube dado su ID.
    """
    #Comprobamos que el audio no este en live
    if is_live_stream(video_id, creds):
        logging.info("El video es un streaming en vivo. Se omitirá la descarga.")
        return

    try:
        logging.debug(f"video_id: {video_id}")
        logging.debug(f"creds: {creds}")
        logging.debug(f"output_path: {output_path}")

        if is_live_stream(video_id, creds):
            logging.info("El video es un streaming en vivo. Se omitirá la descarga.")
            return

        youtube = build('youtube', 'v3', credentials=creds)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        logging.debug(f"Response from YouTube API: {response}")

        if not response['items']:
            logging.error("No se encontró el video.")
            return

        video_title = response['items'][0]['snippet']['title']
        logging.info(f"Descargando audio de '{video_title}'...")

        # Descargar el audio usando pytube
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            logging.error("No se encontró un stream de solo audio.")
            return

        # Crear el directorio de salida si no existe
        os.makedirs(output_path, exist_ok=True)

        # Descargar y guardar el audio
        safe_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        audio_stream.download(output_path, filename=f"{safe_title}.mp3")

        logging.info("Audio descargado exitosamente.")
    except HttpError as e:
        logging.error(f"Ocurrió un error al llamar a la API de YouTube: {e}")
    except Exception as e:
        logging.error(f"Ocurrió un error al descargar el audio: {e}")

def is_live_stream(video_id, creds):
    youtube = build('youtube', 'v3', credentials=creds)
    request = youtube.videos().list(part="snippet,liveStreamingDetails", id=video_id)
    response = request.execute()
    return 'liveStreamingDetails' in response['items'][0]

if __name__ == "__main__":
    output_path = r"/home/gilgamesh/josemanuel/DescargasNoisyogui"
    creds = authenticate()
    video_ids = search_lofi_videos(creds)
    
    if video_ids:
        video_id = random.choice(video_ids)
        while is_live_stream(video_id, creds):
            logging.info(f"El video {video_id} es un streaming en vivo. Intentando con otro.")
            video_ids.remove(video_id)
            if not video_ids:
                logging.error("No se encontraron videos de lo-fi que no sean en vivo.")
                break
            video_id = random.choice(video_ids)
        
        if video_ids:
            download_audio(video_id, creds, output_path)
    else:
        logging.error("No se encontraron videos de lo-fi para descargar.")
