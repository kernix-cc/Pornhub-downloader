#!/usr/bin/env python
import yt_dlp
import requests
import sys
import urllib.parse as urlparse
import sqlite3
import os
from prettytable import PrettyTable
from sqlite3 import Error
from urllib import request
from bs4 import BeautifulSoup

# Database location
database = "./database.db"
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'model')

# Safeguard: reject paths containing system user folders (venv protection)
SYSTEM_USER_PATHS = [
    r'C:\Users\User',
    r'C:\Users\SlientServer\Downloads\PornHub',
    '/root',
]

def is_system_restricted_path(path):
    """Check if path is in a restricted location (system folder from old setup)."""
    if not path:
        return True
    norm_path = os.path.normpath(path).lower()
    for restricted in SYSTEM_USER_PATHS:
        if restricted.lower() in norm_path:
            return True
    return False


# IMPROVED: 고급 yt-dlp 옵션 생성 함수
def get_ytdlp_options(outtmpl, start_video=1, end_video=None, use_cookies=False):
    """
    404 에러 해결을 위한 강화된 yt-dlp 옵션
    
    Args:
        outtmpl: 출력 템플릿
        start_video: 시작 비디오 번호
        end_video: 종료 비디오 번호 (None이면 끝까지)
        use_cookies: 쿠키 사용 여부
    
    Returns:
        dict: yt-dlp 옵션
    """
    options = {
        'format': 'best',
        'outtmpl': outtmpl,
        'nooverwrites': True,
        'no_warnings': False,
        'ignoreerrors': True,
        'continue_dl': True,
        
        # 404 에러 해결을 위한 핵심 설정
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Referer': 'https://www.pornhub.com/',
        },
        
        # 재시도 로직 강화
        'socket_timeout': 30,
        'retries': 15,
        'fragment_retries': 15,
        'extractor_retries': 5,
        'skip_unavailable_fragments': False,
        
        # SSL 인증서 검증 비활성화 (일부 네트워크 환경에서 필요)
        'nocheckcertificate': True,
        
        # 다운로드 속도 제한 (너무 빠르면 차단될 수 있음)
        # 'ratelimit': 5000000,  # 5MB/s (필요시 주석 해제)
        
        # 프록시 설정 (필요시 사용)
        # 'proxy': 'socks5://127.0.0.1:9050',  # Tor 프록시 예시
    }
    
    # 플레이리스트 범위 설정
    if start_video:
        options['playliststart'] = start_video
    if end_video:
        options['playlistend'] = end_video
    
    # 쿠키 파일 사용 (존재하는 경우)
    cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if use_cookies and os.path.exists(cookies_path):
        options['cookiefile'] = cookies_path
        print(f"✓ 쿠키 파일 사용: {cookies_path}")
    
    # FFmpeg 다운로더 사용 (설치되어 있는 경우)
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=3)
        if result.returncode == 0:
            options['external_downloader'] = 'ffmpeg'
            options['external_downloader_args'] = ['-loglevel', 'error']
            print("✓ FFmpeg 다운로더 활성화")
    except:
        pass
    
    return options


# CHECKINGS
def type_check(item):
    if item == "model":
        print("Valid type (model) selected.")
    elif item == "pornstar":
        print("Valid type (pornstar) selected.")
    elif item == "channels":
        print("Valid type (channel) selected.")
    elif item == "users":
        print("Valid type (user) selected.")
    elif item == "playlist":
        print("Valid type (playlist) selected.")
    elif item == "all":
        print("Valid type (all) selected.")
    else:
        how_to_use("Not a valid type.")
        sys.exit()


def ph_url_check(url):
    parsed = urlparse.urlparse(url)
    regions = ["www", "cn", "cz", "de", "es", "fr", "it", "nl", "jp", "pt", "pl", "rt"]
    for region in regions:
        if parsed.netloc == region + ".pornhub.com":
            print("PornHub url validated.")
            return
    print("This is not a PornHub url.")
    sys.exit()


def ph_type_check(url):
    parsed = urlparse.urlparse(url)
    if parsed.path.split('/')[1] == "model":
        print("This is a MODEL url,")
    elif parsed.path.split('/')[1] == "pornstar":
        print("This is a PORNSTAR url,")
    elif parsed.path.split('/')[1] == "channels":
        print("This is a CHANNEL url,")
    elif parsed.path.split('/')[1] == "users":
        print("This is a USER url,")
    elif parsed.path.split('/')[1] == "playlist":
        print("This is a PLAYLIST url,")
    elif parsed.path.split('/')[1] == "view_video.php":
        print("This is a VIDEO url. Please paste a model/pornstar/user/channel/playlist url.")
        sys.exit()
    else:
        print("Somethings wrong with the url. Please check it out.")
        sys.exit()


def ph_alive_check(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        requested = requests.get(url, headers=headers, timeout=10)
        if requested.status_code == 200:
            print("and the URL is existing.")
        else:
            print("but the URL does not exist.")
            sys.exit()
    except Exception as e:
        print(f"URL 확인 중 오류: {e}")
        sys.exit()


def add_check(name_check):
    if name_check == "batch":
        u_input = input("Please enter full path to the batch-file.txt (or c to cancel): ")
        if u_input == "c":
            print("Operation canceled.")
        else:
            with open(u_input, 'r') as input_file:
                for line in input_file:
                    line = line.strip()
                    add_item(line)

    else:
        add_item(name_check)


def get_item_name(item_type, url_item):
    url = url_item
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = request.Request(url, headers=headers)
    html = request.urlopen(req).read().decode('utf8')
    soup = BeautifulSoup(html, 'lxml')

    if item_type == "model":
        finder = soup.find(class_='nameSubscribe')
        title = finder.find(itemprop='name').text.replace('\n', '').strip()
    elif item_type == "pornstar":
        finder = soup.find(class_='nameSubscribe')
        title = finder.find(class_='name').text.replace('\n', '').strip()
    elif item_type == "channels":
        finder = soup.find(class_='bottomExtendedWrapper')
        title = finder.find(class_='title').text.replace('\n', '').strip()
    elif item_type == "users":
        finder = soup.find(class_='bottomInfoContainer')
        title = finder.find('a', class_='float-left').text.replace('\n', '').strip()
    elif item_type == "playlist":
        finder = soup.find(id='playlistTopHeader')
        title = finder.find(id='watchPlaylist').text.replace('\n', '').strip()
    else:
        print("No valid item type.")
        title = False

    return title


##################################### DOWNLOADING


def dl_all_items(conn):
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM ph_items")
    except Error as e:
        print(e)
        sys.exit()

    rows = c.fetchall()

    for row in rows:
        if row[1] == "model":
            url_after = "/videos/upload"
        elif row[1] == "users":
            url_after = "/videos/public"
        elif row[1] == "channels":
            url_after = "/videos"
        else:
            url_after = ""

        print("-----------------------------")
        print(row[1])
        print(row[2])
        print("https://www.pornhub.com/" + str(row[1]) + "/" + str(row[2]) + url_after)
        print("-----------------------------")

        outtmpl = os.path.normpath(os.path.join(get_dl_location('DownloadLocation'), str(row[1]), str(row[3]), '%(title)s.%(ext)s'))
        
        # 개선된 옵션 사용
        ydl_opts_start = get_ytdlp_options(outtmpl, start_video=1, end_video=4)

        url = "https://www.pornhub.com/" + str(row[1]) + "/" + str(row[2] + url_after)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_start) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"다운로드 오류: {e}")
            print("다음 항목으로 계속...")

        try:
            c.execute("UPDATE ph_items SET lastchecked=CURRENT_TIMESTAMP WHERE url_name = ?", (row[2],))
            conn.commit()
        except Error as e:
            print(e)
            sys.exit()


def dl_all_new_items(conn):
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM ph_items WHERE new='1'")
    except Error as e:
        print(e)
        sys.exit()

    rows = c.fetchall()

    for row in rows:

        if str(row[1]) == "model":
            url_after = "/videos/upload"
        elif str(row[1]) == "users":
            url_after = "/videos/public"
        elif str(row[1]) == "channels":
            url_after = "/videos"
        else:
            url_after = ""

        print("-----------------------------")
        print(row[1])
        print(row[2])
        print("https://www.pornhub.com/" + str(row[1]) + "/" + str(row[2]) + url_after)
        print("-----------------------------")

        outtmpl = os.path.normpath(os.path.join(get_dl_location('DownloadLocation'), str(row[1]), str(row[3]), '%(title)s.%(ext)s'))
        
        # 개선된 옵션 사용
        ydl_opts = get_ytdlp_options(outtmpl)

        url = "https://www.pornhub.com/" + str(row[1]) + "/" + str(row[2]) + url_after
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"다운로드 오류: {e}")
            print("다음 항목으로 계속...")

        try:
            c.execute("UPDATE ph_items SET new='0' WHERE url_name = ?", (row[2],))
            c.execute("UPDATE ph_items SET lastchecked=CURRENT_TIMESTAMP WHERE url_name = ?", (row[2],))
            conn.commit()
        except Error as e:
            print(e)


def custom_dl(url):
    ph_url_check(url)
    ph_type_check(url)
    ph_alive_check(url)
    print("Downloading...")
    
    outtmpl = os.path.normpath(os.path.join(get_dl_location('DownloadLocation'), 'custom', '%(title)s.%(ext)s'))
    
    # 개선된 옵션 사용
    ydl_opts = get_ytdlp_options(outtmpl)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n✓ 다운로드 완료!")
    except Exception as e:
        print(f"\n✗ 다운로드 오류: {e}")
        print("\n해결 방법:")
        print("1. yt-dlp 업데이트: pip install -U yt-dlp")
        print("2. 쿠키 파일 사용: 브라우저에서 로그인 후 cookies.txt 생성")
        print("3. VPN 또는 프록시 사용")


def dl_start():
    conn = create_connection(database)
    u_input = input("Do you want to download new items only (n) OR all items (a)? ")
    if u_input == "n":
        print("Downloading new items only...")
        dl_all_new_items(conn)
    elif u_input == "a":
        print("Downloading all items...")
        dl_all_items(conn)
    else:
        print("Not an accepted answer. Try again.")


##################################### Database

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn


def add_item(url):
    ph_url_check(url)
    ph_type_check(url)
    ph_alive_check(url)
    parsed = urlparse.urlparse(url)
    item_type = parsed.path.split('/')[1]
    url_name = parsed.path.split('/')[2]
    name = get_item_name(item_type, url)
    print("adding " + name + " to database.")
    conn = create_connection(database)
    with conn:
        item = (item_type, url_name, name, 1)
        create_item(conn, item)


def create_item(conn, item):
    sql = ''' INSERT INTO ph_items(type, url_name, name, new)
              VALUES(?,?,?,?) '''
    c = conn.cursor()
    c.execute(sql, item)
    return c.lastrowid


def select_all_items(conn, item):
    c = conn.cursor()
    if item == "all":
        c.execute("SELECT * FROM ph_items")
    else:
        c.execute("SELECT * FROM ph_items WHERE type='" + item + "'")

    rows = c.fetchall()

    t = PrettyTable(['Id.', 'Name', 'Type', 'Date created', 'Last checked', 'Url'])
    t.align['Id.'] = "l"
    t.align['Name'] = "l"
    t.align['Type'] = "l"
    t.align['Date created'] = "l"
    t.align['Last checked'] = "l"
    t.align['Url'] = "l"
    for row in rows:
        url = "https://www.pornhub.com/" + str(row[1]) + "/" + str(row[2])
        t.add_row([row[0], row[3], row[1], row[5], row[6], url])
    print(t)


def list_items(item):
    conn = create_connection(database)
    with conn:
        print("Listing items from database:")
        select_all_items(conn, item)


def delete_single_item(conn, id):
    sql = 'DELETE FROM ph_items WHERE id=?'
    c = conn.cursor()
    c.execute(sql, (id,))
    conn.commit()


def delete_item(item_id):
    conn = create_connection(database)
    with conn:
        delete_single_item(conn, item_id)


def create_config(conn, item):
    sql = ''' INSERT INTO ph_settings(option, setting)
              VALUES(?,?) '''
    c = conn.cursor()
    c.execute(sql, item)
    return c.lastrowid


def prepare_config():
    conn = create_connection(database)
    default = os.path.normpath(DEFAULT_DOWNLOAD_DIR)
    prompt = f"Please enter the FULL PATH to your download location (leave empty for default: {default}): "
    u_input = input(prompt)
    if not u_input:
        u_input = default
    u_input = os.path.normpath(u_input)
    try:
        os.makedirs(u_input, exist_ok=True)
    except Exception:
        pass
    with conn:
        c = conn.cursor()
        c.execute("SELECT id FROM ph_settings WHERE option='DownloadLocation'")
        if c.fetchone():
            c.execute("UPDATE ph_settings SET setting=? WHERE option='DownloadLocation'", (u_input,))
        else:
            item = ('DownloadLocation', u_input)
            create_config(conn, item)


def ensure_default_download_location():
    """Ensure a DownloadLocation setting exists in the DB; insert project-local default if missing or restricted."""
    conn = create_connection(database)
    if conn is None:
        return os.path.normpath(DEFAULT_DOWNLOAD_DIR)
    c = conn.cursor()
    c.execute("SELECT * FROM ph_settings WHERE option='DownloadLocation'")
    rows = c.fetchall()
    if not rows:
        dll = os.path.normpath(DEFAULT_DOWNLOAD_DIR)
        try:
            os.makedirs(dll, exist_ok=True)
        except Exception:
            pass
        with conn:
            item = ('DownloadLocation', dll)
            create_config(conn, item)
        return dll
    else:
        for row in rows:
            stored_path = row[2]
            norm_path = os.path.normpath(stored_path) if stored_path else None
            # If stored path is in system folder (from old setup), replace it with default
            if is_system_restricted_path(norm_path):
                dll = os.path.normpath(DEFAULT_DOWNLOAD_DIR)
                try:
                    os.makedirs(dll, exist_ok=True)
                except Exception:
                    pass
                with conn:
                    c = conn.cursor()
                    c.execute("UPDATE ph_settings SET setting=? WHERE option='DownloadLocation'", (dll,))
                    conn.commit()
                return dll
            return norm_path


def get_dl_location(option):
    conn = create_connection(database)
    if conn is not None:
        c = conn.cursor()
        c.execute("SELECT * FROM ph_settings WHERE option=?", (option,))
        rows = c.fetchall()
        if rows:
            for row in rows:
                dllocation = row[2]
                norm_path = os.path.normpath(dllocation) if dllocation else None
                # Safeguard: reject system user paths (venv protection)
                if is_system_restricted_path(norm_path):
                    return ensure_default_download_location()
                return norm_path
        return ensure_default_download_location()
    else:
        return os.path.normpath(DEFAULT_DOWNLOAD_DIR)


def check_for_database():
    print("Running startup checks...")
    if os.path.exists(database):
        print("Database exists.")
    else:
        print("Database does not exist.")
        print("Looks like this is your first time run...")
        first_run()


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print("Tables created.")
    except Error as e:
        print(e)


def create_tables():
    sql_create_items_table = """ CREATE TABLE IF NOT EXISTS ph_items (
                                        id integer PRIMARY KEY,
                                        type text,
                                        url_name text,
                                        name text,
                                        new integer DEFAULT 1,
                                        datecreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                                        lastchecked DATETIME DEFAULT CURRENT_TIMESTAMP
                                    ); """

    sql_create_settings_table = """ CREATE TABLE IF NOT EXISTS ph_settings (
                                        id integer PRIMARY KEY,
                                        option text,
                                        setting text,
                                        datecreated DATETIME DEFAULT CURRENT_TIMESTAMP
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create items table
        create_table(conn, sql_create_items_table)
        create_table(conn, sql_create_settings_table)
        # Ensure a sane default DownloadLocation is present to avoid permission issues inside venv
        ensure_default_download_location()
    else:
        print("Error! cannot create the database connection.")


##################################### Lets do it baby

def first_run():
    create_tables()


##################################### MESSAGING


def how_to_use(error):
    print("Error: " + error)
    print("Please use the tool like this:")
    t = PrettyTable(['Tool', 'command', 'item'])
    t.align['Tool'] = "l"
    t.align['command'] = "l"
    t.align['item'] = "l"
    t.add_row(['phdler', 'start', ''])
    t.add_row(['phdler', 'custom', 'url (full PornHub url) | batch (for .txt file)'])
    t.add_row(['phdler', 'add', 'model | pornstar | channel | user | playlist | batch (for .txt file)'])
    t.add_row(['phdler', 'list', 'model | pornstar | channel | user | playlist | all'])
    t.add_row(['phdler', 'delete', 'model | pornstar | channel | user | playlist'])
    t.add_row(['phdler', 'check', 'url (auto-parse) OR url type name'])
    t.add_row(['phdler', 'resume', 'url (auto-parse) OR url type name'])
    t.add_row(['phdler', 'status', 'directory (show download status)'])
    print(t)


def help_command():
    print("------------------------------------------------------------------")
    print("You asked for help, here it comes! Run phdler with these commands:")
    t = PrettyTable(['Command', 'argument', 'description'])
    t.align['Command'] = "l"
    t.align['argument'] = "l"
    t.align['description'] = "l"
    t.add_row(['start', '', 'start the script'])
    t.add_row(['custom', 'url | batch', 'download a single video from PornHub'])
    t.add_row(
        ['add', 'model | pornstar | channel | user | playlist | batch (for .txt file)', 'adding item to database'])
    t.add_row(['list', 'model | pornstar | channel | user | playlist', 'list selected items from database'])
    t.add_row(['delete', 'model | pornstar | channel | user | playlist', 'delete selected items from database'])
    t.add_row(['check', 'url (auto-parse) OR url type name', 'check which videos are downloaded/missing'])
    t.add_row(['resume', 'url (auto-parse) OR url type name', 'resume downloading missing videos from playlist'])
    t.add_row(['status', 'directory_path', 'show download status for a directory'])
    print(t)
    print("\n📝 쿠키 파일 사용법:")
    print("  1. 브라우저에서 'Get cookies.txt LOCALLY' 확장 프로그램 설치")
    print("  2. PornHub 로그인 후 cookies.txt 다운로드")
    print("  3. cookies.txt를 phdler.py와 같은 폴더에 저장")
    print("\n💡 404 에러 해결:")
    print("  1. yt-dlp 업데이트: pip install -U yt-dlp")
    print("  2. FFmpeg 설치 권장: https://ffmpeg.org/download.html")
    print("  3. VPN 사용 또는 쿠키 파일 준비")
    print("------------------------------------------------------------------")
