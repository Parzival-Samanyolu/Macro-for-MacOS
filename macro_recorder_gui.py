import time
import json
import threading
from pynput import mouse, keyboard
import pyautogui
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext

OUT_FILE = Path("last_macro.json")

recording = False
events = []
start_time = None
mouse_listener = None
keyboard_listener = None

modifiers_pressed = set()

# Keys for old hotkeys (optional)
TOGGLE_RECORD_KEY = keyboard.Key.f8
PLAY_KEY = keyboard.Key.f9
EXIT_KEY = keyboard.Key.esc

# --- Recorder Functions ---

def now():
    return time.time()

def record_event(ev_type, data):
    global events, start_time
    events.append({
        "t": round(now() - start_time, 4),
        "type": ev_type,
        "data": data
    })
    update_event_count()

def on_move(x, y):
    if recording:
        record_event("mouse_move", {"x": x, "y": y})

def on_click(x, y, button, pressed):
    if recording:
        record_event("mouse_click", {"x": x, "y": y, "button": button.name, "pressed": pressed})

def on_scroll(x, y, dx, dy):
    if recording:
        record_event("mouse_scroll", {"x": x, "dy": dy, "dx": dx})

def on_press(key):
    global recording, start_time, events, modifiers_pressed
    try:
        k = key.char
    except AttributeError:
        k = str(key)

    # Old hotkey support (optional)
    if key == TOGGLE_RECORD_KEY:
        app.toggle_record()
        return
    if key == PLAY_KEY:
        app.playback()
        return
    if key == EXIT_KEY:
        app.quit()
        return

    if recording:
        if key in (keyboard.Key.shift, keyboard.Key.shift_r,
                   keyboard.Key.ctrl, keyboard.Key.ctrl_r,
                   keyboard.Key.alt, keyboard.Key.alt_r,
                   keyboard.Key.cmd, keyboard.Key.cmd_r):
            modifiers_pressed.add(k)
        record_event("key_press", {"key": k})

def on_release(key):
    global modifiers_pressed
    if recording:
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        if key in (keyboard.Key.shift, keyboard.Key.shift_r,
                   keyboard.Key.ctrl, keyboard.Key.ctrl_r,
                   keyboard.Key.alt, keyboard.Key.alt_r,
                   keyboard.Key.cmd, keyboard.Key.cmd_r):
            modifiers_pressed.discard(k)
        record_event("key_release", {"key": k})

def start_recording():
    global recording, start_time, events, modifiers_pressed
    events = []
    modifiers_pressed = set()
    start_time = now()
    recording = True
    update_status("Recording...")
    update_event_count()

def stop_recording():
    global recording
    recording = False
    save_events()
    update_status("Idle")
    update_event_count()
    print(f"[recorder] saved {len(events)} events to {OUT_FILE}")

def save_events():
    OUT_FILE.write_text(json.dumps({"created": time.time(), "events": events}, indent=2))

def load_events():
    if not OUT_FILE.exists():
        update_status("No recording found.")
        return None
    return json.loads(OUT_FILE.read_text())["events"]

def playback_thread():
    evs = load_events()
    if not evs:
        return
    update_status("Playing...")
    print("[player] starting playback...")
    t0 = time.time()

    current_modifiers = set()

    def press_mods(mods):
        for m in mods:
            mod_key = map_key_name_to_pyautogui(m)
            if mod_key:
                pyautogui.keyDown(mod_key)

    def release_mods(mods):
        for m in reversed(list(mods)):
            mod_key = map_key_name_to_pyautogui(m)
            if mod_key:
                pyautogui.keyUp(mod_key)

    for e in evs:
        delay = e["t"] - (time.time() - t0)
        if delay > 0:
            time.sleep(delay)
        typ = e["type"]
        d = e["data"]
        try:
            if typ == "mouse_move":
                pyautogui.moveTo(d["x"], d["y"], _pause=False)
            elif typ == "mouse_click":
                if d["pressed"]:
                    pyautogui.click(x=d["x"], y=d["y"], button=d["button"], _pause=False)
            elif typ == "mouse_scroll":
                pyautogui.scroll(d["dy"], x=d["x"], y=d["y"])
            elif typ == "key_press":
                k = d["key"]
                if is_modifier_key(k):
                    current_modifiers.add(k)
                    pyautogui.keyDown(map_key_name_to_pyautogui(k))
                else:
                    press_mods(current_modifiers)
                    if len(k) == 1:
                        pyautogui.typewrite(k, _pause=False)
                    else:
                        special = map_special_key(k)
                        if special:
                            pyautogui.press(special)
                    release_mods(current_modifiers)
            elif typ == "key_release":
                k = d["key"]
                if is_modifier_key(k):
                    current_modifiers.discard(k)
                    pyautogui.keyUp(map_key_name_to_pyautogui(k))
        except Exception as ex:
            print("[player] playback error:", ex)
    update_status("Idle")
    print("[player] done.")

def playback():
    threading.Thread(target=playback_thread, daemon=True).start()

def is_modifier_key(k):
    return k in [
        "Key.shift", "Key.shift_r",
        "Key.ctrl", "Key.ctrl_r",
        "Key.alt", "Key.alt_r",
        "Key.cmd", "Key.cmd_r"
    ]

def map_key_name_to_pyautogui(k):
    mapping = {
        "Key.shift": "shift",
        "Key.shift_r": "shift",
        "Key.ctrl": "ctrl",
        "Key.ctrl_r": "ctrl",
        "Key.alt": "alt",
        "Key.alt_r": "alt",
        "Key.cmd": "command",
        "Key.cmd_r": "command"
    }
    return mapping.get(k, None)

def map_special_key(k):
    mapping = {
        "Key.space": "space",
        "Key.enter": "enter",
        "Key.tab": "tab",
        "Key.backspace": "backspace",
        "Key.esc": "esc",
        "Key.up": "up",
        "Key.down": "down",
        "Key.left": "left",
        "Key.right": "right",
        "Key.delete": "delete",
        "Key.home": "home",
        "Key.end": "end",
        "Key.page_up": "pageup",
        "Key.page_down": "pagedown",
        "Key.f1": "f1",
        "Key.f2": "f2",
        "Key.f3": "f3",
        "Key.f4": "f4",
        "Key.f5": "f5",
        "Key.f6": "f6",
        "Key.f7": "f7",
        "Key.f8": "f8",
        "Key.f9": "f9",
        "Key.f10": "f10",
        "Key.f11": "f11",
        "Key.f12": "f12",
    }
    return mapping.get(k, None)

def stop_all():
    global mouse_listener, keyboard_listener
    if mouse_listener:
        mouse_listener.stop()
    if keyboard_listener:
        keyboard_listener.stop()
    print("exiting.")
    app.root.quit()

# --- GUI App Class ---

class MacroRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Recorder")
        self.root.geometry("350x200")
        self.create_widgets()
        self.setup_listeners()
        self.update_status("Idle")

    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Arial", 12))
        self.status_label.pack(pady=8)

        self.event_count_label = tk.Label(self.root, text="Events recorded: 0")
        self.event_count_label.pack(pady=4)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        self.record_btn = tk.Button(btn_frame, text="Record", width=10, command=self.toggle_record)
        self.record_btn.grid(row=0, column=0, padx=5)

        self.play_btn = tk.Button(btn_frame, text="Play", width=10, command=self.playback)
        self.play_btn.grid(row=0, column=1, padx=5)

        self.quit_btn = tk.Button(btn_frame, text="Quit", width=10, command=self.quit)
        self.quit_btn.grid(row=0, column=2, padx=5)

    def update_status(self, text):
        self.status_label.config(text=f"Status: {text}")

    def update_event_count(self):
        count = len(events)
        self.event_count_label.config(text=f"Events recorded: {count}")

    def toggle_record(self):
        global recording
        if recording:
            stop_recording()
            self.record_btn.config(text="Record")
            self.update_status("Idle")
        else:
            start_recording()
            self.record_btn.config(text="Stop")
            self.update_status("Recording...")

    def playback(self):
        if recording:
            print("Stop recording before playback.")
            return
        self.update_status("Playing...")
        playback()

    def quit(self):
        stop_all()

    def setup_listeners(self):
        global mouse_listener, keyboard_listener
        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        mouse_listener.start()
        keyboard_listener.start()

# Global app instance for callbacks
app = None

def update_status(text):
    if app:
        app.update_status(text)

def update_event_count():
    if app:
        app.update_event_count()

def main():
    global app
    root = tk.Tk()
    app = MacroRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit)
    root.mainloop()

if __name__ == "__main__":
    main()
