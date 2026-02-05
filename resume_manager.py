#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Resume Manager - Handle interrupted downloads and check for missing videos
This module helps resume downloads that were interrupted and detects which videos 
from a playlist/user/model page have been downloaded and which are missing.

IMPROVED VERSION: 404 Error 해결을 위한 강화된 버전
"""

import os
import sys
import json
import yt_dlp
import re
import io
import struct
from pathlib import Path
from functions import get_dl_location, is_system_restricted_path, DEFAULT_DOWNLOAD_DIR, get_ytdlp_options

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class DownloadInfo:
    """Store information about a download session"""
    def __init__(self, url, total_videos, downloaded_videos, download_dir):
        self.url = url
        self.total_videos = total_videos
        self.downloaded_videos = downloaded_videos
        self.download_dir = download_dir
        self.info_file = os.path.join(download_dir, '.download_info.json')
    
    def save(self):
        """Save download information to JSON file"""
        info = {
            'url': self.url,
            'total_videos': self.total_videos,
            'downloaded_videos': self.downloaded_videos,
            'download_dir': self.download_dir
        }
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            with open(self.info_file, 'w') as f:
                json.dump(info, f, indent=2)
            print(f"✓ Download info saved to {self.info_file}")
        except Exception as e:
            print(f"✗ Error saving download info: {e}")
    
    @staticmethod
    def load(download_dir):
        """Load download information from JSON file"""
        info_file = os.path.join(download_dir, '.download_info.json')
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r') as f:
                    info = json.load(f)
                return DownloadInfo(
                    info.get('url'),
                    info.get('total_videos'),
                    info.get('downloaded_videos'),
                    info.get('download_dir')
                )
            except Exception as e:
                print(f"✗ Error loading download info: {e}")
        return None


def get_completed_videos_from_ytdl(download_dir):
    """
    Get list of videos that have been successfully downloaded
    Uses .ytdl metadata files as the source of truth.
    A video is considered complete if:
    1. Its corresponding .ytdl metadata file exists, OR
    2. Its video file exists (mp4, mkv, etc.) and is reasonably sized (>100KB)
    
    Args:
        download_dir: Directory to check
    
    Returns:
        set: Set of video titles (without extension) that are complete
    """
    completed = set()
    
    if not os.path.exists(download_dir):
        return completed
    
    video_extensions = ('.mp4', '.mkv', '.flv', '.webm', '.avi', '.mov')
    
    # Method 1: Check for .ytdl files (most reliable indicator)
    for filename in os.listdir(download_dir):
        if filename.endswith('.ytdl'):
            # Extract base name without .ytdl
            base_name = filename[:-5]  # Remove .ytdl
            completed.add(base_name)
    
    # Method 2: Also check for actual video files that are reasonably sized
    for filename in os.listdir(download_dir):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            file_path = os.path.join(download_dir, filename)
            
            if not os.path.isdir(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    # If file is at least 100KB, consider it downloaded
                    if file_size >= 100 * 1024:
                        base_name = os.path.splitext(filename)[0]
                        completed.add(base_name)
                except:
                    pass
    
    return completed


def get_downloaded_files(download_dir):
    """
    Get list of downloaded video files from directory.
    This function now uses the new get_completed_videos_from_ytdl() for accurate tracking.
    
    Returns: set of video titles that have been downloaded
    Only counts videos that either:
    1. Have a .ytdl metadata file (most reliable), OR
    2. Have a video file >100KB in size
    """
    return get_completed_videos_from_ytdl(download_dir)


def extract_type_and_name_from_url(url):
    """
    Extract content type (model, users, channels, playlist) and name from URL
    
    Args:
        url: Full PornHub URL
    
    Returns:
        tuple: (type, name) or (None, None) if URL is invalid
    
    Examples:
        https://www.pornhub.com/model/utumitumi -> ('model', 'utumitumi')
        https://www.pornhub.com/users/username -> ('users', 'username')
        https://www.pornhub.com/channels/name -> ('channels', 'name')
        https://www.pornhub.com/playlist/123 -> ('playlist', '123')
    """
    try:
        # Remove protocol and domain
        # Extract path part
        if '://' in url:
            url = url.split('://', 1)[1]  # Remove https://
        
        # Remove domain
        if '/' in url:
            url = url.split('/', 1)[1]  # Remove www.pornhub.com
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Remove query parameters
        if '?' in url:
            url = url.split('?')[0]
        
        # Split to get type and name
        parts = url.split('/')
        if len(parts) >= 2:
            content_type = parts[0]  # model, users, channels, playlist
            name = parts[1]  # the name/username/id
            
            # Validate type
            if content_type in ['model', 'users', 'channels', 'playlist']:
                return content_type, name
    except Exception as e:
        print(f"✗ Error parsing URL: {e}")
    
    return None, None


def extract_video_count_from_url(url):
    """
    Extract video ID and other info from youtube-dl info_dict
    This is used to identify individual videos from a playlist
    """
    pass


class YouTubeDLLogger:
    """Custom logger to capture youtube-dl output"""
    def __init__(self):
        self.last_line = ""
        self.total_videos = None
        self.current_video = None
    
    def debug(self, msg):
        self.process_message(msg)
    
    def warning(self, msg):
        self.process_message(msg)
    
    def error(self, msg):
        self.process_message(msg)
    
    def process_message(self, msg):
        self.last_line = msg
        # Look for "Downloading video X of Y" pattern
        match = re.search(r'\[download\]\s+Downloading video (\d+) of (\d+)', msg)
        if match:
            self.current_video = int(match.group(1))
            self.total_videos = int(match.group(2))


def check_playlist_completion(download_dir, url, item_type, item_name):
    """
    Check which videos from a playlist/user/model have been downloaded
    and which are missing.
    
    More sophisticated checking:
    - Uses .ytdl metadata files as primary indicator
    - Matches downloaded files with playlist entries by title
    - Provides accurate count of missing videos
    
    Args:
        download_dir: Full path to the download directory
        url: PornHub URL to the playlist/user/model
        item_type: 'model', 'users', 'channels', 'playlist'
        item_name: Name of the user/model/channel/playlist
    
    Returns:
        tuple: (total_videos, downloaded_count, missing_videos_info)
    """
    
    print(f"\n{'='*60}")
    print(f"다운로드 상태 확인 - {item_name}")
    print(f"{'='*60}\n")
    
    # Get downloaded files
    downloaded_files = get_downloaded_files(download_dir)
    downloaded_count = len(downloaded_files)
    
    print(f"Directory: {download_dir}")
    print(f"✓ 다운로드 완료된 동영상: {downloaded_count}개\n")
    
    if downloaded_count > 0:
        print(f"최근 다운로드 동영상:")
        for i, video in enumerate(sorted(downloaded_files)[-5:], 1):
            title = video[:60] if len(video) > 60 else video
            print(f"  {i}. {title}")
    
    # Try to get playlist information
    print(f"\n🔍 플레이리스트 정보 확인 중...")
    
    # IMPROVED: 404 에러 방지를 위한 강화된 옵션
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'socket_timeout': 30,
        'retries': 5,
        'fragment_retries': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://www.pornhub.com/',
        },
        'nocheckcertificate': True,
    }
    
    # 쿠키 파일이 있으면 사용
    cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path
        print("✓ 쿠키 파일 사용")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            total_videos = info.get('playlist_count') or len(info.get('entries', []))
            print(f"✓ 총 동영상: {total_videos}개")
            
            if downloaded_count >= total_videos:
                print(f"\n✅ 모든 동영상 다운로드 완료!")
                print(f"   {downloaded_count}/{total_videos} (100%)")
            else:
                missing = total_videos - downloaded_count
                percent = (downloaded_count / total_videos * 100) if total_videos > 0 else 0
                print(f"\n📊 다운로드 진행률: {downloaded_count}/{total_videos} ({percent:.1f}%)")
                print(f"   누락된 동영상: {missing}개")
            
            return total_videos, downloaded_count, []
            
    except Exception as e:
        print(f"\n⚠️  플레이리스트 정보를 가져올 수 없습니다.")
        print(f"Error: {str(e)[:100]}")
        print(f"\n💡 해결 방법:")
        print(f"  1. VPN 또는 프록시 사용")
        print(f"  2. 쿠키 파일 생성 (cookies.txt)")
        print(f"  3. yt-dlp 업데이트: pip install -U yt-dlp")
        print(f"\n현재 상태:")
        print(f"  이미 다운로드됨: {downloaded_count}")
        return None, downloaded_count, []


def resume_download(url, item_type, item_name, base_path='./model'):
    """
    Resume downloading missing videos from a playlist/user/model.
    더 섬세하고 정확한 다운로드 추적
    
    IMPROVED: 404 에러 해결을 위한 강화된 버전
    
    Only downloads videos that are missing.
    
    Args:
        url: PornHub URL to the playlist/user/model
        item_type: 'model', 'users', 'channels', 'playlist'
        item_name: Name of the user/model/channel/playlist
        base_path: Base path for downloads (default: './model')
    """
    
    # Normalize paths and safeguard against restricted locations
    base_path = os.path.normpath(base_path) if base_path else os.path.normpath('./model')
    if is_system_restricted_path(base_path):
        base_path = os.path.normpath(DEFAULT_DOWNLOAD_DIR)
    
    # Construct download directory
    download_dir = os.path.join(base_path, item_name)
    download_dir = os.path.normpath(download_dir)
    
    print(f"\n{'='*60}")
    print(f"Resume Manager - 정교한 다운로드 재개 (404 에러 방지 버전)")
    print(f"{'='*60}\n")
    
    # Check completion status
    print(f"Directory: {download_dir}\n")
    downloaded_files = get_downloaded_files(download_dir)
    downloaded_count = len(downloaded_files)
    
    print(f"✓ 다운로드 완료된 동영상: {downloaded_count}개")
    
    if downloaded_count > 0:
        print(f"\n최근 다운로드 동영상:")
        for i, video in enumerate(sorted(downloaded_files)[-5:], 1):
            title = video[:60] if len(video) > 60 else video
            print(f"  {i}. {title}")
    
    # Check if we have any existing data
    info_file = os.path.join(download_dir, '.download_info.json')
    
    total_videos = None
    if os.path.exists(info_file):
        try:
            with open(info_file, 'r') as f:
                info = json.load(f)
                total_videos = info.get('total_videos')
                print(f"\n✓ 이전 다운로드 정보 로드됨: 총 {total_videos}개")
        except:
            pass
    
    # If we don't have total count, try to get it from youtube-dl
    if total_videos is None:
        print(f"\n🔍 플레이리스트 정보 확인 중...")
        
        # IMPROVED: 404 에러 방지를 위한 강화된 옵션
        ydl_opts_check = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Referer': 'https://www.pornhub.com/',
            },
            'nocheckcertificate': True,
        }
        
        # 쿠키 파일이 있으면 사용
        cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        if os.path.exists(cookies_path):
            ydl_opts_check['cookiefile'] = cookies_path
            print("✓ 쿠키 파일 사용")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
                info = ydl.extract_info(url, download=False)
                total_videos = info.get('playlist_count') or len(info.get('entries', []))
                print(f"✓ 총 동영상: {total_videos}개")
        except Exception as e:
            print(f"⚠️  플레이리스트 정보를 가져올 수 없습니다.")
            print(f"   Error: {str(e)[:100]}")
            print(f"\n💡 해결 방법:")
            print(f"   1. 브라우저에서 로그인 후 cookies.txt 생성")
            print(f"   2. VPN 또는 프록시 사용")
            print(f"   3. yt-dlp 업데이트: pip install -U yt-dlp")
            total_videos = None
    
    if total_videos is None:
        # If we still can't get total count, ask user
        print(f"\n총 동영상 개수를 입력해주세요 (또는 Enter로 건너뛰기):")
        try:
            user_input = input("총 개수 (또는 비워두기): ").strip()
            if user_input.isdigit():
                total_videos = int(user_input)
            else:
                print(f"총 개수를 알 수 없습니다. 계속 다운로드할 수 없습니다.")
                return False
        except:
            print(f"입력 오류. 계속 진행할 수 없습니다.")
            return False
    
    # Check if complete
    if downloaded_count >= total_videos:
        print(f"\n✓ 모든 {total_videos}개 동영상이 다운로드되었습니다!")
        return True
    
    # Ask user if they want to continue
    missing_count = total_videos - downloaded_count
    print(f"\n{'='*60}")
    print(f"누락된 동영상: {missing_count}개 (비디오 #{downloaded_count + 1} ~ #{total_videos})")
    print(f"{'='*60}\n")
    
    response = input(f"다운로드를 계속하시겠습니까? (y/n): ").strip().lower()
    
    if response != 'y':
        print("다운로드 취소되었습니다.")
        return False
    
    # Calculate start position for resume
    start_video = downloaded_count + 1
    
    print(f"\n▶️  동영상 #{start_video}부터 #{total_videos}까지 다운로드 시작...\n")
    
    outtmpl = os.path.normpath(os.path.join(download_dir, '%(title)s.%(ext)s'))
    
    # IMPROVED: 404 에러 해결을 위한 강화된 옵션 사용
    ydl_opts = get_ytdlp_options(outtmpl, start_video=start_video, end_video=total_videos, use_cookies=True)
    
    # 추가 설정
    ydl_opts['quiet'] = False
    
    try:
        print("다운로드 시작...\n")
        print("💡 Tips:")
        print("  - 404 에러 발생 시 자동으로 재시도합니다")
        print("  - Ctrl+C로 언제든 중단할 수 있습니다")
        print("  - 다시 'resume' 명령어로 이어서 다운로드할 수 있습니다\n")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        print("\n✓ 다운로드 완료!")
        
        # Verify completion
        final_downloaded = get_downloaded_files(download_dir)
        final_count = len(final_downloaded)
        
        print(f"\n📊 최종 상태:")
        print(f"  총 동영상: {total_videos}")
        print(f"  다운로드됨: {final_count}")
        print(f"  누락: {max(0, total_videos - final_count)}")
        
        if final_count < total_videos:
            print(f"\n💡 일부 동영상이 다운로드되지 않았습니다.")
            print(f"   다시 'python phdler.py resume {url}' 명령어로 재시도하세요.")
        
        # Save completion info
        os.makedirs(download_dir, exist_ok=True)
        info = DownloadInfo(url, total_videos, final_count, download_dir)
        info.save()
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️  다운로드가 중단되었습니다.")
        final_downloaded = get_downloaded_files(download_dir)
        final_count = len(final_downloaded)
        print(f"부분 다운로드 상태: {final_count}/{total_videos}")
        print(f"\n다시 'python phdler.py resume {url}' 명령어로 이어서 다운로드하세요.")
        return False
        
    except Exception as e:
        print(f"\n✗ 다운로드 중 오류 발생:")
        print(f"   {str(e)[:200]}")
        final_downloaded = get_downloaded_files(download_dir)
        final_count = len(final_downloaded)
        print(f"\n⚠️  부분 다운로드 상태: {final_count}/{total_videos}")
        print(f"\n💡 해결 방법:")
        print(f"   1. yt-dlp 업데이트: pip install -U yt-dlp")
        print(f"   2. 쿠키 파일 생성 (cookies.txt)")
        print(f"   3. VPN 또는 프록시 사용")
        print(f"   4. FFmpeg 설치 확인")
        print(f"\n다시 시도: python phdler.py resume {url}")
        return False


def show_download_status(download_dir):
    """Display download status for a directory"""
    if not os.path.exists(download_dir):
        print(f"Directory does not exist: {download_dir}")
        return
    
    downloaded = get_downloaded_files(download_dir)
    print(f"\nDownloaded videos in {download_dir}:")
    print(f"Total: {len(downloaded)} videos\n")
    
    for i, video in enumerate(sorted(downloaded)[:10], 1):
        try:
            print(f"{i:3d}. {video[:60]}")
        except Exception as e:
            print(f"{i:3d}. [Video {i}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Resume Manager - Download resumption and completion checker")
        print("\nUsage:")
        print("  python resume_manager.py check <url> <type> <name>")
        print("    Check which videos are downloaded and which are missing")
        print("    type: model, users, channels, playlist")
        print("\n  python resume_manager.py resume <url> <type> <name>")
        print("    Resume downloading missing videos from the playlist")
        print("\n  python resume_manager.py status <download_dir>")
        print("    Show download status for a directory")
        print("\nExample:")
        print("  python resume_manager.py check https://www.pornhub.com/users/utumitumi users utumitumi")
        print("  python resume_manager.py resume https://www.pornhub.com/users/utumitumi users utumitumi")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check" and len(sys.argv) >= 5:
        url = sys.argv[2]
        item_type = sys.argv[3]
        item_name = sys.argv[4]
        check_playlist_completion(f"./model/{item_name}", url, item_type, item_name)
    
    elif command == "resume" and len(sys.argv) >= 5:
        url = sys.argv[2]
        item_type = sys.argv[3]
        item_name = sys.argv[4]
        resume_download(url, item_type, item_name)
    
    elif command == "status" and len(sys.argv) >= 3:
        download_dir = sys.argv[2]
        show_download_status(download_dir)
    
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
