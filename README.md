# PornHub Downloader (phdler) - Improved version
## I Reposted This REPO thanks for this 
https://github.com/mariosemes/PornHub-downloader-python
## Thanks To
YouTube-DL
PrettyTables
BS4 aka BeautifulSoup4
mariosemes
## 🆕 Key improvements (404 error resolution)

### 1. **Enhanced HTTP Header**
- User-Agent Auto Settings (Latest Chrome)
- Add Referer Header
- Accept header optimization

### 2. **Enhance retry logic**
- Socket timeout: 30 seconds
- Full retries: 15 times
- Retry fragment: 15 times
- Extrater retries: 5 times

### 3. **Cookie support**
- Automatic detection of 'cookies.txt' files
- Keep login session

### 4. **FFmpeg Downloader**
- Automatic detection and use of FFmpeg
- Improved reliability of downloading HLS streams

### 5. **Error handling improvements**
- Detailed error messages
- Auto-guidance for workarounds

## 📦 Installation

```bash
# 1. Update to the latest version of yt-dlp
pip install -U yt-dlp

# 2. Installation of required packages
pip install requests beautifulsoup4 lxml prettytable

# 3. Install FFmpeg (optional, recommended)
# Windows: https://ffmpeg.org/download.html
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## 🔧 404 Error Resolution Method

### Method 1: yt-dlp update (first try)
```bash
pip install -U yt-dlp
```

### Method 2: Use cookie files (very effective)

1. **Install Chrome extensions**
   - "Get cookies.txt LOCALLY" 설치
   - https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. **Create cookie files**
   ```
   1. Log in to PornHub
   2. Click an extension
   3. Click the "Export" button
   4. Download cookies.txt
   ```

3. **Place cookie files**
   ```
   Save cookies.txt to a folder such as phdler.py
   
   Project Folder/
   ├── phdler.py
   ├── functions.py
   ├── resume_manager.py
   └-- cookies.txt ← Save it here
   ```

### Method 3: Using VPN
```bash
# If area blocking is the cause
# Turn on VPN and try again
```

### Method 4: Install FFmpeg
```bash
# If you have FFmpeg, it will be used automatically
# Windows: Download from https://ffmpeg.org/download.html
```

## 💻 How to use it

### basic command

```bash
# 1. Resume download directly to URL
python phdler.py resume "https://www.pornhub.com/model/shio0721"

# 2. Check Download Status
python phdler.py check "https://www.pornhub.com/model/shio0721"

# 3. Check the status of certain directories
python phdler.py status "C:\Users\SlientServer\Downloads\D\model\shio0721"

# 4. Help
python phdler.py help
```

### Advanced Use

```bash
# Custom Downloads
python phdler.py custom "https://www.pornhub.com/model/username"

# Adding to the database
python phdler.py add "https://www.pornhub.com/model/username"

# View List
python phdler.py list model
python phdler.py list all

# Delete
python phdler.py delete model
```

## 🚨 Troubleshooting

### Problem: HTTP Error 404
```
[download] Got error: HTTP Error 404: Not Found. Retrying fragment 1 (1/10)...
```

**Solution:**:
1. yt-dlp update
2. Creating and Using Cookies.txt
3. Using VPNs
4. Installing FFmpeg

### Problem: Unable to get playlist information
```
Unable to get ⚠️ playlist information.
```

**Solution:**:
1. Turn on VPN
2. Using cookies.txt
3. Enter the total number manually

### Problem: Download is too slow

**Solution:**:
Remove annotations from functions.py in the following line:
```python
# 'ratelimit': 5000000,  # 5MB/s
```

### Problem: SSL Certificate Error

Already resolved:
```python
'nocheckcertificate': True
```

## 📊 Track download progress

The improved version tracks:
- '.ytdl' metadata file (most reliable)
- Video files greater than 100 KB
- '.download_info.json' (download session information)

## 🔍 New Features

### 1. Automatic URL parsing
```bash
# Now extract type and name automatically
python phdler.py resume "https://www.pornhub.com/model/shio0721"

# Manual designation is also possible
python phdler.py resume "https://www.pornhub.com/model/shio0721" model shio0721
```

### 2. Detailed progress
```
✓ Downloaded Videos: 15

Recent Download Videos:
  1. 動画タイトル1...
  2. 動画タイトル2...
  ...
📊 Download progress: 15/59 (25.4%)
   Missing video: 44
```

### 3. Automatic cookie detection
```
Using ✓ cookie file: cookies.txt
```

### 4. Enable FFmpeg automatically
```
✓ Enable FFmpeg Downloader
```

## 📝 Configuration File

### cookies.txt format
The browser extension automatically creates it.
No manual creation required.

### database.db
Automatically create SQLite databases

### .download_info.json
Metadata generated in each download folder

## ⚙️ Advanced Settings

### Using proxies
From the 'get_ytdlp_options()' function of 'functions.py ':
```python
# Tor Proxy Example
'proxy': 'socks5://127.0.0.1:9050',
```

### Download speed limit
```python
'ratelimit': 5000000,  # 5MB/s
```

### Adjust Retry Count
```python
'retries': 15, # Full retry
'Fragment_retries': 15, # Retry Fragment
'extractor_retries': 5,  # Extractor 재시도
```

## 🎯 Performance Optimization Tips

1. **Install FFFmpeg** - Improved reliability of downloading HLS streams
2. **Use cookies** - Prevent blocking by maintaining login sessions
3. **VPN** - Regional Restrictions bypass
4. **Update** - regularly updated yt-dlp

## 🐛 Bug Report

If a problem occurs, the report includes the following information:
- The entire error message
- Commands Used
- yt-dlp 버전: `yt-dlp --version`
- Python 버전: `python --version`
- OS: Windows/Mac/Linux

## 📜 License

Follow the license of the original project.

## 🙏 Contribute

Any suggestions for improvements are welcome!
