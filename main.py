import zipfile

from PIL import Image
from ebooklib import epub

import subprocess
import os
import urllib.parse
import shutil
import sys

def trim_url_to_name(url):
    decoded = urllib.parse.unquote(url)
    decoded = decoded.split('#')[0]
    if decoded.endswith(".html"):
        decoded = decoded[:-5]
    return os.path.basename(decoded)

def progress(prefix, total, current, length=40):
    fraction = current / total
    filled_length = int(length * fraction)
    bar = '=' * filled_length + '-' * (length - filled_length)
    percent = fraction * 100
    sys.stdout.write(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()

def convert_image(path, output_folder):
    img = Image.open(path)
    img = img.convert("RGB")
    base = os.path.splitext(os.path.basename(path))[0]
    img.save(f"{output_folder}/{base}.jpg", "JPEG")

def convert_to_epub(extract_folder, title, author="Unknown", language="en", id="id123456"):
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

url = sys.argv[1]
base = trim_url_to_name(url)
home = os.path.expanduser("~")

save_folder = f"{home}/hitomi-epub-converter"
if not os.path.exists(save_folder):
    os.mkdir(save_folder, mode=0o777)

output_epub = f"{save_folder}/{base}.epub"
delete_gallery_cache = False
hitomi_target = f"{save_folder}/cache"

if not os.path.exists(hitomi_target):
    os.mkdir(hitomi_target, mode=0o777)

hitomi_output = f"{hitomi_target}/hitomi"

subprocess.run(["gallery-dl", "-d", hitomi_target, url])

tmp_folder = f"{save_folder}/tmp"
if not os.path.exists(tmp_folder):
    os.mkdir(tmp_folder, mode=0o777)

amount_to_convert = []

for root, dirs, files in os.walk(hitomi_output):
    for file in files:
        if file.lower().endswith((".webp", ".png", ".jpg")):
            full_path = os.path.join(root, file)
            amount_to_convert.append(full_path)
            
converted_images = 0

for file in amount_to_convert:
    convert_image(file, tmp_folder)
    converted_images += 1
    progress("CONVERT", len(amount_to_convert), converted_images)

# convert to epub
convert_to_epub(tmp_folder, f"{base}")

# cleanup
folders_to_delete = []

if delete_gallery_cache:
    folders_to_delete.extend([hitomi_target, tmp_folder])
else:
    folders_to_delete.append(tmp_folder)

deleted = 0

for folder in folders_to_delete:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    deleted += 1
    progress("DELETE", len(folders_to_delete), deleted)

# print output
print(f"{output_epub}")