## A CLI tool for converting hitomi.la managas into .epub files
I had to whip up this cli tool because there are no others like it.
People who read manga, doujinshi, mangwas etc, on e-readers, will find this tool extreamly useful.

In the future I might add tools for batch converting.

# Install dependencies
```bash
python -m venv venv        # create a virtual environment (optional but recommended)
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```
# Linux Install
```bash
git clone https://github.com/Tonierbobcat/Hitomi-Epub-Converter.git
cd Hitomi-Epub-Converter

# if you cant run it make it executable
chmod +x install.sh

sudo ./install.sh
```
# Windows Install
```bash
git clone https://github.com/Tonierbobcat/Hitomi-Epub-Converter.git
cd Hitomi-Epub-Converter

python3 main.py [url]
```
# Usage
```bash
hitomi-epub-converter [url]
```
