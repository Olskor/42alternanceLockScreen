import tkinter as tk
from datetime import datetime, timedelta
import subprocess
import pyautogui
import time
import threading
import json
import socket
import os
import pam

shortcuts_to_disable = [
	"org.gnome.desktop.wm.keybindings switch-to-workspace-left",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-right",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-up",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-down",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-1",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-2",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-3",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-4",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-5",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-6",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-7",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-8",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-9",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-10",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-11",
	"org.gnome.desktop.wm.keybindings switch-to-workspace-12",
	"org.gnome.desktop.wm.keybindings switch-applications",
	"org.gnome.desktop.wm.keybindings switch-windows",
	"org.gnome.desktop.wm.keybindings switch-input-source",
	"org.gnome.desktop.wm.keybindings switch-input-source-backward",
	"org.gnome.settings-daemon.plugins.media-keys terminal",
	"org.gnome.settings-daemon.plugins.media-keys www",
	"org.gnome.settings-daemon.plugins.media-keys email",
	"org.gnome.settings-daemon.plugins.media-keys calculator",
	"org.gnome.settings-daemon.plugins.media-keys home",
	"org.gnome.settings-daemon.plugins.media-keys help",
	"org.gnome.settings-daemon.plugins.media-keys search",
	"org.gnome.settings-daemon.plugins.media-keys magnifier",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-in",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-out",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-in",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-out",
	"org.gnome.settings-daemon.plugins.media-keys screensaver",
	"org.gnome.settings-daemon.plugins.media-keys logout",
	"org.gnome.settings-daemon.plugins.media-keys suspend",
	"org.gnome.settings-daemon.plugins.media-keys hibernate",
	"org.gnome.settings-daemon.plugins.media-keys shutdown",
	"org.gnome.settings-daemon.plugins.media-keys volume-mute",
	"org.gnome.settings-daemon.plugins.media-keys volume-down",
	"org.gnome.settings-daemon.plugins.media-keys volume-up",
	"org.gnome.settings-daemon.plugins.media-keys play",
	"org.gnome.settings-daemon.plugins.media-keys pause",
	"org.gnome.settings-daemon.plugins.media-keys stop",
	"org.gnome.settings-daemon.plugins.media-keys previous",
	"org.gnome.settings-daemon.plugins.media-keys next",
	"org.gnome.settings-daemon.plugins.media-keys eject",
	"org.gnome.settings-daemon.plugins.media-keys mic-mute",
	"org.gnome.settings-daemon.plugins.media-keys video-out",
	"org.gnome.settings-daemon.plugins.media-keys screenshot",
	"org.gnome.settings-daemon.plugins.media-keys area-screenshot",
	"org.gnome.settings-daemon.plugins.media-keys window-screenshot",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-toggle",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-in",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-out",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-in",
	"org.gnome.settings-daemon.plugins.media-keys magnifier-zoom-out",
	"org.gnome.shell.keybindings show-all-applications",
	"org.gnome.shell.keybindings show-notification-list",
	"org.gnome.shell.keybindings toggle-overview",
	"org.gnome.desktop.wm.keybindings hide-window",
	"org.gnome.desktop.wm.keybindings switch-group",
	"org.gnome.desktop.wm.keybindings switch-to-last-workspace",
	"org.gnome.desktop.wm.keybindings switch-to-first-workspace",
	"org.gnome.settings-daemon.plugins.media-keys help"
	"org.gnome.settings-daemon.plugins.media-keys custom-keybindings",
	"org.gnome.settings-daemon.plugins.media-keys custom-keybindings/custom0",
	"org.gnome.settings-daemon.plugins.media-keys custom-keybindings/custom0/name",
	"org.gnome.settings-daemon.plugins.media-keys custom-keybindings/custom0/command",
	"org.gnome.settings-daemon.plugins.media-keys custom-keybindings/custom0/binding"
]


def disable_shortcuts():
	for shortcut in shortcuts_to_disable:
		os.system(f"gsettings set {shortcut} []")

def restore_shortcuts():
    for shortcut in shortcuts_to_disable:
        os.system(f"gsettings reset {shortcut}")

def get_last_login_time():
    try:
        result = subprocess.run(["last", "-F"], stdout=subprocess.PIPE, text=True)
        last_login_line = result.stdout.splitlines()
        for line in last_login_line:
            if "gone - no logout" in line:
                last_login_line = line
        last_login_time_str = " ".join(last_login_line.split()[3:8])
        return datetime.strptime(last_login_time_str, "%a %b %d %H:%M:%S %Y")
    except Exception as e:
        print (f"error: {e}")
        return None

def get_previous_login_time():
    global offset, last_login_time, logSaveFile
    try:
        with open(logSaveFile, "r") as file:
            existing_data = json.load(file)
    except:
        return 0
    
    result = subprocess.run(["last", "-F"], stdout=subprocess.PIPE, text=True)
    all_login_lines = result.stdout.splitlines()

    user_login = os.getlogin()

    for line in all_login_lines:
        if user_login in line and "gone - no logout" not in line:
            login_time_str = " ".join(line.split()[3:8])
            logout_time_str = " ".join(line.split()[9:14])
            login_time = datetime.strptime(login_time_str, "%a %b %d %H:%M:%S %Y")
            if "crash" in logout_time_str:
                logout_time_str = logout_time_str.split()[1][1:-1]
                append = datetime.strptime(logout_time_str, "%H:%M")
                logout_time = login_time + timedelta(hours=append.hour, minutes=append.minute)
            else:
                logout_time = datetime.strptime(logout_time_str, "%a %b %d %H:%M:%S %Y")
            if login_time.date() < datetime.strptime("2025-01-06 00:00:00", "%Y-%m-%d %H:%M:%S").date():
                continue
            if login_time.hour < 8:
                login_time = login_time.replace(hour = 8, minute = 0, second = 0, microsecond = 0)
                if logout_time.hour < 8:
                    continue
            if login_time.hour > 20:
                continue
            if logout_time.hour > 20:
                logout_time = logout_time.replace(hour = 20, minute = 0, second = 0, microsecond = 0)
            for entry in existing_data:
                if login_time == datetime.strptime(entry["login"], "%Y-%m-%d %H:%M:%S"):
                    entry["logout"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")
                    total = logout_time - login_time
                    entry["ellapsed-time"] = str(total).split('.')[0]
                    break

    offset = 0
    for entry in existing_data:
        login_time = datetime.strptime(entry["login"], "%Y-%m-%d %H:%M:%S")
        if login_time.date() == datetime.now().date() and login_time != last_login_time:
            logout_time = datetime.strptime(entry["logout"], "%Y-%m-%d %H:%M:%S")
            offset += (logout_time - login_time).total_seconds()
    
    with open(logSaveFile, "w") as file:
        json.dump(existing_data, file, indent=4)

def Lock(e = None):
    global locked
    locked = not locked
    return

def ask_password():
	global password_window, password_entry
	password_window = tk.Toplevel(root)
	password_window.title("Enter Password")
	password_window.geometry("300x150")
	password_window.configure(bg="black")

	tk.Label(password_window, text="Password:", font=("Helvetica", 14), bg="black", fg="white").pack(pady=10)
	password_entry = tk.Entry(password_window, show="*", font=("Helvetica", 14))
	password_entry.pack(pady=10)
	password_entry.focus_set()
	password_window.bind('<Return>', lambda event: check_password())

def check_password():
	entered_password = password_entry.get()
	user = os.getlogin()
	auth = pam.pam()
	user = os.getlogin()
	if auth.authenticate(user, entered_password):
		password_window.destroy()
		OnEscape()
	else:
		tk.Label(password_window, text="Incorrect Password", font=("Helvetica", 12), bg="black", fg="red").pack(pady=5)


def OnEscape():
    global last_login_time, logSaveFile
    root.destroy()

    current_time = datetime.now()
    time_difference = current_time - last_login_time
    data = {
        "login": last_login_time.strftime("%Y-%m-%d %H:%M:%S"),
        "logout": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "ellapsed-time": str(time_difference).split('.')[0],
        "poste": socket.gethostname()
    }
    try:
        with open(logSaveFile, "r") as file:
            existing_data = json.load(file)
    except:
        existing_data = []

    entryfound = False


    for entry in existing_data:
        if entry["login"] == data["login"]:
            entry.update(data)
            entryfound = True
            break
    if not entryfound:
        existing_data.append(data)

    with open(logSaveFile, "w") as file:
        json.dump(existing_data, file, indent=4)

    os.system("gsettings set org.gnome.mutter overlay-key 'Super_L'")
    restore_shortcuts()
    turn_on_screen()

def PreventLock():
    global locked
    pyautogui.moveRel(0, 1)
    pyautogui.moveRel(0, -1)
    if locked:
        turn_off_screen()
    root.after(1000 * 60 * 4, PreventLock)

def turn_off_screen():
    os.system("xset dpms force off")

def turn_on_screen():
    os.system("xset dpms force on")

def CheckScreen():
    global locked
    if locked:
        turn_off_screen()
    else:
        turn_on_screen()
    root.after(20, UpdateLabelTime)

def UpdateLabelTime():
    global label, last_login_time, offset, root
    current_time = datetime.now()
    if current_time.hour > 20:
        label.configure(text=f"Time out it's 20h", fg = "white")
    if current_time.hour < 8:
        label.configure(text=f"It's to early !", fg = "white")
    time_difference = current_time - last_login_time
    if time_difference.total_seconds() >= 5.75 * 3600:
        label.configure(text=f"Take a break!", fg = "white")
        CheckScreen()
        return
    diff = 7 * 3600
    remaining_time = max(diff - time_difference.total_seconds() - offset, 0)
    if remaining_time < 600:
        remaining_time_str = str(datetime.utcfromtimestamp(remaining_time).strftime("%M:%S.%f")[:-3])
        if int(remaining_time % 2) == 0:
            label.configure(text=f"{remaining_time_str}", fg = "white")
        if int(remaining_time % 2) == 1:
            label.configure(text=f"{remaining_time_str}", fg = "red")
        if remaining_time <= 0:
            label.configure(text=f"YOU ARE FREE !!!", fg = "white")
            CheckScreen()
            return
        CheckScreen()
        return
    remaining_time_str = str(datetime.utcfromtimestamp(remaining_time).strftime("%H:%M:%S"))
    label.configure(text=f"{remaining_time_str}", fg = "white")
    CheckScreen()      

logSaveFile = "saveLog.json"
offset = 0
last_login_time = get_last_login_time()
if last_login_time.hour < 8:
    last_login_time = last_login_time.replace(hour = 8, minute = 0, second = 0, microsecond = 0)
get_previous_login_time()
if last_login_time is None:
    exit()

os.system("gsettings set org.gnome.mutter overlay-key ''")
#disable_shortcuts()

current_time = datetime.now()
time_difference = current_time - last_login_time

root = tk.Tk()
root.title("Time remaning...")
root.attributes("-fullscreen", True)
root.configure(bg="black")

frame = tk.Frame(root, bg = "black")
frame.pack(anchor="center", expand="true")

label = tk.Label(frame, text=f"{time_difference}", justify="center", font=("Helvetica", 200), bg = "black", fg = "white")
label.pack(expand="true")

locked = False

root.after(1, UpdateLabelTime)
root.after(1000, PreventLock)

root.bind('<q>', Lock)
root.bind('<Escape>', lambda e: ask_password())

root.mainloop()
