import zipfile

from PIL import Image
from ebooklib import epub

import subprocess
import os
import urllib.parse
import shutil
import sys

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

def progress(prefix, total, current, length=40):
    fraction = current / total
    filled_length = int(length * fraction)
    bar = '=' * filled_length + '-' * (length - filled_length)
    percent = fraction * 100
    sys.stdout.write(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()

def convert_to_epub(extract_folder, output_epub, title, id, author="Unknown", language="en"):
    book = epub.EpubBook()

    book.set_identifier(id)
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # collect as XHTML pages
    images = sorted(os.listdir(extract_folder))

    pages_to_add = []

    for i, img_file in enumerate(images, start=1):
        pages_to_add.append(img_file)

    added_pages = 0

    for i, img_file in enumerate(pages_to_add, start=1):
        img_path = os.path.join(extract_folder, img_file)
        
        # make sure they are images
        im = Image.open(img_path)
        if im.mode != "RGB":
            im = im.convert("RGB")
            im.save(img_path)
        
        # create XHTML page embedding with the imge
        html_content = f'<html><body><img src="{img_file}" alt="{img_file}"/></body></html>'
        c = epub.EpubHtml(title=f"Page {i}", file_name=f"page_{i}.xhtml", content=html_content)
        book.add_item(c)
        book.spine.append(c)

        # add the image to the epub files
        with open(img_path, 'rb') as f:
            img_item = epub.EpubItem(uid=f"img{i}", file_name=img_file, media_type=f"image/{img_file.split('.')[-1]}", content=f.read())
            book.add_item(img_item)
        added_pages += 1
        progress("EPUB", len(pages_to_add), added_pages)
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # write
    epub.write_epub(output_epub, book)

def download_hitomi(target, url):
    # subprocess.run(["gallery-dl", "-d", target, url])
    return

def exit_cannot_convert_epub(reason):
    print(f"Could not convert into an epub. {reason}")
    sys.exit(1)

def convert_images_to_target_dir(source, target):
    
    def convert_image_to_jpg(path):
        img = Image.open(path)
        img = img.convert("RGB")
        base = os.path.splitext(os.path.basename(path))[0]
        img.save(f"{target}/{base}.jpg", "JPEG")

    amount_to_convert = []

    for file in os.listdir(source):
        if file.endswith((".webp", ".png", ".jpg")):sys.exit(0)
            amount_to_convert.append(full_path)

    # for root, dirs, files in os.walk(source):
    #     for file in files:
    #         if file.lower().endswith((".webp", ".png", ".jpg")):
    #             full_path = os.path.join(root, file)
    #             amount_to_convert.append(full_path)
                
    converted_images = 0
    for file in amount_to_convert:
        convert_image_to_jpg(file)
        converted_images += 1
        progress("CONVERT", len(amount_to_convert), converted_images)

def start_convert(url):
    parsed_url = parse_url(url)
    formated_url = format_parsed_url(parsed_url)

    title = ""
    doujinshi_id = ""

    if formated_url.strip():
        *title_parts, doujinshi_id = formated_url.rsplit(' ', 1)
        title = ' '.join(title_parts)

    home = os.path.expanduser("~")

    save_folder = f"{home}/hitomi-epub-converter"

    output_epub = f"{save_folder}/{title}.epub"

    delete_gallery_cache = False

    cache_folder = f"{save_folder}/cache"

    hitomi_target = f"{save_folder}/cache/{doujinshi_id} {title}"

    tmp_folder = f"{save_folder}/tmp"

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
    for folder in [save_folder, cache_folder, tmp_folder, hitomi_target]:
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

    # convert to epub
    convert_to_epub(tmp_folder, output_epub, title, doujinshi_id)

    # cleanup
    folders_to_delete = []

    folders_to_delete.append(delete_tmp)
    if delete_gallery_cache:
        folders_to_delete.append(delete_cache)

    deleted = 0

    for function in folders_to_delete:
        function()
        deleted += 1

    progress("DELETE", len(folders_to_delete), deleted)
    # print output
    print(f"Successfully converted. {output_epub}")

if (len(sys.argv) < 2):
    print("usage: hitomi-epub-converter <-i|-b> <[url]|[text-file]>")
    sys.exit(1)

option = sys.argv[1]

if (option == "-i"):
    if len(sys.argv) < 3:
        print("usage: hitomi-epub-converter -i [url]")
        sys.exit(1)
    url = sys.argv[2]
    start_convert(url)
    sys.exit(0)
if (option == "-b"):
    if len(sys.argv) < 3:
        print("usage: hitomi-epub-converter -b [text-file]")
        sys.exit(1)
    
    sys.exit(0)

