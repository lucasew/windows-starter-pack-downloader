#!/usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
import re
from urllib.request import urlopen, Request, urlretrieve
import shutil
import tempfile
import zipfile
import json

parser = ArgumentParser()
parser.add_argument("output_dir", type=Path)

def open_request(request):
    # downloads.rclone.org rejects the default Python-urllib user agent.
    if isinstance(request, str):
        request = Request(request, headers={"User-Agent": "Mozilla/5.0"})
    elif request.get_header("User-agent") is None:
        request.add_header("User-Agent", "Mozilla/5.0")
    return urlopen(request)


def download_to(request, output_dir, filename=None, hops=0):
    res = open_request(request)
    print(f"Downloading {res.url}...")

    # get.videolan.org answers 200 text/html with a meta refresh to a mirror.
    if res.headers.get_content_type() == "text/html":
        if hops >= 2:
            raise RuntimeError(f"HTML response from {res.url}")
        page = res.read().decode("utf-8", "replace")
        match = re.search(r"URL=['\"](https?://[^'\"]+)['\"]", page, re.I)
        if match is None:
            raise RuntimeError(f"no download URL in {res.url}")
        return download_to(match.group(1), output_dir, filename=filename, hops=hops + 1)

    file_path = output_dir
    if filename is None:
        file_path = file_path / res.url.split("/")[-1]
    else:
        file_path = file_path / filename
    with open(str(file_path), 'wb') as f:
        while True:
            chunk = res.read(16*1024)
            if not chunk:
                break
            f.write(chunk)
    return file_path


def webcat(request):
    res = open_request(request)
    print(f"Fetching {res.url}...")
    data = b''
    while True:
        chunk = res.read(4096)
        if not chunk:
            break
        data += chunk
    return data.decode('utf-8')


def download_zip_and_extract_to_bin(work_dir, url, zip_filename, file_filter):
    bin_dir = work_dir / "root" / "bin"
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        downloaded_zip = download_to(url, tempdir, filename=zip_filename)
        with zipfile.ZipFile(downloaded_zip, 'r') as z:
            for file_path_str in z.namelist():
                if file_filter(file_path_str):
                    z.extract(file_path_str, tempdir)
                    extracted_file = tempdir / file_path_str
                    if not extracted_file.is_dir():
                        shutil.move(extracted_file, bin_dir)


def is_rclone_exe(filename):
    return filename.endswith("rclone.exe")

def is_ffmpeg_bin(filename):
    return "/bin/" in filename

def is_executable(filename):
    return filename.endswith(".exe")

args = parser.parse_args()

for d in [args.output_dir / "root" / "Program Files", args.output_dir / "root" / "bin"]:
    d.mkdir(parents=True, exist_ok=True)

# copy skeleton to output

work_dir = args.output_dir / "windows10_postinstall"
assert not work_dir.exists(), "Work dir is not empty"
skeleton_dir = Path(__file__).parent / "skeleton"

shutil.copytree(skeleton_dir, work_dir)

# vlc
vlc_page_content = webcat("https://www.videolan.org/vlc/releases/")
regex = r"vlc\/releases/(.*)\.html"
last_version = next(re.finditer(regex, vlc_page_content)).groups()[0]
final_url = f"https://get.videolan.org/vlc/{last_version}/win64/vlc-{last_version}-win64.exe"
download_to(final_url, work_dir)

# 7zip
sevenzip_page_content = webcat("https://www.7-zip.org/")
regex = r"https://github\.com/ip7z/7zip/releases/download/[^\"']+-x64\.exe"
final_url = next(re.finditer(regex, sevenzip_page_content)).group(0)
download_to(final_url, work_dir, filename="7z.exe")

# adwcleaner
download_to("https://adwcleaner.malwarebytes.com/adwcleaner?channel=release", work_dir, filename="adwcleaner.exe")

# rclone
download_zip_and_extract_to_bin(work_dir, "https://downloads.rclone.org/rclone-current-windows-amd64.zip", "rclone.zip", is_rclone_exe)

# yt-dlp
github_release = json.loads(webcat("https://api.github.com/repos/yt-dlp/yt-dlp/releases"))[0] # primeira
for asset in github_release['assets']:
    if asset['name'] != "yt-dlp.exe":
        continue
    download_to(asset['browser_download_url'], work_dir / "root" / "bin", filename="yt-dlp.exe")

# ffmpeg
download_zip_and_extract_to_bin(work_dir, "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", "ffmpeg.zip", is_ffmpeg_bin)

# geek uninstaller
download_zip_and_extract_to_bin(work_dir, "https://geekuninstaller.com/geek.zip", "geek.zip", is_executable)

# aria2
github_release = json.loads(webcat("https://api.github.com/repos/aria2/aria2/releases"))[0] # primeira
for asset in github_release['assets']:
    if "win-64bit" in asset['name']:
        download_zip_and_extract_to_bin(work_dir, asset['browser_download_url'], "aria2.zip", is_executable)


# Windows Update Blocker
with tempfile.TemporaryDirectory(prefix='download_wub') as tempdir:
    tempdir = Path(tempdir)
    downloaded_zip = download_to("https://www.sordum.org/files/downloads.php?st-windows-update-blocker", tempdir, "wub.zip")
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        z.extractall(tempdir)
    shutil.move(tempdir / "Wub", work_dir / "root" / "Program Files")
