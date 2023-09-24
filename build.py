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

def download_to(request, output_dir, filename=None):
    res = urlopen(request)
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

args = parser.parse_args()

for d in [args.output_dir / "root" / "Program Files", args.output_dir / "root" / "bin"]:
    d.mkdir(parents=True, exist_ok=True)

# copy skeleton to output

work_dir = args.output_dir / "windows10_postinstall"
assert not work_dir.exists(), "Work dir is not empty"
skeleton_dir = Path(__file__).parent / "skeleton"

shutil.copytree(skeleton_dir, work_dir)

# vlc
with tempfile.TemporaryDirectory(prefix='download_vlc') as tempdir:
    vlc_page_content = webcat("https://www.videolan.org/vlc/releases/")
    regex = r"vlc\/releases/(.*)\.html"
    last_version = next(re.finditer(regex, vlc_page_content)).groups()[0]
    final_url = f"https://get.videolan.org/vlc/{last_version}/win64/vlc-{last_version}-win64.exe"
    download_to(final_url, work_dir)

# 7zip
with tempfile.TemporaryDirectory(prefix='download_7zip') as tempdir:
    sevenzip_page_content = webcat("https://www.7-zip.org/")
    regex = r"(a\/.*x64\.exe)"
    url_part = next(re.finditer(regex, sevenzip_page_content)).groups()[0]
    final_url = "https://www.7-zip.org/" + url_part
    download_to(final_url, work_dir)

# adwcleaner
with tempfile.TemporaryDirectory(prefix='download_adwcleaner') as tempdir:
    download_to("https://adwcleaner.malwarebytes.com/adwcleaner?channel=release", work_dir, filename="adwcleaner.exe")

# rclone
with tempfile.TemporaryDirectory(prefix='download_rclone') as tempdir:
    tempdir = Path(tempdir)
    output_file = download_to("https://downloads.rclone.org/rclone-current-windows-amd64.zip", tempdir, "rclone.zip")
    downloaded_zip = tempdir / "rclone.zip"
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        for file in z.namelist():
            if file.endswith("rclone.exe"):
                z.extract(file, tempdir)
                shutil.move(tempdir / file, work_dir / "root" / "bin")

# yt-dlp
with tempfile.TemporaryDirectory(prefix='download_ytdlp') as tempdir:
    github_release = json.loads(webcat("https://api.github.com/repos/yt-dlp/yt-dlp/releases"))[0] # primeira
    for asset in github_release['assets']:
        if asset['name'] != "yt-dlp.exe":
            continue
        download_to(asset['browser_download_url'], work_dir / "root" / "bin", filename="yt-dlp.exe")

# ffmpeg
with tempfile.TemporaryDirectory(prefix='download_ffmpeg') as tempdir:
    tempdir = Path(tempdir)
    output_file = download_to("https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", tempdir, "ffmpeg.zip")
    downloaded_zip = tempdir / "ffmpeg.zip"
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        for file in z.namelist():
            try:
                file.index("/bin")
                z.extract(file, tempdir)
                origin = tempdir / file
                if origin.is_dir():
                    continue
                shutil.move(origin, work_dir / "root" / "bin")
            except ValueError:
                pass

# geek uninstaller
with tempfile.TemporaryDirectory(prefix='download_geek') as tempdir:
    tempdir = Path(tempdir)
    output_file = download_to("https://geekuninstaller.com/geek.zip", tempdir, "geek.zip")
    downloaded_zip = tempdir / "geek.zip"
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        for file in z.namelist():
            if not file.endswith(".exe"):
                continue
            z.extract(file, tempdir)
            origin = tempdir / file
            shutil.move(origin, work_dir / "root" / "bin")

# aria2
with tempfile.TemporaryDirectory(prefix='download_aria2') as tempdir:
    tempdir = Path(tempdir)
    github_release = json.loads(webcat("https://api.github.com/repos/aria2/aria2/releases"))[0] # primeira
    for asset in github_release['assets']:
        try:
            asset['name'].index("win-64bit")
            aria2_zip = download_to(asset['browser_download_url'], tempdir, filename="aria2.zip")
            with zipfile.ZipFile(aria2_zip, 'r') as z:
                for file in z.namelist():
                    if not file.endswith(".exe"):
                        continue
                    z.extract(file, tempdir)
                    origin = tempdir / file
                    shutil.move(origin, work_dir / "root" / "bin")
        except ValueError:
            pass


# Windows Update Blocker
with tempfile.TemporaryDirectory(prefix='download_wub') as tempdir:
    tempdir = Path(tempdir)
    downloaded_zip = download_to("https://www.sordum.org/files/downloads.php?st-windows-update-blocker", tempdir, "wub.zip")
    with zipfile.ZipFile(downloaded_zip, 'r') as z:
        z.extractall(tempdir)
    shutil.move(tempdir / "Wub", work_dir / "root" / "Program Files")
