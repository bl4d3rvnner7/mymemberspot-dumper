![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=blue)
![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge)
![Dependencies](https://img.shields.io/badge/Dependencies-yt--dlp%20%7C%20requests%20%7C%20brotli%20%7C%20colorama-blue?style=for-the-badge)
![Output](https://img.shields.io/badge/Output-Video%20%7C%20Transcript%20%7C%20PDF-orange?style=for-the-badge)
![Tested](https://img.shields.io/badge/Tested-Multiple%20Courses-brightgreen?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet?style=for-the-badge)

![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/mymemberspot-dumper?style=for-the-badge)
![GitHub Forks](https://img.shields.io/github/forks/YOUR_USERNAME/mymemberspot-dumper?style=for-the-badge)
![GitHub Issues](https://img.shields.io/github/issues/YOUR_USERNAME/mymemberspot-dumper?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/YOUR_USERNAME/mymemberspot-dumper?style=for-the-badge)

---

# 🎓 MyMemberspot Course Dumper [BETA]

**Backup all your courses, videos, PDFs, and learning materials from any mymemberspot.de platform — all in one tool.**  
Supports **all course formats**, **video lessons**, **PDF attachments**, **chapter structures**, and **full metadata preservation**.  
Perfect for offline learning, archiving, or personal backup.

---

## 📑 Table of Contents

- [🎓 MyMemberspot Course Dumper](#-mymemberspot-course-dumper)
- [📑 Table of Contents](#-table-of-contents)
- [🚀 Features](#-features)
- [📦 Requirements](#-requirements)
- [⚙️ Installation](#️-installation)
- [🚀 Usage](#-usage)
  - [Basic Usage](#basic-usage)
  - [Dump Specific Course](#dump-specific-course)
  - [Custom Output Directory](#custom-output-directory)
  - [Custom Config File](#custom-config-file)
- [📁 Output Overview](#-output-overview)
  - [Folder Structure](#folder-structure)
  - [Text File Format](#text-file-format)
  - [Console Output Example](#console-output-example)
- [⚙️ Configuration](#️-configuration)
  - [Configuration Options](#configuration-options)
- [🔑 How to Get Your Config Values](#-how-to-get-your-config-values)
  - [Prerequisites](#prerequisites)
  - [Step 1: Get firebase_api_key](#step-1-get-firebase_api_key)
  - [Step 2: Get tenant_id](#step-2-get-tenant_id)
  - [Step 3: Get school_id](#step-3-get-school_id)
  - [Step 4: Get base_url](#step-4-get-base_url)
  - [Complete Example Configuration](#complete-example-configuration)
  - [Video Tutorial](#video-tutorial)
  - [Troubleshooting Extraction](#troubleshooting-extraction)
  - [Security Note](#security-note)
- [🧠 Internals & How It Works](#-internals--how-it-works)
- [🔧 Troubleshooting](#-troubleshooting)
  - [Common Issues](#common-issues)
  - [Getting Your Config Values (Recap)](#getting-your-config-values-recap)
- [🤝 Contributing](#-contributing)
- [⚠️ Disclaimer](#️-disclaimer)
- [📄 License](#-license)
- [⭐ Support](#-support)
- [🔗 Links](#-links)

---

## 🚀 Features

🔐 **Automatic Authentication** - Login via email/password with Firebase Auth<br>
📚 **Full Course Structure** - Preserves chapters, modules, and lesson hierarchy<br>
🎥 **Video Download** - Downloads HLS streams (.m3u8) using yt-dlp with multi-threading<br>
📎 **Attachment Support** - Downloads all PDFs and file attachments<br>
📝 **Metadata Preservation** - Saves lesson descriptions and content as text files<br>
🎨 **Colored Output** - Beautiful terminal output with progress indicators<br>
⚙️ **Configurable** - Easy configuration via JSON file<br>
🚀 **Multi-threaded** - Fast parallel downloads with yt-dlp (configurable threads)<br>
📁 **Clean Organization** - Automatic folder structure with numbered lessons<br>
🔄 **Resume Support** - Can resume interrupted downloads<br>

---

## 📦 Requirements

```
requests>=2.31.0
yt-dlp>=2023.10.13
brotli>=1.0.9
```

Install them via:

```bash
pip install -r requirements.txt
```

Also requires **ffmpeg** (optional, for fallback) and **yt-dlp** for video downloads.

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/mymemberspot-dumper.git
cd mymemberspot-dumper

# Install dependencies
pip install -r requirements.txt

# Run the tool (first run creates config.json)
python3 dumper.py --email your@email.com --password yourpassword
```

---

## 🚀 Usage

### Basic Usage

```bash
python3 dumper.py --email your@email.com --password yourpassword
```

### Dump Specific Course

```bash
python3 dumper.py --email your@email.com --password yourpassword --course-id COURSE_ID
```

### Custom Output Directory

```bash
python3 dumper.py --email your@email.com --password yourpassword --output /path/to/downloads
```

### Custom Config File

```bash
python3 dumper.py --email your@email.com --password yourpassword --config myconfig.json
```

---

## 📁 Output Overview

### Folder Structure

This tool automatically generates:

| File / Folder                    | Description                              |
| -------------------------------- | ---------------------------------------- |
| `Course Name/`                   | Main course folder                       |
| `├── README.md`                  | Course overview with description         |
| `├── 01_Chapter Name/`           | Chapter folder with numbered prefix      |
| `│   ├── 1. Lesson Name.mp4`     | Video lesson with proper naming          |
| `│   ├── 1. Lesson Name.txt`     | Lesson description as text               |
| `│   ├── 2. Lesson Name.mp4`     | Next video lesson                        |
| `│   ├── 2. Lesson Name.txt`     | Next lesson description                  |
| `│   └── 3. Lesson Name.pdf`     | Attached PDF file                        |
| `└── 02_Another Chapter/`        | Next chapter folder                      |

### Text File Format

Example of a formatted text file (`1. Lesson Name.txt`):

```
Title: Deine Vision
============================================================

Was ist deine Herzensvision? In dieser Lektion lernst du,
wie du deine langfristigen Ziele definierst und visualisierst.
```

### Console Output Example

```
============================================================
[+] Course: Machin Sales Academy
[+] ID: AMRr6sAycprxKDWBpCCx
============================================================
  [+] Chapters: 10
  [+] Total lessons: 373
  [+] Total duration: 427h 8m 22s

  [*] Chapter: 01_Modul 1 | Einführung und Mindset
      Description: Dein Mindset ist der Schlüssel...
      Lessons: 7

    [*] Lesson 1: Herzlich Willkommen - Deine erste Woche!
        📝 Description saved: 1. Herzlich Willkommen - Deine erste Woche!.txt
        [*] Downloading video: 1. Herzlich Willkommen - Deine erste Woche!
        [+] Downloaded: 1. Herzlich Willkommen - Deine erste Woche!.mp4 (15.23 MB)
```

---

## ⚙️ Configuration

The tool creates a `config.json` file on first run with the following structure:

```json
{
  "api_base": "https://client-api.memberspot.de",
  "firebase_api_key": "YOUR_FIREBASE_API_KEY",
  "tenant_id": "YOUR_TENANT_ID",
  "school_id": "YOUR_SCHOOL_ID",
  "base_url": "https://yoursite.mymemberspot.de",
  "app_version": "2026-04-02-2110/server-client-frontend",
  "app": "client",
  "ytdlp_threads": 4,
  "download_delay": 0.3,
  "chapter_delay": 1,
  "course_delay": 2
}
```

### Configuration Options

| Option              | Description                                    | Default |
| ------------------- | ---------------------------------------------- | ------- |
| `api_base`          | Memberspot API endpoint                        | `https://client-api.memberspot.de` |
| `firebase_api_key`  | Firebase API key for authentication            | (provided) |
| `tenant_id`         | Your tenant ID                                 | (provided) |
| `school_id`         | Your school ID                                 | (provided) |
| `base_url`          | Your memberspot site URL                       | (provided) |
| `app_version`       | App version header                             | latest |
| `ytdlp_threads`     | Number of threads for yt-dlp                   | `4` |
| `download_delay`    | Delay between lesson downloads (seconds)       | `0.3` |
| `chapter_delay`     | Delay between chapters (seconds)               | `1` |
| `course_delay`      | Delay between courses (seconds)                | `2` |

---

## 🔑 How to Get Your Config Values

To use this tool, you need to extract some values from your memberspot platform. Follow this step-by-step guide:

### Prerequisites
- A valid account on your memberspot platform
- Browser with Developer Tools (Chrome, Firefox, Edge)

---

### Step 1: Get `firebase_api_key`

1. Open your memberspot login page
2. Press **F12** to open Developer Tools
3. Go to the **Network** tab
4. Enter your email and password, then click **Login**
5. In the Network tab, look for a POST request to:
   ```
   https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=...
   ```
6. Click on this request
7. Look at the **Request URL** - you'll see a parameter `key=`
8. Copy the value after `key=`

**Example:**
```
Request URL: https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyBsOSvyKi9LaUCQQSdFR3e3G_HEJanqDZ0
                                                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                                              This is your firebase_api_key
```

---

### Step 2: Get `tenant_id`

1. Still in the Network tab, find the same login request
2. Click on the **Payload** tab (or Request tab)
3. Look for the field `tenantId` in the request body
4. Copy its value

**Example Request Body:**
```json
{
  "returnSecureToken": true,
  "email": "user@example.com",
  "password": "********",
  "clientType": "CLIENT_TYPE_WEB",
  "tenantId": "s-V57dJFhCLVpklJx7-w7gxj"
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              This is your tenant_id
}
```

---

### Step 3: Get `school_id`

**Method 1 - From URL (After Login):**
1. Complete the login process
2. After successful login, look for a request to:
   ```
   https://client-api.memberspot.de/school-users/user-v2/...
   ```
3. The `school_id` is the value after `user-v2/` in the URL

**Example URL:**
```
https://client-api.memberspot.de/school-users/user-v2/V57dJFhCLVpklJx7Yn8e
                                                      ^^^^^^^^^^^^^^^^^^^^
                                                      This is your school_id
```

**Method 2 - From Response (Easier):**
1. Find the same request in Network tab
2. Click on the **Response** tab
3. Look for the field `schoolId` in the JSON response
4. Copy its value

**Example Response:**
```json
{
  "_id": "...",
  "uid": "...",
  "schoolId": "V57dJFhCLVpklJx7Yn8e",
              ^^^^^^^^^^^^^^^^^^^^
              This is your school_id
  "email": "user@example.com",
  ...
}
```

---

### Step 4: Get `base_url`

This is simply the URL of your memberspot platform:

```
https://<your-domain>.mymemberspot.de/
```

**Examples:**
- `https://machinsalesacademy.mymemberspot.de`
- `https://learningsite.mymemberspot.de`
- `https://academy.mymemberspot.de`

> ⚠️ **Note:** Do not include trailing slashes or paths after the domain

---

### Complete Example Configuration

After gathering all values, your `config.json` should look like this:

```json
{
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
```

### Troubleshooting Extraction

| Problem                          | Solution                                      |
| -------------------------------- | --------------------------------------------- |
| Can't find login request         | Make sure "Preserve log" is checked in Network tab |
| `tenantId` not in request body   | Try clearing cache and logging in again       |
| `schoolId` not found             | Try filtering for `user-v2` or `school-users` |
| Values don't work                | Double-check for typos, especially at the end of strings |
| Multiple tenant IDs found        | Use the one that appears in the login request |

### Security Note

- Your `config.json` contains sensitive values
- **Never share** your config file or commit it to GitHub
- The `.gitignore` file is configured to exclude `config.json`
- Keep your credentials and tokens secure

---

## 🧠 Internals & How It Works

The script:

1. **Authenticates** with Firebase using email/password
2. **Fetches user info** to get all accessible courses
3. **Retrieves course structure** including all chapters
4. **For each chapter**, requests detailed information including all posts
5. **Extracts video URLs** (hlsSrc) from each post's video object
6. **Downloads videos** using yt-dlp with multi-threading support
7. **Saves descriptions** as formatted text files
8. **Downloads attachments** (PDFs, files) from each lesson
9. **Preserves chapter numbers** and lesson numbers in filenames
10. **Creates README.md** with course overview and progress

Everything is handled inside `dumper.py` with color-coded terminal output.

---

## 🔧 Troubleshooting

### Common Issues

| Issue                          | Solution                                      |
| ------------------------------ | --------------------------------------------- |
| Login failed                   | Check email/password and config values       |
| No courses found               | Verify school_id and tenant_id in config     |
| Video download fails           | Ensure yt-dlp is installed and updated       |
| FFmpeg not found               | Install ffmpeg or use yt-dlp only            |
| Decompression errors           | Install brotli: `pip install brotli`         |

### Getting Your Config Values (Recap)

To get your `school_id`, `tenant_id`, and `firebase_api_key`:

1. Open browser DevTools (F12) → Network tab
2. Login to your memberspot site
3. Look for requests to `identitytoolkit.googleapis.com`
4. Extract values from the request payload

---

## 🤝 Contributing

Pull requests are always welcome.
You can add:
- Support for more memberspot platforms
- GUI interface
- Resume functionality for interrupted downloads
- Batch processing for multiple accounts
- Performance improvements

---

## ⚠️ Disclaimer

This tool is for **personal backup purposes only**. Only download content you have legitimate access to and respect copyright laws. The authors are not responsible for any misuse of this tool.

---

## 📄 License

MIT License - see LICENSE file

---

## ⭐ Support

If you like this project, consider leaving a **star** ⭐ on GitHub.
It motivates further updates and improvements.

---

## 🔗 Links

- [Report Bug](https://github.com/YOUR_USERNAME/mymemberspot-dumper/issues)
- [Request Feature](https://github.com/YOUR_USERNAME/mymemberspot-dumper/issues)
- [Documentation](https://github.com/YOUR_USERNAME/mymemberspot-dumper/wiki)
