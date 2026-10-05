# Image Compressor (Windows)

A simple desktop tool to pick an image and compress it, built with Tkinter and Pillow.

## Features

- Open JPG, PNG, WEBP, BMP and TIFF images
- Live preview with original file size
- JPEG/WebP quality slider (1-95)
- Optional resize (max width/height, aspect ratio kept)
- Convert on save: JPEG, PNG or WEBP
- PNG optimize and palette reduction
- Shows resulting size and % reduction; "Save As" lets you choose the output location

## Package contents

| File | Purpose |
|------|---------|
| `image_compressor_gui.pyw` | The app (runs without a console window) |
| `app_icon.ico` | Icon used for the shortcut |
| `create_desktop_shortcut.vbs` | Creates the desktop shortcut |
| `README_setup_windows.txt` | Plain-text setup notes |

## Setup

1. Install [Python](https://python.org) (tick "Add python.exe to PATH").
2. Install Pillow:
   ```
   pip install Pillow
   ```
3. Keep all files together in one folder, e.g. `C:\Users\<you>\Apps\ImageCompressor\`.
4. Double-click `create_desktop_shortcut.vbs` to add an "Image Compressor" icon to your Desktop.
5. Launch the app from the desktop icon, or run `pythonw image_compressor_gui.pyw`.

## Build a standalone .exe

```
pip install pyinstaller
pyinstaller --onefile --windowed --icon=app_icon.ico image_compressor_gui.pyw
```

The executable appears in `dist/`.

## Troubleshooting

- **Icon does nothing:** right-click it, Properties, and check Target is a valid `pythonw.exe` path followed by the quoted `.pyw` path.
- **Window flashes and closes:** Pillow is missing; run `pip install Pillow`.
