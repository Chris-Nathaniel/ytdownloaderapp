from urllib.parse import urlparse
import os
import re

from flask import Flask, redirect, url_for, render_template, request, send_file
import googleapiclient.discovery
import pytube
from icecream import ic

app = Flask(__name__)
app.static_folder = 'static'

# Set up the YouTube Data API credentials (replace with your own)
api_key = "AIzaSyCmdN4f5HmP0rv-FRCxk3Sp-IMKIDNupXo"
api_key2 = "AIzaSyC30B8x93OUoFso3TPOgOvDamMT5NzX41g"

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key2, static_discovery=False)


def is_valid_url(input_url):
    try:
        parsed_url = urlparse(input_url)
        return parsed_url.scheme in ("http", "https", "ftp")
    except ValueError:
        return False


# Function to delete MP4 files in a directory
def delete_mp4_files():
    try:
        # Get the directory path of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        files = os.listdir(script_dir)
        for file in files:
            if file.endswith(".mp4"):
                file_path = os.path.join(script_dir, file)
                os.remove(file_path)
                print(f"Deleted: {file_path}")
    except Exception as e:
        print(f"Error deleting MP4 files: {e}")


def get_vid_url(song_name):
    video_url = []
    try:
        # Search for videos using the YouTube Data API
        search_response = youtube.search().list(
            q=song_name,
            type="video",
            part="id",
            maxResults=5  # Adjust the number of results as needed
        ).execute()

        # Extract video IDs from the search results
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

        for i in range(5):
            if video_ids:
                url = "https://www.youtube.com/watch?v=" + video_ids[i]
                video_url.append(url)
            else:
                return "No videos found."
        print(f"video url: {video_url}")
        return video_url
    except Exception as e:
        return str(e)


def sanitize_filename(filename):
    # Remove or replace special characters with underscores
    sanitized = re.sub(r'[/|<>(#)&/""'']', '_', filename)
    return sanitized


def parse_video_id(video_url):
    parsed_url = urlparse(video_url)
    if parsed_url.netloc == "www.youtube.com" and parsed_url.path == "/watch":
        query_params = parsed_url.query.split("&")
        for param in query_params:
            param_parts = param.split("=")
            if len(param_parts) == 2 and param_parts[0] == "v":
                return param_parts[1]
    return None


def get_available_resolution(video_url):
    try:
        yt = pytube.YouTube(video_url)
        video_streams = yt.streams.filter(file_extension="mp4", progressive=True, type="video")
        # Extract unique resolutions using a set
        unique_resolutions = set(stream.resolution for stream in video_streams)
        # Sort the resolutions in ascending order
        sorted_resolutions = sorted(unique_resolutions, key=lambda x: int(x[:-1]))

        return sorted_resolutions
    except Exception as e:
        return str(e)


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        search_query = request.form.get("search")

        if is_valid_url(search_query):
            video_url = [search_query]
            title = [pytube.YouTube(video_url[0]).title]
            video_id = (parse_video_id(video_url[0]))
            url = f"https://www.youtube.com/embed/{video_id}"
            embed_url = [url]

            return render_template(
                'main.html',
                result=video_url,
                embed=embed_url,
                query=title,
                video_title=title,
                show_results=True
            )

        else:
            video_url = get_vid_url(search_query)
            embed_url = []
            title = []

            for x in range(5):
                video_id = (parse_video_id(video_url[x]))
                title.append(pytube.YouTube(video_url[x]).title)
                url = f"https://www.youtube.com/embed/{video_id}"
                embed_url.append(url)
            print(f"embed url: {embed_url}")

            return render_template(
                'main.html',
                result=video_url,
                embed=embed_url,
                query=search_query,
                video_title=title,
                show_results=True
            )
    else:
        return render_template('main.html')


@app.route("/download", methods=['POST'])
def download_video():
    if request.method == 'POST':
        video_url = ic(request.form.get("video_url"))
        selected_resolution = request.form.get("quality")
        try:
            delete_mp4_files()
            yt = pytube.YouTube(video_url)
            title = sanitize_filename(yt.title)
            video_filename = f"{title}.mp4"
            mp4_video = yt.streams.filter(
                resolution=selected_resolution,
                progressive=True,
                file_extension="mp4",
                type="video"
            ).first()
            mp4_video.download(filename=video_filename)
            return send_file(video_filename, as_attachment=True)

        except Exception as e:
            return str(e)


@app.route("/audio", methods=['POST'])
def download_audio():
    if request.method == 'POST':
        video_url = ic(request.form.get("video_url"))
        selected_resolution = request.form.get("quality")
        try:
            delete_mp4_files()
            yt = pytube.YouTube(video_url)
            title = sanitize_filename(yt.title)
            video_filename = f"{title}.mp3"
            mp4_video = yt.streams.filter(
              only_audio=True,
            ).first()
            mp4_video.download(filename=video_filename)
            return send_file(video_filename, as_attachment=True)

        except Exception as e:
            return str(e)

@app.route("/select", methods=['POST'])
def select_quality():
    if request.method == 'POST':
        video_url = [request.form.get("video_url")]
        title = [pytube.YouTube(video_url[0]).title]
        video_id = (parse_video_id(video_url[0]))
        url = f"https://www.youtube.com/embed/{video_id}"
        embed_url = [url]
        available_resolution = [get_available_resolution(video_url[0])]
        return render_template(
            'select_quality.html',
            result=video_url,
            embed=embed_url,
            video_title=title,
            available_resolution=available_resolution
        )
    else:
        return render_template('select_quality.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)