# Macro-for-MacOS
1. Open Terminal on your Mac
2. Navigate to your script's folder
Use the cd command to go to the folder where macro_recorder_gui.py is saved. For example, if it’s on your Desktop in a folder called MacroApp:
cd ~/Desktop/MacroApp
3. Install PyInstaller and dependencies (if not installed)
Run:
pip install pyinstaller pyobjc-framework-Quartz pyobjc-framework-ApplicationServices
4. Run PyInstaller to create the app
Type this command:
pyinstaller --windowed --name "MacroRecorder" macro_recorder_gui.py
--windowed means no terminal window will show when running the app
--name sets the name of your app bundle
5. Find your app
When PyInstaller finishes, it creates a folder called dist inside your current folder.
Inside dist, you’ll find:

MacroRecorder.app
6. Run your app
Open it by typing:
open dist/MacroRecorder.app
7. Grant Accessibility permissions
Go to System Settings → Privacy & Security → Accessibility
Click the + and add MacroRecorder.app (or Terminal if you run from there)
This lets your app record keyboard/mouse input.
That’s it! Your Python macro recorder will now run as a normal macOS app.
