#!/usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
import re
from urllib.request import urlopen, Request, urlretrieve
import shutil
import tempfile
import zipfile
import ssl
import json

parser = ArgumentParser()
parser.add_argument("output_dir", type=Path)

context = ssl.create_default_context()

def download_to(request, output_dir, filename=None):
    res = urlopen(request, context=context)
    print(f"Downloading {res.url}...")

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
    res = urlopen(request)
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
regex = r"(a\/.*x64\.exe)"
url_part = next(re.finditer(regex, sevenzip_page_content)).groups()[0]
final_url = "https://www.7-zip.org/" + url_part
sevenzip_filename = url_part.split("/")[-1]
download_to(final_url, work_dir, filename=sevenzip_filename)

# adwcleaner
download_to("https://adwcleaner.malwarebytes.com/adwcleaner?channel=release", work_dir, filename="adwcleaner.exe")

# rclone
download_zip_and_extract_to_bin(work_dir, "https://downloads.rclone.org/rclone-current-windows-amd64.zip", "rclone.zip", lambda f: f.endswith("rclone.exe"))

# yt-dlp
github_release = json.loads(webcat("https://api.github.com/repos/yt-dlp/yt-dlp/releases"))[0] # primeira
for asset in github_release['assets']:
    if asset['name'] != "yt-dlp.exe":
        continue
    download_to(asset['browser_download_url'], work_dir / "root" / "bin", filename="yt-dlp.exe")

# ffmpeg
download_zip_and_extract_to_bin(work_dir, "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", "ffmpeg.zip", lambda f: "/bin/" in f)

# geek uninstaller
download_zip_and_extract_to_bin(work_dir, "https://geekuninstaller.com/geek.zip", "geek.zip", lambda f: f.endswith(".exe"))

# aria2
github_release = json.loads(webcat("https://api.github.com/repos/aria2/aria2/releases"))[0] # primeira
for asset in github_release['assets']:
    if "win-64bit" in asset['name']:
        download_zip_and_extract_to_bin(work_dir, asset['browser_download_url'], "aria2.zip", lambda f: f.endswith(".exe"))


# Windows Update Blocker
with tempfile.TemporaryDirectory(prefix='download_wub') as tempdir:
    tempdir = Path(tempdir)
    downloaded_zip = download_to("https://www.sordum.org/files/downloads.php?st-windows-update-blocker", tempdir, "wub.zip")
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        z.extractall(tempdir)
    shutil.move(tempdir / "Wub", work_dir / "root" / "Program Files")
