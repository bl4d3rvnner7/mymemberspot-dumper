#!/usr/bin/env python3
"""
mymemberspot.de Complete Course Dumper
Uses the chapter API endpoint that returns all posts with video URLs
"""

import requests
import json
import os
import uuid
import time
import subprocess
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import shutil
from tqdm import tqdm
import sys

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def color_print(text, color=Colors.RESET, bold=False):
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")

def print_banner():
    """Print a clean ASCII art banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ███╗   ███╗██╗   ██╗███╗   ███╗███████╗██████╗ ███████╗██████╗ ██████╗ ████████╗
    ████╗ ████║╚██╗ ██╔╝████╗ ████║██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝
    ██╔████╔██║ ╚████╔╝ ██╔████╔██║█████╗  ██████╔╝███████╗██████╔╝██████╔╝   ██║   
    ██║╚██╔╝██║  ╚██╔╝  ██║╚██╔╝██║██╔══╝  ██╔══██╗╚════██║██╔═══╝ ██╔══██╗   ██║   
    ██║ ╚═╝ ██║   ██║   ██║ ╚═╝ ██║███████╗██║  ██║███████║██║     ██║  ██║   ██║   
    ╚═╝     ╚═╝   ╚═╝   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝   

                    ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗                    
                    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗                   
                    ██║  ██║██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝                   
                    ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗                   
                    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║                   
                    ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝                   

        {Colors.RESET}
        {Colors.DIM}┌─────────────────────────────────────────────────────────────────────────────┐
        │                                                                             │
        │  Author  : bl4d3rvnner7                                                     │
        │  GitHub  : https://github.com/bl4d3rvnner7/mymemberspot-dumper              │
        │  License : MIT                                                              │
        │                                                                             │
        └─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}
"""
    print(banner)


def sanitize_name(name):
    """Replace unsafe characters in filenames and folder names."""
    replacements = {
        ':': '：',  # Colon
        '/': '／',  # Forward slash
        '\\': '＼',  # Backslash
        '?': '？',  # Question mark
        '*': '＊',  # Asterisk
        '"': '＂',  # Double quote
        '<': '＜',  # Less than
        '>': '＞',  # Greater than
        '|': '｜',  # Vertical bar (pipe)
        '!': ''
    }
    
    for unsafe, safe in replacements.items():
        name = name.replace(unsafe, safe)
    
    # Trim spaces and dots to prevent Windows issues (e.g., "file .txt")
    return name.strip().rstrip('.')

class VimeoDownloader:
    def __init__(self, url, referer, debug):
        self.url = url
        self.referer = referer
        self.debug = debug
        self.video_id = self.extract_id()

    def extract_id(self):
        match = re.search(r'vimeo\.com/(?:video/)?(\d+)', self.url)
        if not match:
            raise ValueError("Invalid Vimeo URL")
        return match.group(1)

    def get_player_url(self):
        try:
            oembed_url = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{self.video_id}?share=copy&speed=true"
            origin = self.referer.rstrip('/')
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": self.referer,
                "Origin": origin
            }
            r = requests.get(oembed_url, headers=headers)
            r.raise_for_status()
            data = r.json()
            if self.debug:
                print(data)
            iframe = data["html"]
            player_url = re.search(r'src="([^"]+)"', iframe).group(1)
            return player_url
        except Exception as e:
            if self.debug:
                print(f"[Vimeo ERROR] {str(e)}")
            return None


    def download(self, cmd):
        player_url = self.get_player_url()
        cmd[-1] = player_url
        cmd += [
            "--add-header", f"Referer: {self.referer}",
            "--add-header", f"Origin: {self.referer.rstrip('/')}"
        ]
        if self.debug:
            print(cmd)
        return subprocess.run(cmd)



class ProgressTracker:
    def __init__(self):
        self.current_course = None
        self.current_chapter = None
        self.current_lesson = None
        self.pbar = None
        self.lesson_pbar = None
    
    def update(self, **kwargs):
        if self.pbar:
            if 'course' in kwargs:
                self.current_course = kwargs['course']
            if 'chapter' in kwargs:
                self.current_chapter = kwargs['chapter']
            if 'lesson' in kwargs:
                self.current_lesson = kwargs['lesson']
            
            # Update progress bar description
            desc = f"{self.current_course or 'N/A'}"
            if self.current_chapter:
                desc += f" | {self.current_chapter}"
            if self.current_lesson:
                desc += f" | {self.current_lesson}"
            self.pbar.set_description(desc[:80])  # Limit length

progress = ProgressTracker()

class MemberspotDumper:
    def __init__(self, email: str = None, password: str = None, config_path: str = "config.json"):
        # Load config
        self.config = self.load_config(config_path)
        
        self.api_base = self.config.get("api_base", "https://client-api.memberspot.de")
        self.firebase_api_key = self.config.get("firebase_api_key")
        self.tenant_id = self.config.get("tenant_id")
        self.school_id = self.config.get("school_id")
        self.base_url = self.config.get("base_url")
        self.debug = self.config.get("debug")
        
        # Chapter limit settings
        self.chapter_limit = self.config.get("chapter_limit", 50)
        self.download_until_limit = self.config.get("download_until_limit", True)
        
        # Retry settings
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 5)
        
        # Validate required config
        if not all([self.firebase_api_key, self.tenant_id, self.school_id, self.base_url]):
            color_print("[-] Missing required config values! Check config.json", Colors.RED)
            raise ValueError("Missing required configuration")
        
        self.session = requests.Session()
        self.id_token = None
        
        # Headers for API calls
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'app-version': self.config.get("app_version", "2026-04-02-2110/server-client-frontend"),
            'app': self.config.get("app", "client"),
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'DNT': '1',
            'Sec-GPC': '1',
        }
        
        if email and password:
            self.login(email, password)
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "api_base": "https://client-api.memberspot.de",
            "firebase_api_key": "AIzaSyBsOSvyKi9LaUCQQSdFR3e3G_HEJanqDZ0",
            "tenant_id": "s-V57dJFhCLVpklJx7-w7gxj",
            "school_id": "V57dJFhCLVpklJx7Yn8e",
            "base_url": "https://machinsalesacademy.mymemberspot.de",
            "app_version": "2026-04-02-2110/server-client-frontend",
            "app": "client",
            "ytdlp_threads": 4,
            "download_delay": 0.3,
            "chapter_delay": 1,
            "course_delay": 2,
            "chapter_limit": 50,
            "download_until_limit": True,
            "max_retries": 3,
            "retry_delay": 5,
            "ytdlp_retries": 10,
            "ytdlp_fragment_retries": 10
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
                    color_print(f"[+] Loaded config from {config_path}", Colors.GREEN)
            except Exception as e:
                color_print(f"[-] Error loading config: {e}", Colors.RED)
                color_print(f"[*] Using default config", Colors.YELLOW)
        else:
            # Create default config file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            color_print(f"[+] Created default config file: {config_path}", Colors.GREEN)
            color_print(f"[*] Please edit {config_path} if needed", Colors.YELLOW)
        
        return default_config
    
    def login(self, email: str, password: str):
        """Login and get token"""
        color_print(f"[*] Logging in as {email}...", Colors.CYAN)
        
        login_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        params = {"key": self.firebase_api_key}
        
        payload = {
            "returnSecureToken": True,
            "email": email,
            "password": password,
            "clientType": "CLIENT_TYPE_WEB",
            "tenantId": self.tenant_id
        }
        
        response = requests.post(login_url, params=params, json=payload)
        
        if response.status_code != 200:
            color_print(f"[-] Login failed: {response.text}", Colors.RED)
            return False
        
        data = response.json()
        self.id_token = data.get('idToken')
        self.user_id = data.get('localId')
        self.api_headers['authorization'] = self.id_token
        
        color_print(f"[+] Login successful!", Colors.GREEN, bold=True)
        return True
    
    def refresh_token_if_needed(self):
        """Refresh the authentication token if needed"""
        # For now, we'll just re-login if we get 403 errors
        # This method can be enhanced to use refresh tokens
        pass
    
    def get_courses(self) -> List[Dict]:
        """Get all courses from user info"""
        url = f"{self.api_base}/school-users/user-v2/{self.school_id}"
        response = requests.get(url, headers=self.api_headers)
        
        if response.status_code != 200:
            color_print(f"[-] Failed to get user info: {response.status_code}", Colors.RED)
            return []
        
        user_info = response.json()
        color_print(f"[+] User: {user_info.get('firstname')} {user_info.get('name')}", Colors.GREEN)
        
        courses = []
        for course_ref in user_info.get('hasCourses', []):
            course_id = course_ref.get('courseId')
            if course_id:
                course_info = self.get_course_info(course_id)
                if course_info:
                    courses.append(course_info)
        
        return courses
    
    def get_course_info(self, course_id: str) -> Dict:
        """Get course details including all chapters"""
        url = f"{self.api_base}/user-course/course/{self.school_id}/{course_id}"
        response = requests.get(url, headers=self.api_headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_chapter_details(self, course_id: str, chapter_id: str) -> Dict:
        """Get chapter details with all posts (videos, files, etc.)"""
        url = f"{self.api_base}/user-course/chapter/{self.school_id}/{course_id}/{chapter_id}"
        response = requests.get(url, headers=self.api_headers)
        
        if response.status_code == 200:
            return response.json()
        color_print(f"    [!] Failed to get chapter {chapter_id}: {response.status_code}", Colors.RED)
        return None
    
    def download_chapter_thumbnail(self, chapter_info: Dict, chapter_dir: Path, chapter_idx: int):
        """Download chapter thumbnail image"""
        thumbnail_url = chapter_info.get('thumbnailUrl')
        
        if not thumbnail_url:
            return
        
        # Determine file extension
        if thumbnail_url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            base_url = thumbnail_url.split('?')[0]
            ext = base_url.split('.')[-1]
        else:
            ext = 'jpg'
        
        thumbnail_path = chapter_dir / f"chapter_thumbnail.{ext}"
        
        # Check if thumbnail already exists
        if thumbnail_path.exists() and thumbnail_path.stat().st_size > 1000:
            return
        
        try:
            file_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': self.base_url,
            }
            
            response = requests.get(thumbnail_url, headers=file_headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(thumbnail_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
                    return True
        except Exception:
            pass
        
        return False

    def download_course_thumbnail(self, course_info: Dict, course_dir: Path):
        """Download course thumbnail image"""
        # Try multiple possible field names for thumbnail
        thumbnail_url = course_info.get('thumbnailUrl') or course_info.get('image')
        
        if not thumbnail_url:
            color_print(f"  [!] No thumbnail URL found for course", Colors.YELLOW)
            return
    
        # Determine file extension from URL or default to jpg
        if thumbnail_url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            # Extract extension from URL, handling query parameters
            base_url = thumbnail_url.split('?')[0]
            ext = base_url.split('.')[-1]
        else:
            ext = 'jpg'
        
        thumbnail_path = course_dir / f"course_thumbnail.{ext}"
        
        # Check if thumbnail already exists
        if thumbnail_path.exists() and thumbnail_path.stat().st_size > 1000:
            color_print(f"  [✓] Thumbnail already exists", Colors.GREEN)
            return True
        
        try:
            # Use minimal headers for thumbnail download (same as file downloads)
            file_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': self.base_url,
            }
            
            response = requests.get(thumbnail_url, headers=file_headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                # Get total size for progress bar
                total_size = int(response.headers.get('content-length', 0))
                
                with open(thumbnail_path, 'wb') as f:
                    if total_size > 0:
                        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"  Downloading thumbnail", leave=False) as pbar:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                    else:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                
                if thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
                    size_kb = thumbnail_path.stat().st_size / 1024
                    color_print(f"  [+] Downloaded course thumbnail ({size_kb:.1f} KB)", Colors.GREEN)
                    return True
                else:
                    color_print(f"  [!] Downloaded thumbnail is empty", Colors.YELLOW)
                    if thumbnail_path.exists():
                        thumbnail_path.unlink()
                    return False
            else:
                color_print(f"  [!] Failed to download thumbnail: HTTP {response.status_code}", Colors.YELLOW)
                return False
        except Exception as e:
            color_print(f"  [!] Error downloading thumbnail: {e}", Colors.YELLOW)
            return False
    
    def create_credits_file(self, course_dir: Path):
        """Create credits.txt file in course directory"""
        credits_content = f"""This course was downloaded using the mymemberspot.de Course Dumper tool.

Downloader Information:
- Tool: mymemberspot-dumper
- Author: bl4d3rvnner7
- GitHub Repository: https://github.com/bl4d3rvnner7/mymemberspot-dumper
- Download Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This tool is for personal use only. Please respect copyright laws and the terms of service of the platform.

If you found this tool useful, please consider starring the repository on GitHub!
"""
        
        credits_path = course_dir / "credits.txt"
        with open(credits_path, 'w', encoding='utf-8') as f:
            f.write(credits_content)
        color_print(f"  [+] Created credits.txt", Colors.GREEN)
    
    def download_video_with_retry(self, video_info: Dict, output_path: Path, lesson_num: int, lesson_name: str):
        """Download video with retry mechanism and stealth yt-dlp command"""
        for attempt in range(self.max_retries):
            if attempt > 0:
                color_print(f"        [*] Video retry {attempt}/{self.max_retries}...", Colors.YELLOW)
                time.sleep(self.retry_delay)
                # Refresh token on retry
                if attempt == 2:  # On second retry, try to refresh
                    color_print(f"        [*] Attempting to refresh authentication...", Colors.YELLOW)
                    # Token refresh would go here if implemented
            
            if self.download_video(video_info, output_path, lesson_num, lesson_name):
                return True
        
        color_print(f"        [-] Failed after {self.max_retries} attempts", Colors.RED)
        return False

    def sanitize_filename_for_fs(self, name: str) -> str:
        """Extra aggressive sanitization for filesystem paths"""
        if isinstance(name, Path):
            name = str(name)

        name = sanitize_name(name)
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        if len(name) > 200:
            name = name[:200]
        return name.strip()

    def debug_print(self, msg, color=Colors.DIM):
        if self.debug:
            color_print(msg, color)


    def download_external_video(self, url: str, output_path: Path, lesson_name: str):
        ytdlp = shutil.which('yt-dlp')
        if not ytdlp:
            color_print(f"        [!] yt-dlp not found", Colors.RED)
            return False

        if "vimeo.com" in url:
            color_print(f"        [*] External video (Vimeo)", Colors.CYAN)
            downloader = VimeoDownloader(
                url=url,
                referer=self.config.get("base_url", ""),
                debug=self.debug
            )

            temp_output = output_path.parent / f".tmp_{uuid.uuid4().hex}.mp4"

            cmd = [
                ytdlp,
                '-N', str(self.config.get("ytdlp_threads", 4)),
                '-o', str(temp_output),
                '--retries', str(self.config.get("ytdlp_retries", 10)),
                '--fragment-retries', str(self.config.get("ytdlp_fragment_retries", 10)),
                '--skip-unavailable-fragments',
                '--concurrent-fragments', '5',
                '--geo-bypass',
                '--quiet',
                '--no-progress',
                '--hls-use-mpegts',
                url
            ]

            start_time = time.time()

            try:
                result = downloader.download(cmd)
                elapsed = time.time() - start_time

                if result.returncode == 0 and temp_output.exists() and temp_output.stat().st_size > 0:
                    try:
                        shutil.move(str(temp_output), str(output_path))

                        size_mb = output_path.stat().st_size / (1024 * 1024)
                        color_print(f"        [+] Done: {output_path.name} ({size_mb:.2f} MB) in {elapsed:.1f}s", Colors.GREEN)
                        return True

                    except Exception as e:
                        color_print(f"        [!] Move failed: {e}", Colors.RED)
                        return False
                else:
                    color_print(f"        [!] External download failed", Colors.RED)
                    return False

            finally:
                if temp_output.exists():
                    try:
                        temp_output.unlink()
                    except:
                        pass

        color_print(f"        [*] External video (generic)", Colors.CYAN)

        cmd = [
            ytdlp,
            '-o', str(output_path),
            url
        ]

        result = subprocess.run(cmd)

        return result.returncode == 0 and output_path.exists()
        
    def download_video(self, video_info: Dict, output_path: Path, lesson_num: int, lesson_name: str):
        """Download video using HLS with safe temp file handling"""

        # STEP 1: Get HLS URL
        self.debug_print(f"        [DEBUG] Getting HLS URL...", Colors.DIM)
        hls_url = video_info.get('hlsSrc')
        if not hls_url:
            self.debug_print(f"        [!] No hlsSrc found", Colors.RED)
            return False

        # STEP 2: Ensure directory exists
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.debug_print(f"        [!] Directory creation failed: {e}", Colors.RED)
            return False

        # STEP 3: Skip if already downloaded
        if output_path.exists():
            size = output_path.stat().st_size
            if size > 1024 * 1024:
                size_mb = size / (1024 * 1024)
                color_print(f"        [✓] Already exists: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                return True
            else:
                output_path.unlink()

        # STEP 4: yt-dlp check
        ytdlp = shutil.which('yt-dlp')
        if not ytdlp:
            self.debug_print(f"        [!] yt-dlp not found", Colors.RED)
            return False

        # STEP 5: Temp file (SAFE!)
        temp_output = output_path.parent / f".tmp_{uuid.uuid4().hex}.mp4"

        # STEP 6: Build command
        cmd = [
            ytdlp,
            '-N', str(self.config.get("ytdlp_threads", 4)),
            '-o', str(temp_output),
            '--retries', str(self.config.get("ytdlp_retries", 10)),
            '--fragment-retries', str(self.config.get("ytdlp_fragment_retries", 10)),
            '--skip-unavailable-fragments',
            '--concurrent-fragments', '5',
            '--geo-bypass',
            '--quiet',
            '--no-progress',
            '--hls-use-mpegts',
            hls_url
        ]

        # STEP 7: Run download
        color_print(f"        [*] Downloading...", Colors.CYAN)
        start_time = time.time()

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            elapsed = time.time() - start_time

            if result.returncode == 0:
                if temp_output.exists() and temp_output.stat().st_size > 0:
                    try:
                        shutil.move(str(temp_output), str(output_path))

                        size = output_path.stat().st_size
                        size_mb = size / (1024 * 1024)

                        color_print(f"        [+] Done: {output_path.name} ({size_mb:.2f} MB) in {elapsed:.1f}s", Colors.GREEN)
                        return True

                    except Exception as e:
                        self.debug_print(f"        [!] Move failed: {e}", Colors.RED)
                        return False
                else:
                    self.debug_print(f"        [!] Temp file missing/empty", Colors.RED)

            else:
                self.debug_print(f"        [!] yt-dlp failed ({result.returncode})", Colors.RED)

                if result.stderr:
                    for line in result.stderr.splitlines()[:10]:
                        if line.strip():
                            self.debug_print(f"        {line}", Colors.YELLOW)

            return False

        except subprocess.TimeoutExpired:
            self.debug_print(f"        [!] Timeout after 2h", Colors.RED)
            return False

        except Exception as e:
            self.debug_print(f"        [!] Exception: {e}", Colors.RED)
            return False

        finally:
            # STEP 8: Cleanup temp file
            if temp_output.exists():
                try:
                    temp_output.unlink()
                except:
                    pass
    def download_file_with_retry(self, url: str, output_path: Path):
        """Download file with retry - using minimal headers for CDN compatibility"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    time.sleep(self.retry_delay)
                
                file_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(url, headers=file_headers, stream=True, timeout=30)
                
                if response.status_code == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(output_path, 'wb') as f:
                        if total_size > 0:
                            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"            Downloading {output_path.name}", leave=False) as pbar:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                        else:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    
                    if output_path.exists() and output_path.stat().st_size > 0:
                        size_mb = output_path.stat().st_size / (1024 * 1024)
                        color_print(f"        [+] Downloaded: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                        return True
                    else:
                        color_print(f"        [-] Downloaded file is empty", Colors.RED)
                        if output_path.exists():
                            output_path.unlink()
                        return False
                        
                elif response.status_code == 403:
                    color_print(f"        [!] HTTP 403 for {output_path.name} (attempt {attempt + 1}/{self.max_retries})", Colors.YELLOW)
                    if attempt == self.max_retries - 1:
                        color_print(f"        [*] Trying with no custom headers...", Colors.CYAN)
                        response = requests.get(url, stream=True, timeout=30)
                        if response.status_code == 200:
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(output_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            if output_path.exists() and output_path.stat().st_size > 0:
                                size_mb = output_path.stat().st_size / (1024 * 1024)
                                color_print(f"        [+] Downloaded with no headers: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                                return True
                    continue
                    
                else:
                    if attempt < self.max_retries - 1:
                        color_print(f"        [*] Retry {attempt + 1}/{self.max_retries} for {output_path.name} (HTTP {response.status_code})", Colors.YELLOW)
                    else:
                        color_print(f"        [-] Failed to download {output_path.name}: HTTP {response.status_code}", Colors.RED)
                            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    color_print(f"        [*] Retry {attempt + 1}/{self.max_retries} for {output_path.name}: {str(e)[:50]}", Colors.YELLOW)
                else:
                    color_print(f"        [-] Download failed: {e}", Colors.RED)
        
        return False

    def format_time(self, seconds: int) -> str:
        """Format time"""
        if not seconds:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"
    
    def is_downloadable_file(self, url: str, content_type: str = None, file_size: int = 0) -> bool:
        """Check if the URL points to a downloadable file vs a web page"""
        # Check content type from API
        if content_type == 'link':
            return False
        
        # Check file size - 0 often indicates a link
        if file_size == 0:
            return False
        
        # Check URL patterns for known product pages
        if '/produkt/' in url or '/product/' in url:
            return False
        
        # Check for common file extensions
        downloadable_extensions = ('.pdf', '.zip', '.rar', '.7z', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4')
        if any(url.lower().endswith(ext) for ext in downloadable_extensions):
            return True
        
        # Check if URL has a token and seems to be from file storage
        if 'files.mspotcdn.de' in url and 'alt=media' in url and 'token=' in url:
            return True
        
        # Default to treating as link if uncertain
        return False


    def clean_html(self, html_content: str) -> str:
        """Remove HTML tags from content and return plain text"""
        if not html_content:
            return ""
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', html_content)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean)
        # Remove HTML entities
        clean = re.sub(r'&[a-z]+;', ' ', clean, flags=re.IGNORECASE)
        # Trim and clean up
        clean = clean.strip()
        # Fix multiple spaces
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean
    
    def create_course_description_file(self, course_info: Dict, course_dir: Path):
        """Create a formatted description file for the course"""
        name = course_info.get('name', 'No Title')
        description = course_info.get('description', 'No description')
        content = course_info.get('content', '')
        
        # Clean HTML content
        clean_content = self.clean_html(content) if content else ""
        
        description_path = course_dir / "Description.txt"
        
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*70}\n")
            f.write(f"{name}\n")
            f.write(f"{'='*70}\n\n")
            
            f.write(f"DESCRIPTION:\n")
            f.write(f"{'-'*40}\n")
            f.write(f"{description}\n\n")
            
            if clean_content:
                f.write(f"CONTENT:\n")
                f.write(f"{'-'*40}\n")
                f.write(f"{clean_content}\n\n")
            
            # Add course metadata
            f.write(f"COURSE INFORMATION:\n")
            f.write(f"{'-'*40}\n")
            f.write(f"ID: {course_info.get('id', 'N/A')}\n")
            f.write(f"Priority: {course_info.get('priority', 'N/A')}\n")
            f.write(f"State: {course_info.get('state', 'N/A')}\n")
            if course_info.get('thumbnailUrl'):
                f.write(f"Thumbnail URL: {course_info.get('thumbnailUrl')}\n")
            
            f.write(f"\n{'='*70}\n")
        
        color_print(f"  [+] Created course description file", Colors.GREEN)

    def create_chapter_description_file(self, chapter_info: Dict, chapter_dir: Path, chapter_idx: int):
        """Create a formatted description file for the chapter"""
        name_raw = chapter_info.get('name', f'Chapter_{chapter_idx}')
        # Clean the name from "Modul X | " pattern if present
        name = re.sub(r'^Modul\s+\d+\s*\|\s*', '', name_raw)
        description = chapter_info.get('description', 'No description')
        
        description_path = chapter_dir / "Description.txt"
        
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*70}\n")
            f.write(f"{name}\n")
            f.write(f"{'='*70}\n\n")
            
            f.write(f"DESCRIPTION:\n")
            f.write(f"{'-'*40}\n")
            f.write(f"{description}\n\n")
            
            # Add chapter metadata
            f.write(f"CHAPTER INFORMATION:\n")
            f.write(f"{'-'*40}\n")
            f.write(f"ID: {chapter_info.get('id', 'N/A')}\n")
            f.write(f"Priority: {chapter_info.get('priority', 'N/A')}\n")
            f.write(f"State: {chapter_info.get('state', 'N/A')}\n")
            f.write(f"Number of Lessons: {chapter_info.get('numberOfActivePosts', 0)}\n")
            f.write(f"Total Video Time: {self.format_time(chapter_info.get('videoTime', 0))}\n")
            
            if chapter_info.get('thumbnailUrl'):
                f.write(f"Thumbnail URL: {chapter_info.get('thumbnailUrl')}\n")
            
            f.write(f"\n{'='*70}\n")
        
        return True

    def dump_chapter(self, course_id: str, chapter_info: Dict, course_dir: Path, chapter_idx: int):
        """Dump a chapter using the chapter details API"""
        # Format chapter name: "1. Modul 1 - Einführung und Mindset"
        chapter_name_raw = chapter_info.get('name', f'Chapter_{chapter_idx}')
        # Remove the "Modul X | " pattern and reformat
        chapter_name_clean = re.sub(r'^Modul\s+\d+\s*\|\s*', '', chapter_name_raw)
        chapter_folder = f"{chapter_idx}. {chapter_name_clean}"
        chapter_folder = sanitize_name(chapter_folder)
        chapter_dir = course_dir / chapter_folder
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        # Get full chapter details with all posts
        chapter_details = self.get_chapter_details(course_id, chapter_info['id'])

        if not chapter_details:
            color_print(f"    [!] Could not get chapter details", Colors.RED)
            return

        # Download chapter thumbnail
        self.download_chapter_thumbnail(chapter_info, chapter_dir, chapter_idx)

        # Create chapter description file
        self.create_chapter_description_file(chapter_info, chapter_dir, chapter_idx)

        # Get active posts
        active_posts = chapter_details.get('activePosts', [])
        
        # Check chapter limit
        num_lessons = len(active_posts)
        if num_lessons > self.chapter_limit:
            if not self.download_until_limit:
                color_print(f"\n  [!] Chapter '{chapter_name_clean}' has {num_lessons} lessons (limit: {self.chapter_limit}) - Skipping due to config", Colors.YELLOW)
                return
            else:
                color_print(f"\n  [!] Chapter '{chapter_name_clean}' has {num_lessons} lessons - Downloading first {self.chapter_limit} only", Colors.YELLOW)
                active_posts = active_posts[:self.chapter_limit]
        
        if not active_posts:
            color_print(f"    [!] No active posts found", Colors.RED)
            return
        
        color_print(f"\n  [*] Chapter: {chapter_folder}", Colors.BLUE, bold=True)
        color_print(f"      Lessons: {len(active_posts)}/{num_lessons}", Colors.CYAN)
        
        desc = chapter_info.get('description', 'No description')[:100]
        if desc:
            color_print(f"      Description: {desc}", Colors.DIM)
        
        # Update progress
        progress.update(chapter=chapter_folder[:50])
        
        for post_idx, post in enumerate(active_posts, 1):#
            lesson_name_raw = post.get('name', f'Lesson_{post_idx}')
            lesson_name = sanitize_name(lesson_name_raw)
            lesson_name = sanitize_name(lesson_name)

            self.debug_print(post, Colors.BLUE)
            # Create filename with number and name: "1. Lesson Name.mp4"
            video_filename = f"{post_idx}. {lesson_name}.mp4"
            video_path = chapter_dir / video_filename
            
            # Description file with same naming
            description_filename = f"{post_idx}. {lesson_name}.txt"
            description_path = chapter_dir / description_filename
            
            # Update progress
            progress.update(lesson=f"{post_idx}/{len(active_posts)}")
            
            # Use tqdm.write to avoid breaking progress bars
            tqdm.write(f"\n    [*] Lesson {post_idx}: {lesson_name_raw}")
            
            # Save description
            if post.get('description'):
                with open(description_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {lesson_name_raw}\n")
                    f.write(f"{'─'*30}\n\n")
                    f.write(post['description'])
                tqdm.write(f"        Description saved: {description_filename}")
            
            # Save content if any (as additional info)
            if post.get('content'):
                content_filename = f"{post_idx}. {lesson_name}_content.html"
                content_path = chapter_dir / content_filename
                with open(content_path, 'w', encoding='utf-8') as f:
                    f.write(f"<h1>{lesson_name_raw}</h1>\n")
                    f.write(post['content'])
            
            # Download video if present with retry
            video_info = post.get('video')
            if video_info:
                if video_info.get('hlsSrc'):
                    self.download_video_with_retry(video_info, video_path, post_idx, lesson_name)
                elif video_info.get('isExternal') and video_info.get('link'):
                    self.download_external_video(video_info['link'], video_path, lesson_name)
            
            # Download file attachments (PDFs, etc.)
            files = post.get('files', {})
            for file_id, file_info in files.items():
                download_url = file_info.get('downloadUrl')
                if not download_url:
                    continue
                
                original_name = file_info.get('originalName', f'{file_id}')
                content_type = file_info.get('contentType', '')
                file_size = file_info.get('size', 0)
                
                # Check if this is actually a downloadable file
                if not self.is_downloadable_file(download_url, content_type, file_size):
                    # Save as .url file for links
                    link_filename = f"{post_idx}. {lesson_name}_{sanitize_name(original_name)}.url"
                    link_path = chapter_dir / link_filename
                    
                    # Create Windows .url file format
                    with open(link_path, 'w', encoding='utf-8') as f:
                        f.write(f"[InternetShortcut]\nURL={download_url}\n")
                    tqdm.write(f"        [🔗] Saved link: {link_filename}")
                    continue
                
                # Sanitize filename and download
                original_name = sanitize_name(original_name)
                attachment_filename = f"{post_idx}. {lesson_name}_{original_name}"

                attachment_path = chapter_dir / attachment_filename
                
                # Check if file already exists
                if attachment_path.exists() and attachment_path.stat().st_size > 1000:
                    size_mb = attachment_path.stat().st_size / (1024 * 1024)
                    tqdm.write(f"        [✓] Already downloaded: {attachment_path.name} ({size_mb:.2f} MB)")
                    continue
                
                # Download the actual file
                self.download_file_with_retry(download_url, attachment_path)

                        
            time.sleep(self.config.get("download_delay", 0.3))
    
    def list_courses(self):
        """List all courses with their statistics"""
        courses = self.get_courses()
        
        if not courses:
            color_print("[-] No courses found", Colors.RED)
            return
        
        color_print(f"\n{'─'*100}", Colors.BOLD)
        color_print(f"{'COURSE LIST':^100}", Colors.CYAN, bold=True)
        color_print(f"{'─'*100}", Colors.BOLD)
        
        for i, course in enumerate(courses, 1):
            course_name = course.get('name', 'Unknown')
            course_id = course.get('id', 'N/A')
            chapters = course.get('chapters', {})
            num_chapters = len(chapters)
            
            # Calculate total lessons and duration
            total_lessons = sum(ch.get('numberOfActivePosts', 0) for ch in chapters.values())
            total_duration = sum(ch.get('videoTime', 0) for ch in chapters.values())
            
            # Check chapter limit warning
            exceeds_limit = any(ch.get('numberOfActivePosts', 0) > self.chapter_limit for ch in chapters.values())
            limit_warning = f" {Colors.RED}[!] Some chapters exceed {self.chapter_limit} lessons{Colors.RESET}" if exceeds_limit else ""
            
            color_print(f"\n[{i}] {course_name}", Colors.GREEN, bold=True)
            color_print(f"    ID: {course_id}", Colors.DIM)
            color_print(f"    Chapters: {num_chapters}", Colors.WHITE)
            color_print(f"    Total Lessons: {total_lessons}", Colors.WHITE)
            color_print(f"    Total Duration: {self.format_time(total_duration)}", Colors.WHITE)
            if exceeds_limit:
                color_print(f"    {limit_warning}", Colors.RED)
            
            # List chapters with their stats
            if num_chapters > 0:
                color_print(f"    {Colors.DIM}Chapters:{Colors.RESET}")
                sorted_chapters = sorted(chapters.items(), key=lambda x: x[1].get('priority', 999))
                for idx, (ch_id, ch_info) in enumerate(sorted_chapters[:5], 1):  # Show first 5 chapters
                    ch_name = ch_info.get('name', f'Chapter_{idx}')
                    ch_lessons = ch_info.get('numberOfActivePosts', 0)
                    ch_duration = ch_info.get('videoTime', 0)
                    warning = f" {Colors.RED}[LIMIT EXCEEDED]{Colors.RESET}" if ch_lessons > self.chapter_limit else ""
                    color_print(f"      {idx}. {ch_name[:50]} - {ch_lessons} lessons, {self.format_time(ch_duration)}{warning}", Colors.DIM)
                if len(sorted_chapters) > 5:
                    color_print(f"      ... and {len(sorted_chapters) - 5} more chapters", Colors.DIM)
        
        color_print(f"\n{'─'*50}", Colors.BOLD)
        color_print(f"Chapter limit: {self.chapter_limit} lessons", Colors.YELLOW)
        color_print(f"Download until limit: {self.download_until_limit}", Colors.YELLOW)
        color_print(f"{'─'*50}\n", Colors.BOLD)
    
    def dump_course(self, course_info: Dict, output_dir: str = "downloads"):
        """Dump a complete course"""
        course_title = sanitize_name(course_info.get('name', 'Course'))
        course_dir = Path(output_dir) / course_title
        course_dir.mkdir(parents=True, exist_ok=True)
        
        color_print(f"\n{'─'*35}", Colors.BOLD)
        color_print(f"[+] Course: {course_title}", Colors.GREEN, bold=True)
        color_print(f"[+] ID: {course_info.get('id')}", Colors.DIM)
        desc = course_info.get('description', 'No description')[:200]
        if desc:
            color_print(f"[+] Description: {desc}", Colors.DIM)
        color_print(f"{'─'*35}", Colors.BOLD)
        
        # Download course thumbnail
        self.download_course_thumbnail(course_info, course_dir)

        # Create course description file
        self.create_course_description_file(course_info, course_dir)
        
        # Create credits file
        self.create_credits_file(course_dir)
        
        # Update progress
        progress.update(course=course_title[:60])
        
        # Save course info as README
        with open(course_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(f"# {course_info.get('name', 'Course')}\n\n")
            f.write(f"## Description\n\n{course_info.get('description', 'No description')}\n\n")
            f.write(f"## Course Info\n\n")
            f.write(f"- **ID**: {course_info.get('id')}\n")
            f.write(f"- **Dump Date**: {datetime.now().isoformat()}\n")
            f.write(f"- **Chapter Limit**: {self.chapter_limit}\n")
            f.write(f"- **Download Until Limit**: {self.download_until_limit}\n")
        
        # Get chapters
        chapters = course_info.get('chapters', {})
        
        if not chapters:
            color_print("  [!] No chapters found", Colors.RED)
            return
        
        # Calculate totals
        total_lessons = sum(ch.get('numberOfActivePosts', 0) for ch in chapters.values())
        total_duration = sum(ch.get('videoTime', 0) for ch in chapters.values())
        
        color_print(f"  [+] Chapters: {len(chapters)}", Colors.CYAN)
        color_print(f"  [+] Total lessons: {total_lessons}", Colors.CYAN)
        color_print(f"  [+] Total duration: {self.format_time(total_duration)}", Colors.CYAN)
        
        # Sort chapters by priority
        sorted_chapters = sorted(chapters.items(), key=lambda x: x[1].get('priority', 999))
        
        # Create global progress bar for all lessons
        total_lessons_to_download = 0
        for chapter_id, chapter_info in sorted_chapters:
            if self.download_until_limit or chapter_info.get('numberOfActivePosts', 0) <= self.chapter_limit:
                total_lessons_to_download += min(chapter_info.get('numberOfActivePosts', 0), self.chapter_limit)
        
        # Set up global progress bar
        progress.pbar = tqdm(total=total_lessons_to_download, desc="Overall Progress", unit="lesson", position=0, leave=True)
        
        for idx, (chapter_id, chapter_info) in enumerate(sorted_chapters, 1):
            try:
                # Check if chapter exceeds limit
                num_posts = chapter_info.get('numberOfActivePosts', 0)
                if num_posts > self.chapter_limit and not self.download_until_limit:
                    tqdm.write(f"\n  [!] Chapter '{chapter_info.get('name', f'Chapter_{idx}')}' has {num_posts} lessons - Skipping (limit: {self.chapter_limit})")
                    continue
                
                # Dump the chapter
                self.dump_chapter(course_info['id'], chapter_info, course_dir, idx)
                
                # Update global progress bar
                lessons_downloaded = min(num_posts, self.chapter_limit) if self.download_until_limit else num_posts
                progress.pbar.update(lessons_downloaded)
                
            except Exception as e:
                tqdm.write(f"  [!] Error dumping chapter: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(self.config.get("chapter_delay", 1))
        
        progress.pbar.close()
        progress.pbar = None
        
        # Count total files
        total_files = sum(1 for _ in course_dir.rglob('*') if _.is_file())
        color_print(f"\n[+] Course dump complete: {course_dir}", Colors.GREEN, bold=True)
        color_print(f"[+] Total files saved: {total_files}", Colors.GREEN)
    
    def dump_all_courses(self, output_dir: str = "downloads"):
        """Dump all courses"""
        courses = self.get_courses()
        
        if not courses:
            color_print("[-] No courses found", Colors.RED)
            return
        
        color_print(f"\n[*] Found {len(courses)} course(s)", Colors.CYAN, bold=True)
        
        for i, course in enumerate(courses, 1):
            color_print(f"\n[{i}/{len(courses)}] Processing course...", Colors.BLUE, bold=True)
            try:
                self.dump_course(course, output_dir)
            except Exception as e:
                color_print(f"[-] Error dumping course: {e}", Colors.RED)
            
            time.sleep(self.config.get("course_delay", 2))


def main():
    print_banner()
    import argparse
    
    parser = argparse.ArgumentParser(description='Dump courses from mymemberspot.de')
    parser.add_argument('--email', '-e', required=True, help='Login email')
    parser.add_argument('--password', '-p', required=True, help='Login password')
    parser.add_argument('--output', '-o', default='downloads', help='Output directory')
    parser.add_argument('--course-id', help='Dump only specific course ID') # works with --course too
    parser.add_argument('--config', '-c', default='config.json', help='Config file path')
    parser.add_argument('--list', '-l', action='store_true', help='List all courses with stats and exit')
    
    args = parser.parse_args()
    
    dumper = MemberspotDumper(email=args.email, password=args.password, config_path=args.config)
    
    if args.list:
        dumper.list_courses()
        return
    
    if args.course_id:
        course = dumper.get_course_info(args.course_id)
        if course:
            dumper.dump_course(course, args.output)
        else:
            color_print(f"[-] Course {args.course_id} not found", Colors.RED)
    else:
        dumper.dump_all_courses(args.output)


if __name__ == "__main__":
    main()
