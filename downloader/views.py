import os
import uuid
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse, StreamingHttpResponse
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# Dictionary to store download progress information
download_progress = {}

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
                # Use yt-dlp to get video info with additional options to bypass protection
                command = [
                    'yt-dlp', 
                    '--dump-json',
                    '--no-check-certificates',  # Skip HTTPS certificate validation
                    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Use realistic user agent
                    '--skip-download',  # Skip downloading the actual video
                    '--force-ipv4',     # Force IPv4 to avoid some blocks
                    '--sleep-interval', '3', '--max-sleep-interval', '6',  # Add delay between requests
                    '--ignore-config',   # Ignore any problematic user config
                    url
                ]
                result = subprocess.run(command, capture_output=True, text=True)
                
                # Check for bot detection in stderr
                stderr = result.stderr.strip()
                if result.returncode != 0:
                    if 'Sign in to confirm you\'re not a bot' in stderr or 'Please sign in' in stderr:
                        # YouTube bot protection triggered
                        # Try to get just the title directly as a fallback
                        try:
                            title_command = ['yt-dlp', '--get-title', '--no-check-certificates', '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', '--force-ipv4', '--ignore-config', url]
                            title_result = subprocess.run(title_command, capture_output=True, text=True)
                            if title_result.returncode == 0:
                                title = title_result.stdout.strip()
                                # We can continue with just the title
                                return JsonResponse({
                                    'success': True,
                                    'videoId': get_video_id(url),
                                    'title': title,
                                    'format': form.cleaned_data['format_choice'],
                                    'quality': form.cleaned_data.get('quality', 'highest')
                                })
                        except Exception:
                            pass
                        
                        return JsonResponse({
                            'error': 'YouTube yêu cầu xác minh không phải là bot. Vui lòng thử lại sau hoặc tiến hành tải xuống trực tiếp.',
                            'bot_protection': True
                        }, status=429)
                    else:
                        # Other error
                        return JsonResponse({'error': f'Lỗi khi xử lý video: {stderr}'}, status=500)
                
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

# Progress monitoring endpoint
@csrf_exempt
def check_progress(request):
    """API endpoint to check the progress of a download"""
    if request.method == 'POST':
        download_id = request.POST.get('download_id')
        if download_id and download_id in download_progress:
            return JsonResponse(download_progress[download_id])
    return JsonResponse({'progress': 0, 'status': 'unknown'})

@require_POST
def download(request):
    """Handle the download request"""
    form = YouTubeDownloadForm(request.POST)
    if form.is_valid():
        url = form.cleaned_data['url']
        format_choice = form.cleaned_data['format_choice']
        quality = form.cleaned_data.get('quality', 'highest')
        download_id = request.POST.get('download_id', str(uuid.uuid4()))
        
        # Initialize progress tracking
        download_progress[download_id] = {
            'progress': 5,
            'status': 'starting',
            'message': 'Đang chuẩn bị tải xuống...'
        }
        
        if not is_valid_youtube_url(url):
            return render(request, 'downloader/index.html', {
                'form': form, 
                'error': 'URL không hợp lệ. Vui lòng nhập URL YouTube.'
            })
        
        try:
            # Create temp directory to store download
            temp_dir = tempfile.mkdtemp(dir=settings.MEDIA_ROOT)
            output_template = os.path.join(temp_dir, 'download')
            
            # Common yt-dlp options to bypass restrictions
            common_options = [
                '--no-check-certificates',  # Skip HTTPS certificate validation
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Use realistic user agent
                '--no-playlist',          # Don't download playlists
                '--extractor-retries', '3',  # Retry extraction
                '--ignore-errors',       # Continue on download errors
                '--force-ipv4',          # Force IPv4 to avoid some blocks
                '--sleep-interval', '3', '--max-sleep-interval', '6',  # Add delay between requests
                '--ignore-config',        # Ignore any problematic user config
                '--mark-watched',        # Mark videos as watched to avoid suspicion
                '--no-warnings'          # Hide deprecation warnings
            ]
            
            # Prepare download command based on format choice
            if format_choice == 'mp3':
                # Audio download
                filename = f"{output_template}.%(ext)s"
                command = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '-o', filename,
                ]
                # Add quality flag if specified
                if quality == 'highest':
                    command.extend(['--audio-quality', '0'])
                elif quality == 'medium':
                    command.extend(['--audio-quality', '5'])
                elif quality == 'lowest':
                    command.extend(['--audio-quality', '9'])
                
                # Add common options and URL
                command.extend(common_options)
                command.append(url)
            else:
                # Video download (mp4)
                filename = f"{output_template}.%(ext)s"
                format_option = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                
                # Modify format based on quality selection
                if quality == 'medium':
                    format_option = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
                elif quality == 'lowest':
                    format_option = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
                
                command = [
                    'yt-dlp',
                    # Ensure we get a format that's ready to play without remuxing
                    '-f', format_option,
                    '--merge-output-format', 'mp4',  # Force merge to mp4
                    '--recode-video', 'mp4',        # Recode if needed
                    '-o', filename,
                ]
                
                # Add common options and URL
                command.extend(common_options)
                command.append(url)
            
            # Extract video ID for filename in case title retrieval fails
            video_id = get_video_id(url) or 'video'
            
            # Update progress
            download_progress[download_id] = {
                'progress': 30,
                'status': 'downloading',
                'message': 'Đang tải xuống video...'
            }
            
            # Add progress tracking to yt-dlp command
            progress_options = [
                '--newline',          # Force progress on new lines
                '--progress',         # Show progress
                '--progress-template', '%(progress.downloaded_bytes)s/%(progress.total_bytes)s'
            ]
            
            # Add progress options to command
            for option in progress_options:
                command.insert(-1, option)  # Insert before URL
            
            # Run the download command
            try:
                # Create a process with pipe for output to track progress
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Read output line by line to track progress
                for line in process.stdout:
                    line = line.strip()
                    if '/' in line and not line.startswith('ERROR'):
                        try:
                            current, total = line.split('/')
                            if total and total.isdigit() and int(total) > 0:
                                percent = min(85, 30 + (int(current) / int(total) * 55))
                                download_progress[download_id] = {
                                    'progress': int(percent),
                                    'status': 'downloading',
                                    'message': f'Đang tải xuống video... {int(percent)}%'
                                }
                        except (ValueError, ZeroDivisionError):
                            pass
                
                # Wait for the process to complete
                process.wait()
                
                # Check if the process completed successfully
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)
                
            except subprocess.CalledProcessError as e:
                # Capture stderr for error analysis
                stderr = e.stderr.lower() if hasattr(e, 'stderr') and e.stderr else ''
                
                # Update progress status
                download_progress[download_id] = {
                    'progress': 40,
                    'status': 'retrying',
                    'message': 'Đang thử phương pháp khác...'
                }
                
                # If it fails due to bot protection or any other error, try direct approach
                # Use most basic format to maximize chance of success
                fallback_options = [
                    '--no-check-certificates', 
                    '--force-ipv4', 
                    '--ignore-config',
                    '--geo-bypass', 
                    '--no-warnings', 
                    '--ignore-errors',
                    '--no-playlist',
                    '--newline',          # Force progress on new lines
                    '--progress',         # Show progress
                    '--progress-template', '%(progress.downloaded_bytes)s/%(progress.total_bytes)s'
                ]
                
                if format_choice == 'mp3':
                    # Use the simplest audio extraction approach
                    alt_command = [
                        'yt-dlp', 
                        '-x', 
                        '--audio-format', 'mp3', 
                        '--extract-audio',  # Force audio extraction
                        '--audio-quality', '0' if quality == 'highest' else ('5' if quality == 'medium' else '9'),
                        '-o', filename
                    ]
                    alt_command.extend(fallback_options)
                    alt_command.append(url)
                else:
                    # Use simplest video format approach
                    format_str = 'best'
                    if quality == 'medium':
                        format_str = 'best[height<=720]/best'
                    elif quality == 'lowest':
                        format_str = 'best[height<=480]/best'
                        
                    alt_command = [
                        'yt-dlp', 
                        '-f', format_str,
                        '--recode-video', 'mp4',
                        '-o', filename
                    ]
                    alt_command.extend(fallback_options)
                    alt_command.append(url)
                
                try:
                    # Update progress
                    download_progress[download_id] = {
                        'progress': 50,
                        'status': 'retrying',
                        'message': 'Đang dùng phương pháp thứ hai...'
                    }
                    
                    # Run the alternative command with progress tracking
                    process = subprocess.Popen(
                        alt_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Read output line by line to track progress
                    for line in process.stdout:
                        line = line.strip()
                        if '/' in line and not line.startswith('ERROR'):
                            try:
                                current, total = line.split('/')
                                if total and total.isdigit() and int(total) > 0:
                                    percent = min(75, 50 + (int(current) / int(total) * 25))
                                    download_progress[download_id] = {
                                        'progress': int(percent),
                                        'status': 'downloading',
                                        'message': f'Phương pháp thay thế... {int(percent)}%'
                                    }
                            except (ValueError, ZeroDivisionError):
                                pass
                    
                    # Wait for the process to complete
                    process.wait()
                    
                    # Check if the process completed successfully
                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(process.returncode, alt_command)
                    
                except subprocess.CalledProcessError as e2:
                    # If both methods fail, try direct link with minimal processing
                    download_progress[download_id] = {
                        'progress': 80,
                        'status': 'final_attempt',
                        'message': 'Đang thử phương pháp cuối cùng...'
                    }
                    
                    last_resort_command = [
                        'yt-dlp',
                        '-o', filename,
                        '--force-ipv4',
                        '--ignore-config',
                        '--no-warnings',
                        '--progress',
                        url
                    ]
                    subprocess.run(last_resort_command, check=True)
            
            # Update progress to processing
            download_progress[download_id] = {
                'progress': 90,
                'status': 'processing',
                'message': 'Đang xử lý file tải xuống...'
            }
            
            # Find the downloaded file
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                download_progress[download_id] = {
                    'progress': 100,
                    'status': 'error',
                    'message': 'Không tìm thấy file sau khi tải xuống.'
                }
                raise Exception('Không tìm thấy file sau khi tải xuống.')
            
            download_path = os.path.join(temp_dir, downloaded_files[0])
            
            # Verify file exists and has content
            if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
                download_progress[download_id] = {
                    'progress': 100,
                    'status': 'error',
                    'message': 'File tải xuống trống hoặc bị lỗi.'
                }
                raise Exception('File tải xuống trống hoặc bị lỗi.')
                
            file_size = os.path.getsize(download_path)
            
            # Update progress to completion
            download_progress[download_id] = {
                'progress': 95,
                'status': 'preparing',
                'message': 'Đang chuẩn bị trả về file...'
            }
            
            # Try to get video title for filename, but handle failure gracefully
            video_title = video_id  # Default to video ID if title retrieval fails
            try:
                info_command = [
                    'yt-dlp', 
                    '--get-title', 
                    '--no-check-certificates',
                    '--force-ipv4',
                    '--ignore-config',
                    '--no-warnings',
                    '--quiet',
                    url
                ]
                result = subprocess.run(info_command, capture_output=True, text=True, check=True)
                title_result = result.stdout.strip()
                if title_result:
                    video_title = title_result.replace('/', '_').replace('\\', '_')
            except subprocess.CalledProcessError:
                # If unable to get title, use the video ID or timestamp as filename
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                video_title = f"{video_id}_{timestamp}"
            
            # Clean up the title for filename use
            safe_title = ''.join(c for c in video_title if c.isalnum() or c in ' -_').strip()
            if format_choice == 'mp3':
                content_type = 'audio/mpeg'
                filename = f"{safe_title}.mp3"
            else:
                content_type = 'video/mp4'
                filename = f"{safe_title}.mp4"
            
            # Update progress to complete
            download_progress[download_id] = {
                'progress': 100,
                'status': 'complete',
                'message': 'Hoàn thành!'
            }
            
            # Return the file as a response
            response = FileResponse(
                open(download_path, 'rb'),
                content_type=content_type,
                as_attachment=True,
                filename=filename
            )
            
            # Add Content-Length header
            response['Content-Length'] = file_size
            
            # Add a cleanup function to delete all files in media directory after response is sent
            def cleanup_media_directory(response):
                try:
                    # Delete all files and subdirectories in the media directory
                    for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.unlink(file_path)
                            except Exception as e:
                                print(f"Error deleting file {file_path}: {e}")
                        for dir in dirs:
                            dir_path = os.path.join(root, dir)
                            try:
                                os.rmdir(dir_path)
                            except Exception as e:
                                print(f"Error deleting directory {dir_path}: {e}")
                    print("Media directory cleaned successfully")
                except Exception as e:
                    print(f"Error cleaning media directory: {e}")
                return response
            
            # Register the cleanup function to be called after the response is sent
            response._resource_closers.append(lambda: cleanup_media_directory(response))
            
            return response
            
        except Exception as e:
            return render(request, 'downloader/index.html', {
                'form': form, 
                'error': f'Lỗi khi tải xuống: {str(e)}'
            })
    
    return render(request, 'downloader/index.html', {'form': form})
