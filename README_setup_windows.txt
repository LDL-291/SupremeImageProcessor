IMAGE COMPRESSOR - Windows Desktop Icon Setup
===============================================

Files in this package:
  image_compressor_gui.pyw     -> the app (runs without a console window)
  app_icon.ico                 -> the icon used for the shortcut
  create_desktop_shortcut.vbs  -> creates the desktop icon for you
  README_setup_windows.txt     -> this file

ONE-TIME SETUP
---------------
1. Install Python from https://python.org (during install, check "Add
   python.exe to PATH"), if you don't already have it.

2. Open Command Prompt and install Pillow:
       pip install Pillow

3. Put all files from this package into one folder, e.g.
       C:\Users\<you>\Apps\ImageCompressor\

4. Double-click "create_desktop_shortcut.vbs".
   A shortcut named "Image Compressor" will appear on your Desktop,
   using the custom icon.

5. Double-click the new desktop icon any time to launch the app.

TROUBLESHOOTING
-----------------
- If double-clicking the desktop icon does nothing, right-click it ->
  Properties, and check the "Target" field points to a real pythonw.exe
  path followed by the .pyw file in quotes, e.g.:
      "C:\Users\you\AppData\Local\Programs\Python\Python312\pythonw.exe" "C:\Users\you\Apps\ImageCompressor\image_compressor_gui.pyw"

- If Pillow is missing you'll get a console flash-and-close. Reinstall
  it with:  pip install Pillow

- Prefer a real standalone .exe (no Python install needed on other
  machines)? On a Windows machine with Python installed, run:
      pip install pyinstaller
      pyinstaller --onefile --windowed --icon=app_icon.ico image_compressor_gui.pyw
  The .exe will appear in the "dist" folder. You can then make a
  shortcut to that .exe with the same icon instead.
