#!/usr/bin/env python3
"""
mymemberspot.de Complete Course Dumper
Uses the chapter API endpoint that returns all posts with video URLs
Enhanced with Playwright for JavaScript-rendered content with persistent session
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
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
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
    ██║╚██╔╝██║  ╚██╔╝  ██║╚██╔╝██║██╔══╝  ██╔══██╗╚════██╗██╔═══╝ ██╔══██╗   ██║   
    ██║ ╚═╝ ██║   ██║   ██║ ╚═╝ ██║███████╗██║  ██║███████║██║     ██║  ██║   ██║   
    ╚═╝     ╚═╝   ╚═╝   ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝   

                    ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗                    
                    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗                   
                    ██║  ██║██║   ██║████╔████╔██║██████╔╝█████╗  ██████╔╝                   
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
            
            desc = f"{self.current_course or 'N/A'}"
            if self.current_chapter:
                desc += f" | {self.current_chapter}"
            if self.current_lesson:
                desc += f" | {self.current_lesson}"
            self.pbar.set_description(desc[:80])

progress = ProgressTracker()

class MemberspotDumper:
    def __init__(self, email: str = None, password: str = None, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        
        self.api_base = self.config.get("api_base", "https://client-api.memberspot.de")
        self.firebase_api_key = self.config.get("firebase_api_key")
        self.tenant_id = self.config.get("tenant_id")
        self.school_id = self.config.get("school_id")
        self.base_url = self.config.get("base_url")
        self.debug = self.config.get("debug", False)
        self.use_playwright = self.config.get("use_playwright", True)
        
        self.chapter_limit = self.config.get("chapter_limit", 50)
        self.download_until_limit = self.config.get("download_until_limit", True)
        
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 5)
        
        if not all([self.firebase_api_key, self.tenant_id, self.school_id, self.base_url]):
            color_print("[-] Missing required config values! Check config.json", Colors.RED)
            raise ValueError("Missing required configuration")
        
        self.session = requests.Session()
        self.id_token = None
        self.email = email
        self.password = password
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.playwright_initialized = False
        
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
            "ytdlp_fragment_retries": 10,
            "debug": False,
            "use_playwright": True,
            "playwright_headless": True,
            "playwright_timeout": 10000,
            "playwright_wait_for": "appc-post-content"
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    color_print(f"[+] Loaded config from {config_path}", Colors.GREEN)
            except Exception as e:
                color_print(f"[-] Error loading config: {e}", Colors.RED)
                color_print(f"[*] Using default config", Colors.YELLOW)
        else:
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
        self.email = email
        self.password = password
        
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
    
    def init_playwright(self):
        """Initialize Playwright browser with persistent session"""
        if self.playwright_initialized:
            return True
        
        if not self.use_playwright:
            return False
        
        try:
            import os
            possible_paths = [
                os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-1181/chrome-headless-shell-linux64/chrome-headless-shell"),
                os.path.expanduser("~/.cache/ms-playwright/chromium-1181/chrome-linux64/chrome"),
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]
            
            self.playwright = sync_playwright().start()
            headless=self.config.get("playwright_headless", True)
            browser = None
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        browser = self.playwright.chromium.launch(
                            headless=headless,
                            executable_path=path,
                            args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-dev-shm-usage',
                                '--disable-accelerated-2d-canvas',
                                '--disable-gpu',
                                '--disable-web-security',
                                '--disable-features=IsolateOrigins,site-per-process'
                            ]
                        )
                        color_print(f"        [*] Found browser at: {path}", Colors.DIM)
                        break
                    except Exception as e:
                        continue
            
            if not browser:
                try:
                    browser = self.playwright.chromium.launch(
                        headless=headless,
                        args=['--no-sandbox', '--disable-setuid-sandbox']
                    )
                except Exception as e:
                    raise Exception(f"No browser found: {e}")
            
            self.browser = browser
            self.context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            
            self.page = self.context.new_page()
            
            color_print(f"        [*] Logging in with Playwright...", Colors.CYAN)
            login_url = f"{self.base_url}/login"
            self.page.goto(login_url, wait_until='domcontentloaded', timeout=15000)
            
            try:
                self.page.wait_for_selector('input[type="text"], input[type="email"]', timeout=10000)
                
                email_input = self.page.locator('input[type="text"], input[type="email"]').first
                email_input.fill(self.email or '')
                
                password_input = self.page.locator('input[type="password"]').first
                password_input.fill(self.password or '')
                
                login_button_selectors = [
                    'button[type="submit"]',
                    'button[data-cy="userLoginButton"]',
                    'button:has-text("Login")',
                    'button:has-text("Anmelden")'
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        login_button = self.page.locator(selector).first
                        if login_button.is_visible():
                            break
                    except:
                        continue
                
                if login_button:
                    login_button.click()
                else:
                    password_input.press('Enter')
                
                self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                
                try:
                    self.page.wait_for_selector('appc-shell-view, appc-header-mobile, .client-header', timeout=10000)
                    color_print(f"        [✓] Playwright login successful!", Colors.GREEN)
                    self.playwright_initialized = True

                    cookies = self.context.cookies()
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                    
                    return True
                except:
                    color_print(f"        [!] Login may have failed, but continuing...", Colors.YELLOW)
                    self.playwright_initialized = True
                    return True
                    
            except Exception as e:
                color_print(f"        [!] Playwright login failed: {e}", Colors.RED)
                self.close_playwright()
                return False
                
        except Exception as e:
            color_print(f"        [!] Playwright initialization failed: {e}", Colors.RED)
            return False
    
    def close_playwright(self):
        """Close Playwright browser"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        self.playwright_initialized = False
    
    def get_lesson_page_html_playwright(self, post_id: str, course_id: str = None, chapter_id: str = None) -> Optional[str]:
        """Fetch the HTML page using Playwright with persistent session"""
        if not post_id:
            return None
        
        if not self.use_playwright:
            return None
        
        if not self.playwright_initialized:
            if not self.init_playwright():
                return None
        
        if course_id and chapter_id:
            lesson_url = f"{self.base_url}/library/{course_id}/{chapter_id}/{post_id}/details"
        else:
            lesson_url = f"{self.base_url}/post/{post_id}"
        
        try:
            tqdm.write(f"        [*] Loading page with Playwright...")
            self.page.goto(lesson_url, wait_until='domcontentloaded', timeout=15000)
            
            selectors = [
                'appc-post-content',
                'tiptap-editor', 
                '.ProseMirror',
                'appc-lecture',
                'appc-post-wrapper',
                '.video-card',
                'media-player',
                'appc-post-details'
            ]
            
            content_loaded = False
            for selector in selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    tqdm.write(f"        [✓] Content loaded with selector: {selector}")
                    content_loaded = True
                    break
                except:
                    continue
            
            if not content_loaded:
                tqdm.write(f"        [⚠] Content may not have loaded fully")
                if self.debug:
                    debug_dir = Path("debug_html_playwright")
                    debug_dir.mkdir(exist_ok=True)
                    screenshot_file = debug_dir / f"lesson_{post_id}_screenshot.png"
                    self.page.screenshot(path=str(screenshot_file), full_page=True)
                    tqdm.write(f"        [DEBUG] Saved screenshot to: {screenshot_file}")
            
            html_content = self.page.content()
            
            if 'appc-client-login' in html_content or 'Login' in html_content:
                tqdm.write(f"        [⚠] Still on login page - session may have expired")
                self.close_playwright()
                self.playwright_initialized = False
                if self.init_playwright():
                    self.page.goto(lesson_url, wait_until='domcontentloaded', timeout=15000)
                    html_content = self.page.content()
            
            if self.debug:
                debug_dir = Path("debug_html_playwright")
                debug_dir.mkdir(exist_ok=True)
                debug_file = debug_dir / f"lesson_{post_id}_playwright.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                tqdm.write(f"        [DEBUG] Saved Playwright HTML to: {debug_file}")
                
                screenshot_file = debug_dir / f"lesson_{post_id}_screenshot.png"
                self.page.screenshot(path=str(screenshot_file), full_page=True)
                tqdm.write(f"        [DEBUG] Saved screenshot to: {screenshot_file}")
            
            return html_content
            
        except Exception as e:
            tqdm.write(f"        [!] Playwright error: {e}")
            self.close_playwright()
            self.playwright_initialized = False
            return None

    def debug_print(self, msg, color=Colors.DIM):
        if self.debug:
            color_print(msg, color)

    def find_m3u8_in_data(self, data, max_depth=5):
        """Recursively search for m3u8 URLs in nested dict/list structures"""
        if max_depth < 0:
            return []
        
        urls = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and ('.m3u8' in value or 'hls.m3u8' in value):
                    if value.startswith('http') or value.startswith('/'):
                        urls.append(value)
                    elif '://' in value:
                        urls.append(value)
                else:
                    urls.extend(self.find_m3u8_in_data(value, max_depth - 1))
        
        elif isinstance(data, list):
            for item in data:
                urls.extend(self.find_m3u8_in_data(item, max_depth - 1))
        
        return urls

    def download_video(self, video_info: Dict, output_path: Path, lesson_num: int, lesson_name: str):
        """Download video using HLS with safe temp file handling - enhanced with fallback"""
        
        hls_url = None
        video_id = None
        
        if isinstance(video_info, dict):
            for key in ['hlsSrc', 'src', 'url', 'link', 'playbackUrl', 'streamUrl', 'videoUrl', 'hls', 'source']:
                if video_info.get(key) and isinstance(video_info[key], str):
                    value = video_info[key]
                    if '.m3u8' in value:
                        hls_url = value
                        self.debug_print(f"        [DEBUG] Found HLS URL in '{key}': {hls_url[:100]}...", Colors.DIM)
                        break
            
            if 'id' in video_info:
                video_id = video_info['id']
        
        if not hls_url and video_id:
            for key in ['previewThumbnails', 'previewImg', 'thumbnail']:
                if video_info.get(key) and isinstance(video_info[key], str):
                    preview_url = video_info[key]
                    match = re.match(r'(https://[^/]+/[^/]+/[^/]+)/[^/]+$', preview_url)
                    if match:
                        base_path = match.group(1)
                        hls_url = f"{base_path}/hls.m3u8"
                        self.debug_print(f"        [DEBUG] Constructed HLS URL from preview URL: {hls_url[:100]}...", Colors.DIM)
                        break
        
        if not hls_url and isinstance(video_info, dict):
            self.debug_print(f"        [DEBUG] Searching for m3u8 in video_info...", Colors.DIM)
            found_urls = self.find_m3u8_in_data(video_info)
            if found_urls:
                hls_url = found_urls[0]
                self.debug_print(f"        [DEBUG] Found m3u8 in nested data: {hls_url[:100]}...", Colors.DIM)
        
        if not hls_url and isinstance(video_info, str):
            if '.m3u8' in video_info or 'vimeo.com' in video_info or 'youtube.com' in video_info:
                hls_url = video_info
                self.debug_print(f"        [DEBUG] video_info is URL string: {hls_url[:100]}...", Colors.DIM)
        
        if not hls_url and isinstance(video_info, dict):
            if video_info.get('isExternal') and video_info.get('link'):
                self.debug_print(f"        [DEBUG] External video detected, using download_external_video", Colors.DIM)
                return self.download_external_video(video_info['link'], output_path, lesson_name)
            
            for key in ['link', 'url', 'embed', 'iframe']:
                if video_info.get(key) and isinstance(video_info[key], str):
                    value = video_info[key]
                    if 'vimeo.com' in value or 'youtube.com' in value or 'youtu.be' in value:
                        self.debug_print(f"        [DEBUG] Found external video in '{key}': {value[:100]}...", Colors.DIM)
                        return self.download_external_video(value, output_path, lesson_name)
        
        if not hls_url and isinstance(video_info, dict):
            for field in ['content', 'description', 'html', 'body']:
                if video_info.get(field) and isinstance(video_info[field], str):
                    content = video_info[field]
                    m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', content)
                    if m3u8_match:
                        hls_url = m3u8_match.group(0)
                        self.debug_print(f"        [DEBUG] Found m3u8 in {field}: {hls_url[:100]}...", Colors.DIM)
                        break
                    
                    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', content)
                    if iframe_match:
                        iframe_url = iframe_match.group(1)
                        if 'vimeo.com' in iframe_url or 'youtube.com' in iframe_url:
                            self.debug_print(f"        [DEBUG] Found iframe with video in {field}", Colors.DIM)
                            return self.download_external_video(iframe_url, output_path, lesson_name)
        
        if not hls_url:
            self.debug_print(f"        [!] No video URL found after all fallbacks", Colors.RED)
            if self.debug:
                self.debug_print(f"        [DEBUG] Full video_info structure:", Colors.YELLOW)
                if isinstance(video_info, dict):
                    for key, value in video_info.items():
                        if isinstance(value, str) and len(value) < 200:
                            self.debug_print(f"        [DEBUG]   {key}: {value[:100]}", Colors.YELLOW)
                        elif isinstance(value, dict):
                            self.debug_print(f"        [DEBUG]   {key}: dict with {len(value)} keys", Colors.YELLOW)
                            for subkey, subvalue in value.items():
                                if isinstance(subvalue, str) and len(subvalue) < 200:
                                    self.debug_print(f"        [DEBUG]     {subkey}: {subvalue[:100]}", Colors.YELLOW)
            return False

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.debug_print(f"        [!] Directory creation failed: {e}", Colors.RED)
            return False

        if output_path.exists():
            size = output_path.stat().st_size
            if size > 1024 * 1024:
                size_mb = size / (1024 * 1024)
                color_print(f"        [✓] Already exists: {output_path.name} ({size_mb:.2f} MB)", Colors.GREEN)
                return True
            else:
                output_path.unlink()

        ytdlp = shutil.which('yt-dlp')
        if not ytdlp:
            self.debug_print(f"        [!] yt-dlp not found", Colors.RED)
            return False

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
            hls_url
        ]

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
                
                if result.stderr and ("drm" in result.stderr.lower() or "widevine" in result.stderr.lower()):
                    tqdm.write(f"        [!] Video is DRM protected (Widevine). Cannot download with yt-dlp.")
                    tqdm.write(f"        [!] Try using N_m3u8DL-RE with the appropriate key.")
                    
                    vid_id = video_info.get('id', 'unknown')
                    if vid_id != 'unknown':
                        tqdm.write(f"        [i] Video ID: {vid_id}")
                    
                    if hls_url:
                        tqdm.write(f"        [i] HLS URL: {hls_url}")
                    
                    return False

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
            if temp_output.exists():
                try:
                    temp_output.unlink()
                except:
                    pass

    def download_video_with_retry(self, video_info: Dict, output_path: Path, lesson_num: int, lesson_name: str):
        """Download video with retry mechanism and stealth yt-dlp command"""
        for attempt in range(self.max_retries):
            if attempt > 0:
                color_print(f"        [*] Video retry {attempt}/{self.max_retries}...", Colors.YELLOW)
                time.sleep(self.retry_delay)
                if attempt == 2: 
                    color_print(f"        [*] Attempting to refresh authentication...", Colors.YELLOW)
            
            if self.download_video(video_info, output_path, lesson_num, lesson_name):
                return True
        
        color_print(f"        [-] Failed after {self.max_retries} attempts", Colors.RED)
        return False

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
                
                try:
                    head_response = requests.head(url, headers=file_headers, timeout=10)
                    content_disposition = head_response.headers.get('content-disposition', '')
                    if content_disposition and 'filename=' in content_disposition:
                        import urllib.parse
                        match = re.search(r'filename\*?=([^;]+)', content_disposition)
                        if match:
                            filename = match.group(1).strip().strip('"')
                            if filename.startswith("UTF-8''"):
                                filename = urllib.parse.unquote(filename[7:])
                            new_path = output_path.parent / filename
                            if not new_path.exists():
                                output_path = new_path
                except:
                    pass
                
                response = requests.get(url, headers=file_headers, stream=True, timeout=30)
                
                if response.status_code == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    if output_path.name == 'unknown.bin' or output_path.suffix == '.bin':
                        import urllib.parse
                        url_path = urllib.parse.urlparse(url).path
                        if url_path:
                            filename_from_url = os.path.basename(url_path)
                            if filename_from_url and '.' in filename_from_url:
                                new_path = output_path.parent / filename_from_url
                                if not new_path.exists():
                                    output_path = new_path
                    
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
        if content_type == 'link':
            return False
        
        if file_size == 0:
            return False
        
        if '/produkt/' in url or '/product/' in url:
            return False
        
        downloadable_extensions = ('.pdf', '.zip', '.rar', '.7z', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4')
        if any(url.lower().endswith(ext) for ext in downloadable_extensions):
            return True
        
        if 'files.mspotcdn.de' in url and 'alt=media' in url and 'token=' in url:
            return True
        
        return False

    def get_lesson_details_api_v2(self, course_id: str, chapter_id: str, post_id: str) -> Optional[Dict]:
        """Try to get lesson details from the API using the correct endpoint"""
        if not all([course_id, chapter_id, post_id]):
            return None
        
        endpoints = [
            f"{self.api_base}/user-course/post/{self.school_id}/{post_id}",
            f"{self.api_base}/library/post/{self.school_id}/{post_id}",
            f"{self.api_base}/course/{course_id}/chapter/{chapter_id}/post/{post_id}",
            f"{self.api_base}/posts/{post_id}",
            f"{self.base_url}/api/post/{post_id}",
            f"{self.base_url}/api/library/{course_id}/{chapter_id}/{post_id}",
        ]
        
        for url in endpoints:
            try:
                self.debug_print(f"        [DEBUG] Trying API: {url}", Colors.DIM)
                response = requests.get(url, headers=self.api_headers)
                if response.status_code == 200:
                    data = response.json()
                    if data and (data.get('description') or data.get('content') or data.get('files')):
                        self.debug_print(f"        [DEBUG] Found data in API: {url}", Colors.GREEN)
                        return data
            except Exception as e:
                self.debug_print(f"        [DEBUG] API failed: {e}", Colors.DIM)
                continue
        
        return None

    def extract_description_from_html(self, html_content: str) -> str:
        """Extract the lesson description from the HTML page - focused on appc-post-content"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            post_content = soup.find('appc-post-content')
            if post_content:
                tiptap = post_content.find('tiptap-editor')
                if tiptap:
                    prose_mirror = tiptap.find('div', class_='ProseMirror')
                    if prose_mirror:
                        text_parts = []
                        for child in prose_mirror.children:
                            if child.name == 'p':
                                text = child.get_text(strip=True)
                                if text:
                                    text_parts.append(text)
                            elif child.name == 'br':
                                text_parts.append('')
                        return '\n\n'.join(text_parts) if text_parts else ""
            
            prose_mirror = soup.find('div', class_='ProseMirror')
            if prose_mirror:
                text_parts = []
                for child in prose_mirror.children:
                    if child.name == 'p':
                        text = child.get_text(strip=True)
                        if text:
                            text_parts.append(text)
                    elif child.name == 'br':
                        text_parts.append('')
                return '\n\n'.join(text_parts) if text_parts else ""
            
            return ""
            
        except Exception as e:
            self.debug_print(f"        [!] Error extracting description: {e}", Colors.YELLOW)
            return ""

    def extract_attachments_from_html_page(self, html_content: str) -> List[Dict]:
        """Extract attachments from the full HTML page - focused on mspot-file-attachments-list"""
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            attachments = []
            seen_urls = set()
            
            for container in soup.find_all('mspot-file-attachments-list'):
                for link in container.find_all('a', href=True):
                    href = link.get('href')
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    name = link.get_text(strip=True)
                    if not name:
                        img = link.find('img')
                        if img and img.get('alt'):
                            name = img.get('alt')
                        else:
                            name = f"attachment_{len(attachments)+1}"
                    
                    is_download = link.get('download') is not None or 'files.mspotcdn.de' in href
                    
                    is_file = any(href.lower().endswith(ext) for ext in ['.zip', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4'])
                    
                    size_text = ""
                    size_elem = link.find_parent().find('div', class_=lambda x: x and 'text-text-default' in x) if link.find_parent() else None
                    if size_elem:
                        size_text = size_elem.get_text(strip=True)
                    
                    attachments.append({
                        'url': href,
                        'name': name,
                        'is_download': is_download or is_file,
                        'size': size_text,
                        'is_file': is_file or 'files.mspotcdn.de' in href
                    })
                
                for btn in container.find_all('mspot-download-button'):
                    link = btn.find('a', href=True)
                    if not link:
                        continue
                        
                    href = link.get('href')
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    name = link.get_text(strip=True)
                    if not name:
                        img = link.find('img')
                        if img and img.get('alt'):
                            name = img.get('alt')
                        else:
                            name = f"attachment_{len(attachments)+1}"
                    
                    is_download = link.get('download') is not None or 'files.mspotcdn.de' in href
                    is_file = any(href.lower().endswith(ext) for ext in ['.zip', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4'])
                    
                    size_text = ""
                    size_elem = btn.find('div', class_=lambda x: x and 'text-text-default' in x)
                    if size_elem:
                        size_text = size_elem.get_text(strip=True)
                    
                    attachments.append({
                        'url': href,
                        'name': name,
                        'is_download': is_download or is_file,
                        'size': size_text,
                        'is_file': is_file or 'files.mspotcdn.de' in href
                    })
            
            return attachments
            
        except Exception as e:
            self.debug_print(f"        [!] Error extracting attachments from HTML: {e}", Colors.YELLOW)
            return []

    def download_lesson_attachments(self, post_id: str, chapter_dir: Path, post_idx: int, lesson_name: str, course_id: str = None, chapter_id: str = None):
        """Download attachments by fetching the lesson HTML page"""
        html_content = self.get_lesson_page_html_playwright(post_id, course_id, chapter_id)
        if not html_content:
            tqdm.write(f"        [!] Could not fetch lesson page for attachments")
            return
        
        attachments = self.extract_attachments_from_html_page(html_content)
        
        if not attachments:
            tqdm.write(f"        [ℹ] No attachments found on lesson page")
            return
        
        tqdm.write(f"        [*] Found {len(attachments)} attachment(s) on lesson page")
        
        for attachment in attachments:
            url = attachment['url']
            name = attachment['name']
            is_download = attachment['is_download']
            size_text = attachment.get('size', '')
            is_file = attachment.get('is_file', False)
            
            clean_name = sanitize_name(name)
            clean_name = re.sub(r'\s*Link\s*$', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s*\(Link\)\s*$', '', clean_name, flags=re.IGNORECASE)
            clean_name = clean_name.strip()
            
            if not clean_name:
                clean_name = f"attachment_{post_idx}_{len(attachments)}"
            
            if 'docs.google.com' in url:
                is_download = False
                is_file = False
            
            if 'webinar' in url or 'utm_source' in url:
                is_download = False
                is_file = False
            
            if 'files.mspotcdn.de' in url:
                is_download = True
                is_file = True
            
            if is_download and is_file:
                ext = ''
                if '.' in url.split('/')[-1]:
                    ext = '.' + url.split('/')[-1].split('.')[-1].split('?')[0]
                elif 'files.mspotcdn.de' in url:
                    parts = url.split('/')
                    if parts and '.' in parts[-1]:
                        ext = '.' + parts[-1].split('.')[-1].split('?')[0]
                    else:
                        ext = '.bin'
                if 'zip' in url.lower() or '.zip' in url.lower():
                    ext = '.zip'
                elif 'pdf' in url.lower() or '.pdf' in url.lower():
                    ext = '.pdf'
                elif 'doc' in url.lower() or '.docx' in url.lower():
                    ext = '.docx'
                elif 'mp3' in url.lower() or '.mp3' in url.lower():
                    ext = '.mp3'
                elif 'mp4' in url.lower() or '.mp4' in url.lower():
                    ext = '.mp4'
                
                if not ext:
                    ext = '.bin'
                
                attachment_filename = f"{post_idx}. {clean_name}{ext}"
                attachment_path = chapter_dir / attachment_filename
                if attachment_path.exists() and attachment_path.stat().st_size > 1000:
                    size_mb = attachment_path.stat().st_size / (1024 * 1024)
                    tqdm.write(f"        [✓] Already downloaded: {attachment_path.name} ({size_mb:.2f} MB)")
                    continue
                tqdm.write(f"        [*] Downloading: {attachment_filename}{' (' + size_text + ')' if size_text else ''}")
                self.download_file_with_retry(url, attachment_path)
            else:
                clean_name = re.sub(r'\s*Link\s*$', '', clean_name, flags=re.IGNORECASE)
                clean_name = clean_name.strip()
                link_filename = f"{post_idx}. {clean_name}.url"
                link_path = chapter_dir / link_filename
                if link_path.exists():
                    continue
                with open(link_path, 'w', encoding='utf-8') as f:
                    f.write(f"[InternetShortcut]\nURL={url}\n")
                tqdm.write(f"        [🔗] Saved link: {link_filename}")

    def debug_video_structure(self, post_data, post_idx, lesson_name):
        """Debug the video structure in the post data"""
        color_print(f"\n        [DEBUG] === Video structure for Lesson {post_idx}: {lesson_name} ===", Colors.YELLOW)
        if 'video' in post_data:
            video_data = post_data['video']
            color_print(f"        [DEBUG] Found 'video' key of type: {type(video_data)}", Colors.YELLOW)
            
            if isinstance(video_data, dict):
                color_print(f"        [DEBUG] Video keys: {list(video_data.keys())}", Colors.YELLOW)
                for key, value in video_data.items():
                    if isinstance(value, str) and len(str(value)) < 200:
                        color_print(f"        [DEBUG]   {key}: {value[:150]}", Colors.YELLOW)
                    elif isinstance(value, dict):
                        color_print(f"        [DEBUG]   {key}: dict with keys {list(value.keys())}", Colors.YELLOW)
                    elif isinstance(value, list):
                        color_print(f"        [DEBUG]   {key}: list with {len(value)} items", Colors.YELLOW)
                        for i, item in enumerate(value[:3]):
                            if isinstance(item, dict):
                                color_print(f"        [DEBUG]     item {i}: {list(item.keys())}", Colors.YELLOW)
                            else:
                                color_print(f"        [DEBUG]     item {i}: {str(item)[:100]}", Colors.YELLOW)
                    else:
                        color_print(f"        [DEBUG]   {key}: {str(value)[:100]}", Colors.YELLOW)
            elif isinstance(video_data, str):
                color_print(f"        [DEBUG] video is a string: {video_data[:200]}", Colors.YELLOW)
        else:
            color_print(f"        [DEBUG] No 'video' key found in post", Colors.RED)
        video_related_keys = ['content', 'description', 'videoUrl', 'playbackUrl', 'hls', 'stream', 'media', 'url', 'link', 'src']
        found_keys = []
        
        for key in video_related_keys:
            if key in post_data:
                value = post_data[key]
                if isinstance(value, str) and ('.m3u8' in value or 'vimeo' in value or 'youtube' in value or 'mp4' in value):
                    found_keys.append(f"{key}: {value[:100]}...")
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, str) and ('.m3u8' in subvalue or 'vimeo' in subvalue):
                            found_keys.append(f"{key}.{subkey}: {subvalue[:100]}...")
        
        if found_keys:
            color_print(f"        [DEBUG] Found video-related data in other keys:", Colors.GREEN)
            for found in found_keys:
                color_print(f"        [DEBUG]   {found}", Colors.GREEN)
        else:
            color_print(f"        [DEBUG] No video-related data found in common keys", Colors.RED)
        if self.debug:
            color_print(f"        [DEBUG] Full post structure:", Colors.BLUE)
            color_print(json.dumps(post_data, indent=2, default=str)[:2000], Colors.DIM)
        
        color_print(f"        [DEBUG] === End debug ===", Colors.YELLOW)

    def clean_html(self, html_content: str) -> str:
        """Remove HTML tags from content and return plain text"""
        if not html_content:
            return ""
        clean = re.sub(r'<[^>]+>', ' ', html_content)
        clean = re.sub(r'\s+', ' ', clean)
        clean = re.sub(r'&[a-z]+;', ' ', clean, flags=re.IGNORECASE)
        clean = clean.strip()
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean
    
    def create_course_description_file(self, course_info: Dict, course_dir: Path):
        """Create a formatted description file for the course"""
        name = course_info.get('name', 'No Title')
        description = course_info.get('description', 'No description')
        content = course_info.get('content', '')
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

    def download_chapter_thumbnail(self, chapter_info: Dict, chapter_dir: Path, chapter_idx: int):
        """Download chapter thumbnail image"""
        thumbnail_url = chapter_info.get('thumbnailUrl')
        
        if not thumbnail_url:
            return
        if thumbnail_url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            base_url = thumbnail_url.split('?')[0]
            ext = base_url.split('.')[-1]
        else:
            ext = 'jpg'
        
        thumbnail_path = chapter_dir / f"chapter_thumbnail.{ext}"
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
        thumbnail_url = course_info.get('thumbnailUrl') or course_info.get('image')
        
        if not thumbnail_url:
            color_print(f"  [!] No thumbnail URL found for course", Colors.YELLOW)
            return
        if thumbnail_url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            base_url = thumbnail_url.split('?')[0]
            ext = base_url.split('.')[-1]
        else:
            ext = 'jpg'
        
        thumbnail_path = course_dir / f"course_thumbnail.{ext}"
        if thumbnail_path.exists() and thumbnail_path.stat().st_size > 1000:
            color_print(f"  [✓] Thumbnail already exists", Colors.GREEN)
            return True
        
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

    def dump_chapter(self, course_id: str, chapter_info: Dict, course_dir: Path, chapter_idx: int):
        """Dump a chapter using the chapter details API - Enhanced with Playwright for JavaScript rendering"""
        chapter_name_raw = chapter_info.get('name', f'Chapter_{chapter_idx}')
        chapter_name_clean = re.sub(r'^Modul\s+\d+\s*\|\s*', '', chapter_name_raw)
        chapter_folder = f"{chapter_idx}. {chapter_name_clean}"
        chapter_folder = sanitize_name(chapter_folder)
        chapter_dir = course_dir / chapter_folder
        chapter_dir.mkdir(parents=True, exist_ok=True)
        chapter_details = self.get_chapter_details(course_id, chapter_info['id'])

        if not chapter_details:
            color_print(f"    [!] Could not get chapter details", Colors.RED)
            return
        self.download_chapter_thumbnail(chapter_info, chapter_dir, chapter_idx)
        self.create_chapter_description_file(chapter_info, chapter_dir, chapter_idx)
        active_posts = chapter_details.get('activePosts', [])
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
        progress.update(chapter=chapter_folder[:50])
        
        for post_idx, post in enumerate(active_posts, 1):
            lesson_name_raw = post.get('name', f'Lesson_{post_idx}')
            lesson_name = sanitize_name(lesson_name_raw)
            lesson_name = sanitize_name(lesson_name)
            
            post_id = post.get('id')
            chapter_id = chapter_info.get('id')
            if post_idx == 1:
                self.debug_video_structure(post, post_idx, lesson_name)
            video_filename = f"{post_idx}. {lesson_name}.mp4"
            video_path = chapter_dir / video_filename
            description_filename = f"{post_idx}. {lesson_name}.txt"
            description_path = chapter_dir / description_filename
            progress.update(lesson=f"{post_idx}/{len(active_posts)}")
            tqdm.write(f"\n    [*] Lesson {post_idx}: {lesson_name_raw}")
            api_data = None
            if post_id:
                if course_id and chapter_id:
                    api_data = self.get_lesson_details_api_v2(course_id, chapter_id, post_id)
                if not api_data:
                    api_data = self.get_lesson_details_api_v2(course_id, chapter_id, post_id)
                
            if api_data:
                description_text = api_data.get('description') or api_data.get('content')
                if description_text:
                    clean_desc = self.clean_html(description_text)
                    with open(description_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {lesson_name_raw}\n")
                        f.write(f"{'─'*30}\n\n")
                        f.write(clean_desc)
                    tqdm.write(f"        Description saved from API: {description_filename}")
                files = api_data.get('files', {})
                if files:
                    tqdm.write(f"        [*] Found {len(files)} attachment(s) in API")
                    for file_id, file_info in files.items():
                        download_url = file_info.get('downloadUrl')
                        if not download_url:
                            continue
                        original_name = file_info.get('originalName', f'{file_id}')
                        content_type = file_info.get('contentType', '')
                        file_size = file_info.get('size', 0)
                        clean_name = sanitize_name(original_name)
                        if not clean_name:
                            clean_name = f"attachment_{post_idx}"
                        if 'docs.google.com' in download_url or 'webinar' in download_url:
                            link_filename = f"{post_idx}. {clean_name}.url"
                            link_path = chapter_dir / link_filename
                            if not link_path.exists():
                                with open(link_path, 'w', encoding='utf-8') as f:
                                    f.write(f"[InternetShortcut]\nURL={download_url}\n")
                                tqdm.write(f"        [🔗] Saved link: {link_filename}")
                            continue
                        if self.is_downloadable_file(download_url, content_type, file_size):
                            ext = ''
                            if '.' in download_url.split('/')[-1]:
                                ext = '.' + download_url.split('/')[-1].split('.')[-1].split('?')[0]
                            if not ext:
                                ext = '.bin'
                            
                            attachment_filename = f"{post_idx}. {clean_name}{ext}"
                            attachment_path = chapter_dir / attachment_filename
                            
                            if attachment_path.exists() and attachment_path.stat().st_size > 1000:
                                size_mb = attachment_path.stat().st_size / (1024 * 1024)
                                tqdm.write(f"        [✓] Already downloaded: {attachment_path.name} ({size_mb:.2f} MB)")
                                continue
                            
                            tqdm.write(f"        [*] Downloading: {attachment_filename}")
                            self.download_file_with_retry(download_url, attachment_path)
                        else:
                            link_filename = f"{post_idx}. {clean_name}.url"
                            link_path = chapter_dir / link_filename
                            if not link_path.exists():
                                with open(link_path, 'w', encoding='utf-8') as f:
                                    f.write(f"[InternetShortcut]\nURL={download_url}\n")
                                tqdm.write(f"        [🔗] Saved link: {link_filename}")
            if not api_data and post_id and course_id and chapter_id:
                tqdm.write(f"        [*] Using Playwright to fetch rendered content...")
                html_content = self.get_lesson_page_html_playwright(post_id, course_id, chapter_id)
                if html_content:
                    description_text = self.extract_description_from_html(html_content)
                    if description_text:
                        with open(description_path, 'w', encoding='utf-8') as f:
                            f.write(f"Title: {lesson_name_raw}\n")
                            f.write(f"{'─'*30}\n\n")
                            f.write(description_text)
                        tqdm.write(f"        Description saved from Playwright HTML: {description_filename}")
                    else:
                        tqdm.write(f"        [ℹ] No description found in Playwright HTML")
                    self.download_lesson_attachments(post_id, chapter_dir, post_idx, lesson_name, course_id, chapter_id)
                else:
                    tqdm.write(f"        [!] Could not fetch lesson page with Playwright")
                    if post.get('description'):
                        with open(description_path, 'w', encoding='utf-8') as f:
                            f.write(f"Title: {lesson_name_raw}\n")
                            f.write(f"{'─'*30}\n\n")
                            f.write(post['description'])
                        tqdm.write(f"        Description saved (API fallback): {description_filename}")
            if post.get('content'):
                content_filename = f"{post_idx}. {lesson_name}_content.html"
                content_path = chapter_dir / content_filename
                with open(content_path, 'w', encoding='utf-8') as f:
                    f.write(f"<h1>{lesson_name_raw}</h1>\n")
                    f.write(post['content'])
            video_info = post.get('video')
            video_downloaded = False
            
            if video_info:
                video_downloaded = self.download_video_with_retry(video_info, video_path, post_idx, lesson_name)
                if not video_downloaded and post.get('content'):
                    tqdm.write(f"        [*] Video download failed, trying to extract from content...")
                    content = post.get('content')
                    m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', content)
                    if m3u8_urls:
                        tqdm.write(f"        [*] Found m3u8 in content: {m3u8_urls[0][:100]}...")
                        fallback_video_info = {
                            'hlsSrc': m3u8_urls[0],
                            'url': m3u8_urls[0]
                        }
                        video_downloaded = self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
                    else:
                        video_urls = re.findall(r'https?://[^\s"\']+\.(?:mp4|webm|mov)[^\s"\']*', content)
                        if video_urls:
                            tqdm.write(f"        [*] Found video in content: {video_urls[0][:100]}...")
                            fallback_video_info = {
                                'url': video_urls[0]
                            }
                            video_downloaded = self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
            elif post.get('content'):
                content = post.get('content')
                m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', content)
                if m3u8_urls:
                    tqdm.write(f"        [*] Found m3u8 in content: {m3u8_urls[0][:100]}...")
                    fallback_video_info = {
                        'hlsSrc': m3u8_urls[0],
                        'url': m3u8_urls[0]
                    }
                    video_downloaded = self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
                else:
                    video_urls = re.findall(r'https?://[^\s"\']+\.(?:mp4|webm|mov)[^\s"\']*', content)
                    if video_urls:
                        tqdm.write(f"        [*] Found video in content: {video_urls[0][:100]}...")
                        fallback_video_info = {
                            'url': video_urls[0]
                        }
                        video_downloaded = self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
            if not video_downloaded:
                post_str = json.dumps(post, default=str)
                m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', post_str)
                if m3u8_urls:
                    tqdm.write(f"        [*] Found m3u8 in post data: {m3u8_urls[0][:100]}...")
                    fallback_video_info = {'hlsSrc': m3u8_urls[0]}
                    self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
                else:
                    vimeo_urls = re.findall(r'vimeo\.com/(?:video/)?(\d+)', post_str)
                    if vimeo_urls:
                        tqdm.write(f"        [*] Found Vimeo video in post data: {vimeo_urls[0]}...")
                        fallback_video_info = {'link': f'https://vimeo.com/{vimeo_urls[0]}', 'isExternal': True}
                        self.download_video_with_retry(fallback_video_info, video_path, post_idx, lesson_name)
                        
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
            total_lessons = sum(ch.get('numberOfActivePosts', 0) for ch in chapters.values())
            total_duration = sum(ch.get('videoTime', 0) for ch in chapters.values())
            exceeds_limit = any(ch.get('numberOfActivePosts', 0) > self.chapter_limit for ch in chapters.values())
            limit_warning = f" {Colors.RED}[!] Some chapters exceed {self.chapter_limit} lessons{Colors.RESET}" if exceeds_limit else ""
            
            color_print(f"\n[{i}] {course_name}", Colors.GREEN, bold=True)
            color_print(f"    ID: {course_id}", Colors.DIM)
            color_print(f"    Chapters: {num_chapters}", Colors.WHITE)
            color_print(f"    Total Lessons: {total_lessons}", Colors.WHITE)
            color_print(f"    Total Duration: {self.format_time(total_duration)}", Colors.WHITE)
            if exceeds_limit:
                color_print(f"    {limit_warning}", Colors.RED)
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
        self.download_course_thumbnail(course_info, course_dir)
        self.create_course_description_file(course_info, course_dir)
        self.create_credits_file(course_dir)
        progress.update(course=course_title[:60])
        with open(course_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(f"# {course_info.get('name', 'Course')}\n\n")
            f.write(f"## Description\n\n{course_info.get('description', 'No description')}\n\n")
            f.write(f"## Course Info\n\n")
            f.write(f"- **ID**: {course_info.get('id')}\n")
            f.write(f"- **Dump Date**: {datetime.now().isoformat()}\n")
            f.write(f"- **Chapter Limit**: {self.chapter_limit}\n")
            f.write(f"- **Download Until Limit**: {self.download_until_limit}\n")
        chapters = course_info.get('chapters', {})
        
        if not chapters:
            color_print("  [!] No chapters found", Colors.RED)
            return
        total_lessons = sum(ch.get('numberOfActivePosts', 0) for ch in chapters.values())
        total_duration = sum(ch.get('videoTime', 0) for ch in chapters.values())
        
        color_print(f"  [+] Chapters: {len(chapters)}", Colors.CYAN)
        color_print(f"  [+] Total lessons: {total_lessons}", Colors.CYAN)
        color_print(f"  [+] Total duration: {self.format_time(total_duration)}", Colors.CYAN)
        sorted_chapters = sorted(chapters.items(), key=lambda x: x[1].get('priority', 999))
        total_lessons_to_download = 0
        for chapter_id, chapter_info in sorted_chapters:
            if self.download_until_limit or chapter_info.get('numberOfActivePosts', 0) <= self.chapter_limit:
                total_lessons_to_download += min(chapter_info.get('numberOfActivePosts', 0), self.chapter_limit)
        progress.pbar = tqdm(total=total_lessons_to_download, desc="Overall Progress", unit="lesson", position=0, leave=True)
        
        for idx, (chapter_id, chapter_info) in enumerate(sorted_chapters, 1):
            try:
                num_posts = chapter_info.get('numberOfActivePosts', 0)
                if num_posts > self.chapter_limit and not self.download_until_limit:
                    tqdm.write(f"\n  [!] Chapter '{chapter_info.get('name', f'Chapter_{idx}')}' has {num_posts} lessons - Skipping (limit: {self.chapter_limit})")
                    continue
                self.dump_chapter(course_info['id'], chapter_info, course_dir, idx)
                lessons_downloaded = min(num_posts, self.chapter_limit) if self.download_until_limit else num_posts
                progress.pbar.update(lessons_downloaded)
                
            except Exception as e:
                tqdm.write(f"  [!] Error dumping chapter: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(self.config.get("chapter_delay", 1))
        
        progress.pbar.close()
        progress.pbar = None
        self.close_playwright()
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
        self.close_playwright()


def main():
    print_banner()
    import argparse
    
    parser = argparse.ArgumentParser(description='Dump courses from mymemberspot.de')
    parser.add_argument('--email', '-e', required=True, help='Login email')
    parser.add_argument('--password', '-p', required=True, help='Login password')
    parser.add_argument('--output', '-o', default='downloads', help='Output directory')
    parser.add_argument('--course-id', help='Dump only specific course ID')
    parser.add_argument('--config', '-c', default='config.json', help='Config file path')
    parser.add_argument('--list', '-l', action='store_true', help='List all courses with stats and exit')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
    parser.add_argument('--no-playwright', action='store_true', help='Disable Playwright (use only simple HTTP requests)')
    parser.add_argument('--headless', action='store_true', help='Run Playwright in headless mode (no browser window)')
    parser.add_argument('--no-headless', action='store_true', help='Run Playwright with visible browser window')
    
    args = parser.parse_args()
    config = {}
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
    config['debug'] = args.debug
    if args.no_playwright:
        config['use_playwright'] = False
    if args.headless:
        config['playwright_headless'] = True
    if args.no_headless:
        config['playwright_headless'] = False
    with open(args.config, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
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
