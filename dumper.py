#!/usr/bin/env python3
"""
mymemberspot.de Complete Course Dumper
Uses the chapter API endpoint that returns all posts with video URLs
"""

import requests
import json
import os
import time
import subprocess
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import shutil

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

class MemberspotDumper:
    def __init__(self, email: str = None, password: str = None, config_path: str = "config.json"):
        # Load config
        self.config = self.load_config(config_path)
        
        self.api_base = self.config.get("api_base", "https://client-api.memberspot.de")
        self.firebase_api_key = self.config.get("firebase_api_key")
        self.tenant_id = self.config.get("tenant_id")
        self.school_id = self.config.get("school_id")
        self.base_url = self.config.get("base_url")
        
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
            "course_delay": 2
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
    
    def download_video(self, video_info: Dict, output_path: Path, lesson_num: int, lesson_name: str):
        """Download video using the hlsSrc URL"""
        hls_url = video_info.get('hlsSrc')
        if not hls_url:
            color_print(f"        [!] No hlsSrc found in video info", Colors.RED)
            return False
        
        color_print(f"        [*] Downloading video: {lesson_num}. {lesson_name}", Colors.CYAN)
        
        # Use yt-dlp for best results
        ytdlp = shutil.which('yt-dlp')
        if ytdlp:
            cmd = [
                ytdlp,
                '-N', str(self.config.get("ytdlp_threads", 4)),
                '-o', str(output_path),
                '--no-progress',
                hls_url
            ]
        else:
            # Fallback to ffmpeg
            ffmpeg = shutil.which('ffmpeg')
            if not ffmpeg:
                color_print(f"        [!] Neither yt-dlp nor ffmpeg found", Colors.RED)
                return False
            
            cmd = [
                ffmpeg, '-i', hls_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                str(output_path),
                '-y'
            ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                color_print(f"        [+] Downloaded: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                return True
            else:
                error = result.stderr[:200] if result.stderr else "Unknown"
                color_print(f"        [-] Download error: {error}", Colors.RED)
                return False
        except Exception as e:
            color_print(f"        [-] Error: {e}", Colors.RED)
            return False
    
    def download_file(self, url: str, output_path: Path):
        """Download file attachment"""
        try:
            response = requests.get(url, headers=self.api_headers, stream=True)
            if response.status_code == 200:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_mb = output_path.stat().st_size / (1024 * 1024)
                color_print(f"        [+] Downloaded: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                return True
        except Exception as e:
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
        
        color_print(f"\n  [*] Chapter: {chapter_folder}", Colors.BLUE, bold=True)
        desc = chapter_info.get('description', 'No description')[:100]
        if desc:
            color_print(f"      Description: {desc}", Colors.DIM)
        
        # Get full chapter details with all posts
        chapter_details = self.get_chapter_details(course_id, chapter_info['id'])
        
        if not chapter_details:
            color_print(f"    [!] Could not get chapter details", Colors.RED)
            return
        
        # Get active posts
        active_posts = chapter_details.get('activePosts', [])
        
        if not active_posts:
            color_print(f"    [!] No active posts found", Colors.RED)
            return
        
        color_print(f"      Lessons: {len(active_posts)}", Colors.CYAN)
        
        for post_idx, post in enumerate(active_posts, 1):
            lesson_name_raw = post.get('name', f'Lesson_{post_idx}')
            lesson_name = sanitize_name(lesson_name_raw)
            
            # Create filename with number and name: "1. Lesson Name.mp4"
            video_filename = f"{post_idx}. {lesson_name}.mp4"
            video_path = chapter_dir / video_filename
            
            # Description file with same naming
            description_filename = f"{post_idx}. {lesson_name}.txt"
            description_path = chapter_dir / description_filename
            
            color_print(f"\n    [*] Lesson {post_idx}: {lesson_name_raw}", Colors.YELLOW)
            
            # Save description
            if post.get('description'):
                with open(description_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {lesson_name_raw}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(post['description'])
                color_print(f"        📝 Description saved: {description_filename}", Colors.DIM)
            
            # Save content if any (as additional info)
            if post.get('content'):
                content_filename = f"{post_idx}. {lesson_name}_content.html"
                content_path = chapter_dir / content_filename
                with open(content_path, 'w', encoding='utf-8') as f:
                    f.write(f"<h1>{lesson_name_raw}</h1>\n")
                    f.write(post['content'])
            
            # Download video if present
            video_info = post.get('video')
            if video_info and video_info.get('hlsSrc'):
                self.download_video(video_info, video_path, post_idx, lesson_name)
            
            # Download file attachments (PDFs, etc.)
            files = post.get('files', {})
            for file_id, file_info in files.items():
                if file_info.get('downloadUrl'):
                    # Name attachment with post number and original name
                    original_name = file_info.get('originalName', f'{file_id}.pdf')
                    original_name = sanitize_name(original_name)
                    attachment_filename = f"{post_idx}. {lesson_name}_{original_name}"
                    attachment_path = chapter_dir / attachment_filename
                    self.download_file(file_info['downloadUrl'], attachment_path)
            
            time.sleep(self.config.get("download_delay", 0.3))
    
    def dump_course(self, course_info: Dict, output_dir: str = "downloads"):
        """Dump a complete course"""
        course_title = sanitize_name(course_info.get('name', 'Course'))
        course_dir = Path(output_dir) / course_title
        course_dir.mkdir(parents=True, exist_ok=True)
        
        color_print(f"\n{'='*70}", Colors.BOLD)
        color_print(f"[+] Course: {course_title}", Colors.GREEN, bold=True)
        color_print(f"[+] ID: {course_info.get('id')}", Colors.DIM)
        desc = course_info.get('description', 'No description')[:200]
        if desc:
            color_print(f"[+] Description: {desc}", Colors.DIM)
        color_print(f"{'='*70}", Colors.BOLD)
        
        # Save course info as README
        with open(course_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(f"# {course_info.get('name', 'Course')}\n\n")
            f.write(f"## Description\n\n{course_info.get('description', 'No description')}\n\n")
            f.write(f"## Course Info\n\n")
            f.write(f"- **ID**: {course_info.get('id')}\n")
            f.write(f"- **Dump Date**: {datetime.now().isoformat()}\n")
        
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
        
        for idx, (chapter_id, chapter_info) in enumerate(sorted_chapters, 1):
            try:
                self.dump_chapter(course_info['id'], chapter_info, course_dir, idx)
            except Exception as e:
                color_print(f"  [!] Error dumping chapter: {e}", Colors.RED)
                import traceback
                traceback.print_exc()
            
            time.sleep(self.config.get("chapter_delay", 1))
        
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
    parser.add_argument('--course-id', help='Dump only specific course ID')
    parser.add_argument('--config', '-c', default='config.json', help='Config file path')
    
    args = parser.parse_args()
    
    dumper = MemberspotDumper(email=args.email, password=args.password, config_path=args.config)
    
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
