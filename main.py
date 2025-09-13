import zipfile

from PIL import Image
# from ebooklib import epub

import subprocess
import os
import urllib.parse
import shutil
import sys
import comicon
import re
from rich import print
from rich.progress import Progress

from gallery_dl import config, extractor, job

home = os.path.expanduser("~")
data_folder = f"{home}/hitomi-epub-converter"
cache_folder = f"{data_folder}/cache"
tmp_folder = f"{data_folder}/tmp"
debug = False

def parse_url(url):
    decoded = urllib.parse.unquote(url)
    decoded = decoded.split('#')[0]
    return decoded

def format_parsed_url(url):
    basename = os.path.basename(url)
    if basename.endswith(".html"):
        basename = basename[:-5]

    parts = basename.split('-')
    parts = [part[0].upper() + part[1:] if part else '' for part in parts]

    basename = ' '.join(parts)

    return basename

def convert_cbz_to_epub(cbz, epub, pages):
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Converting cbz...", total=pages)
        for value in comicon.convert_progress(cbz, epub):
            progress.update(task, advance=1)

def download_hitomi(target, url):
    config.set((), "base-directory", target)
    config.set((), "directory", ())

    config.set((), "loglevel", "CRITICAL")
    config.set(("output",), "mode", "null")

    extr = extractor.find(url)
    dl_job = job.DownloadJob(extr)
    dl_job.run()
    return

def exit_cannot_convert_epub(reason):
    print(f"Could not convert into an epub. {reason}")
    sys.exit(1)

def convert_images_to_target_dir(source, target):
    
    kobo_libra_colour_pixels_y = 1680

    def convert_image_to_jpg(path):
        img = Image.open(path)
        img = img.convert("RGB")

        # Calculate new width to maintain aspect ratio
        orig_width, orig_height = img.size
        if orig_height > kobo_libra_colour_pixels_y:
            new_height = kobo_libra_colour_pixels_y
            new_width = int(orig_width * (new_height / orig_height))
            img = img.resize((new_width, new_height), Image.LANCZOS)

        base = os.path.splitext(os.path.basename(path))[0]
        img.save(f"{target}/{base}.jpg", "JPEG", quality=95)

    amount_to_convert = []

    for file in os.listdir(source):
        if file.endswith((".webp", ".png", ".jpg")):
            amount_to_convert.append(f"{source}/{file}")

    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Converting images...", total=len(amount_to_convert))
        for file in amount_to_convert:
            convert_image_to_jpg(file)
            progress.update(task, advance=1)

def start_convert(url, delete_gallery_cache):
    parsed_url = parse_url(url)
    formated_url = format_parsed_url(parsed_url)

    title = ""
    doujinshi_id = ""

    if formated_url.strip():
        *title_parts, doujinshi_id = formated_url.rsplit(' ', 1)
        title = ' '.join(title_parts)


    legal_title = re.sub(r'[:?"*\\|/]', ' ', title)

    # rakuten kobo doesnt allow files that contain : ? " * \ | /"
    output_epub = f"{data_folder}/{legal_title}.epub"

    hitomi_target = f"{data_folder}/cache/{doujinshi_id} {title}"

    def delete_tmp():
        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)
        return
    def delete_cache():
        if os.path.exists(hitomi_target):
            shutil.rmtree(hitomi_target)
        return

    # delete old tmp
    delete_tmp()

    # validate folders
    # hitomi target added the end
    for folder in [data_folder, cache_folder, tmp_folder, hitomi_target]:
        if not os.path.exists(folder):
            os.mkdir(folder, mode=0o777)

    # download manga/doujinshi
    print(f"Downloading {title} ({doujinshi_id})...")
    download_hitomi(hitomi_target, url)
    downloaded = len(os.listdir(hitomi_target))
    if downloaded <= 0:
        exit_cannot_convert_epub("No pages were downloaded.")
    print(f"Downloaded {downloaded} page(s)")
    
    # copy images to output and converts them
    convert_images_to_target_dir(hitomi_target, tmp_folder)

    # create cbz file
    output_cbz = f"{tmp_folder}/{title}.cbz"
    images = sorted(
        [f for f in os.listdir(tmp_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    )
    with zipfile.ZipFile(output_cbz, 'w', zipfile.ZIP_DEFLATED) as cbz:
        for image in images:
            image_path = os.path.join(tmp_folder, image)
            cbz.write(image_path, arcname=image)

    # convert to epub
    convert_cbz_to_epub(output_cbz, output_epub, len(images))

    # cleanup
    folders_to_delete = []

    if not debug:
        folders_to_delete.append(delete_tmp)
    if delete_gallery_cache:
        folders_to_delete.append(delete_cache)
    for function in folders_to_delete:
        function()

    # print output
    print(f"Successfully converted. {output_epub}")

if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0]} <-i|-b> <[url]|[text-file]> [-x]")
    sys.exit(1)

option = sys.argv[1]

if option == "-i":
    delete_cache = False
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} -i [url] [-x]")
        sys.exit(1)
    
    if sys.argv[2] == "-x" and len(sys.argv) >= 4:
        url = sys.argv[3]
        delete_cache = True
    else:
        url = sys.argv[2]

    start_convert(url, delete_cache)
    sys.exit(0)

elif option == "-b":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} -b [text-file]")
        sys.exit(1)
    
    # Call your batch processing function here
    # process_batch(sys.argv[2])
    sys.exit(0)

else:
    print(f"Unknown option: {option}")
    print(f"usage: {sys.argv[0]} <-i|-b> <[url]|[text-file]> [-x]")
    sys.exit(1)