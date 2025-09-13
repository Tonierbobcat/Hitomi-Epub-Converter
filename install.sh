#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root: sudo ./install.sh"
  exit 1
fi

cp -r . "/usr/local/share/hitomi-epub-converter"
cd /usr/local/share/hitomi-epub-converter || exit
cp /usr/local/share/hitomi-epub-converter/bin/hitomi-epub-converter /usr/local/bin/
chmod +x /usr/local/bin/hitomi-epub-converter

cd /usr/local/share/hitomi-epub-converter || exit
if [ ! -d "venv" ]; then
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo "Installation complete"