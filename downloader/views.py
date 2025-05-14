import os
import uuid
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import YouTubeDownloadForm

def is_valid_youtube_url(url):
    """Validate if a URL is a valid YouTube URL"""
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
        return True
    return False

def get_video_id(url):
    """Extract the video ID from a YouTube URL"""
    if 'youtube.com' in url:
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('v', [None])[0]
    elif 'youtu.be' in url:
        return urlparse(url).path.lstrip('/')
    return None

def index(request):
    """Main view for the YouTube downloader"""
    form = YouTubeDownloadForm()
    context = {'form': form}
    return render(request, 'downloader/index.html', context)

def get_video_info(request):
    """AJAX endpoint to get video information before downloading"""
    if request.method == 'POST':
        form = YouTubeDownloadForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if not is_valid_youtube_url(url):
                return JsonResponse({'error': 'URL không hợp lệ. Vui lòng nhập URL YouTube.'}, status=400)
            
            try:
                # Use yt-dlp to get video info
                command = ['yt-dlp', '--dump-json', url]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                video_info_str = result.stdout.strip()
                
                # Properly parse the JSON output
                import json
                try:
                    video_info = json.loads(video_info_str)
                    title = video_info.get('title', 'Unknown Title')
                except json.JSONDecodeError:
                    # Fallback in case JSON parsing fails
                    title = 'Unknown Title'
                
                # Return the video information
                return JsonResponse({
                    'success': True,
                    'videoId': get_video_id(url),
                    'title': title,
                    'format': form.cleaned_data['format_choice'],
                    'quality': form.cleaned_data.get('quality', 'highest')
                })
            except Exception as e:
                return JsonResponse({'error': f'Lỗi khi xử lý video: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Yêu cầu không hợp lệ'}, status=400)

@require_POST
def download(request):
    """Handle the download request"""
    form = YouTubeDownloadForm(request.POST)
    if form.is_valid():
        url = form.cleaned_data['url']
        format_choice = form.cleaned_data['format_choice']
        quality = form.cleaned_data.get('quality', 'highest')
        
        if not is_valid_youtube_url(url):
            return render(request, 'downloader/index.html', {
                'form': form, 
                'error': 'URL không hợp lệ. Vui lòng nhập URL YouTube.'
            })
        
        try:
            # Create temp directory to store download
            temp_dir = tempfile.mkdtemp(dir=settings.MEDIA_ROOT)
            output_template = os.path.join(temp_dir, 'download')
            
            # Prepare download command based on format choice
            if format_choice == 'mp3':
                # Audio download
                filename = f"{output_template}.%(ext)s"
                command = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '-o', filename,
                    url
                ]
                # Add quality flag if specified
                if quality == 'highest':
                    command.insert(2, '--audio-quality', '0')
                elif quality == 'medium':
                    command.insert(2, '--audio-quality', '5')
                elif quality == 'lowest':
                    command.insert(2, '--audio-quality', '9')
            else:
                # Video download (mp4)
                filename = f"{output_template}.%(ext)s"
                command = [
                    'yt-dlp',
                    # Ensure we get a format that's ready to play without remuxing
                    '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    '--merge-output-format', 'mp4',  # Force merge to mp4
                    '--recode-video', 'mp4',        # Recode if needed
                    '-o', filename,
                    url
                ]
                # Add quality flag based on selection
                if quality == 'medium':
                    command[2] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
                elif quality == 'lowest':
                    command[2] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
            
            # Run the download command
            subprocess.run(command, check=True)
            
            # Find the downloaded file
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                raise Exception('Không tìm thấy file sau khi tải xuống.')
            
            download_path = os.path.join(temp_dir, downloaded_files[0])
            file_size = os.path.getsize(download_path)
            
            # Get video info for filename
            info_command = ['yt-dlp', '--get-title', url]
            result = subprocess.run(info_command, capture_output=True, text=True, check=True)
            video_title = result.stdout.strip().replace('/', '_').replace('\\', '_')
            
            # Clean up the title for filename use
            safe_title = ''.join(c for c in video_title if c.isalnum() or c in ' -_').strip()
            if format_choice == 'mp3':
                content_type = 'audio/mpeg'
                filename = f"{safe_title}.mp3"
            else:
                content_type = 'video/mp4'
                filename = f"{safe_title}.mp4"
            
            # Return the file as a response
            response = FileResponse(
                open(download_path, 'rb'),
                content_type=content_type,
                as_attachment=True,
                filename=filename
            )
            
            # Add Content-Length header
            response['Content-Length'] = file_size
            return response
            
        except Exception as e:
            return render(request, 'downloader/index.html', {
                'form': form, 
                'error': f'Lỗi khi tải xuống: {str(e)}'
            })
    
    return render(request, 'downloader/index.html', {'form': form})
