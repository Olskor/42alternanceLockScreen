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
from pynput import keyboard

def get_all_shortcuts():
	result = subprocess.run(["gsettings", "list-recursively"], stdout=subprocess.PIPE, text=True)
	lines = result.stdout.splitlines()
	shortcuts = []
	for line in lines:
		if "start_timer" in line:
			continue
		if "keybindings" in line or "media-keys" in line:
			key = line.split()[0] + " " + line.split()[1]
			shortcuts.append(key)
	return shortcuts

shortcuts_to_disable = get_all_shortcuts()


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
    global offset, last_login_time, logSaveFile, user
    try:
        with open(logSaveFile, "r") as file:
            existing_data = json.load(file)
    except:
        return 0
    
    result = subprocess.run(["last", "-F"], stdout=subprocess.PIPE, text=True)
    all_login_lines = result.stdout.splitlines()

    for line in all_login_lines:
        if user in line and "gone - no logout" not in line:
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
	global locked, lock_window, lock_label, password_entry, locked_time, user, lock_bkg_path, root
	if locked:
		return
	try:
		root.withdraw()
		reset_screen_off_timer()
		locked = True
		locked_time = datetime.now()
		os.system("gsettings set org.gnome.mutter overlay-key ''")
		threading.Thread(target=disable_shortcuts).start()
		lock_window = tk.Toplevel(root)
		lock_window.attributes("-fullscreen", True)
		lock_window.configure(bg="black")
		screen_width = lock_window.winfo_screenwidth()
		screen_height = lock_window.winfo_screenheight()
		lockcanvas = tk.Canvas(lock_window, width=screen_width, height=screen_height, bg="black", highlightthickness=0)
		if os.path.exists("/home/jauffret/Documents/42alternanceLockScreen/ft_lock_bkg.png"):
			try:
				bg_image = tk.PhotoImage(file="/home/jauffret/Documents/42alternanceLockScreen/ft_lock_bkg.png")
				bg_image = bg_image.subsample(bg_image.width() // screen_width, bg_image.height() // screen_height)
				lock_window.bg_image = bg_image
				lockcanvas.create_image(0, 0, anchor="nw", image=bg_image)
			except:
				lockcanvas.create_image(0, 0, anchor="nw")
				print("Error loading background image")
		lockcanvas.pack(fill="both", expand=True)
		lock_label = lockcanvas.create_text(screen_width - 20, screen_height - 20, text="", font=("Helvetica", 20), fill="white", anchor="se")
		locked_by = lockcanvas.create_text(540, 100, text="Locked by jauffret : a few seconds ago...\n Back sOOn..", font=("Helvetica", 14), fill="white", anchor="center", justify="center")
		password_entry = tk.Entry(lockcanvas, show="o", font=("Helvetica", 14), insertbackground="white")
		password_entry.configure(bg="#8FABFF", fg="#FFFFFF", width=30, bd=8, relief="flat", highlightthickness=0)
		password_entry.pack(side="top", anchor="nw", padx=280, pady=150)
		password_entry.focus_set()
		lock_window.password_entry = password_entry
		lock_window.bind('<Return>', lambda event: check_password())
		lock_window.canvas = lockcanvas
		lock_window.locked_by = locked_by
		lock_window.mainloop()
	except Exception as e:
		print(f"Error: {e}")
		locked = False
		os.system("gsettings set org.gnome.mutter overlay-key 'Super_L'")
		restore_shortcuts()
		turn_on_screen()
		if lock_window is not None:
			lock_window.destroy()
	return

def check_password():
	global lock_window, locked, user, root
	entered_password = lock_window.password_entry.get()
	auth = pam.pam()
	if auth.authenticate(user, entered_password):
		os.system("gsettings set org.gnome.mutter overlay-key 'Super_L'")
		threading.Thread(target=restore_shortcuts).start()
		turn_on_screen()
		locked = False
		lock_window.destroy()
		root.deiconify()
	else:
		lock_window.password_entry.delete(0, "end")


def OnEscape():
    global last_login_time, logSaveFile, locked

    if locked:
        return

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
    pyautogui.moveRel(0, 1)
    pyautogui.moveRel(0, -1)
    root.after(1000 * 60 * 4, PreventLock)

def turn_off_screen():
    os.system("xset dpms force off")

def turn_on_screen():
    os.system("xset dpms force on")

def screen_off_locked():
	global screen_off_timer, screen_off, locked
	if not locked:
		screen_off = False
	if screen_off_timer <= 0:
		screen_off = True
	else:
		screen_off_timer -= 1
		screen_off = False
	root.after(1000, screen_off_locked)

def CheckScreen():
    global screen_off, locked
    if screen_off and locked:
        turn_off_screen()
        root.after(10000, UpdateLabelTime)
        return
    else:
        turn_on_screen()
    root.after(20, UpdateLabelTime)

def UpdateLabelTime():
	global last_login_time, offset, root, lock_label, lock_window, locked, locked_time
	current_time = datetime.now()
	if locked:
		time_since_locked = current_time - locked_time
		if time_since_locked.total_seconds() >= 60:
			lock_window.canvas.itemconfigure(lock_window.locked_by, text=f"Locked by {user} : {time_since_locked.seconds // 60} minutes ago...\n Back sOOn..")
			if time_since_locked.total_seconds() > 60 * 45:
				lock_window.canvas.itemconfigure(lock_window.locked_by, text=f"Locked by {user} : a long time ago...\n Back sOOn..")
	if current_time.hour > 20:
		root.canvas.itemconfigure(root.label, text=f"Time out it's 20h")
		if locked:
			lock_window.canvas.itemconfigure(lock_label, text=f"Time out it's 20h")
	if current_time.hour < 8:
		if locked:
			lock_window.canvas.itemconfigure(lock_label, text=f"It's to early !")
		root.canvas.itemconfigure(root.label, text=f"It's to early !")
	time_difference = current_time - last_login_time
	if time_difference.total_seconds() >= 5.75 * 3600:
		root.canvas.itemconfigure(root.label, text=f"Take a break!")
		if locked:
			lock_window.canvas.itemconfigure(lock_label, text=f"Take a break!")
		CheckScreen()
		return
	diff = 7 * 3600
	remaining_time = max(diff - time_difference.total_seconds() - offset, 0)
	if remaining_time < 600:
		remaining_time_str = str(datetime.utcfromtimestamp(remaining_time).strftime("%M:%S.%f")[:-3])
		if int(remaining_time % 2) == 0:
			root.canvas.itemconfigure(root.label, text=f"{remaining_time_str}", fill="red")
		if int(remaining_time % 2) == 1:
			root.canvas.itemconfigure(root.label, text=f"{remaining_time_str}", fill="white")
		if remaining_time <= 0:
			root.canvas.itemconfigure(root.label, text=f"YOU ARE FREE !!!", fill="green")
			if locked:
				lock_window.canvas.itemconfigure(lock_label, text=f"YOU ARE FREE !!!")
			CheckScreen()
			return
		CheckScreen()
		if locked:
			lock_window.canvas.itemconfigure(lock_label, text=f"{remaining_time_str}")
		return
	remaining_time_str = str(datetime.utcfromtimestamp(remaining_time).strftime("%H:%M:%S"))
	root.canvas.itemconfigure(root.label, text=f"{remaining_time_str}")
	if locked:
		lock_window.canvas.itemconfigure(lock_label, text=f"{remaining_time_str}")
	CheckScreen()

logSaveFile = "/home/jauffret/Documents/42alternanceLockScreen/saveLog.json"
offset = 0
user = os.getlogin()
screen_off_timeout = 15

last_login_time = get_last_login_time()
if last_login_time.hour < 8:
    last_login_time = last_login_time.replace(hour = 8, minute = 0, second = 0, microsecond = 0)
get_previous_login_time()
if last_login_time is None:
    exit()

current_time = datetime.now()
time_difference = current_time - last_login_time

root = tk.Tk()
root.title("Time remaning...")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg="black")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)
root.geometry(f"300x48+{screen_width-460}+0")

label = canvas.create_text(150, 30, text=f"{time_difference}", font=("Helvetica", 16), fill="white", anchor="center", justify="center")
root.label = label
root.canvas = canvas

locked = False
screen_off_timer = screen_off_timeout
screen_off = False

root.after(1, UpdateLabelTime)
root.after(1000, PreventLock)
root.after(1000, screen_off_locked)

def reset_screen_off_timer():
	global screen_off_timer
	screen_off_timer = 15

def big_time():
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	root.canvas.itemconfigure(root.label, font=("Helvetica", 20))
	root.canvas.coords(root.label, screen_width // 2, screen_height // 2)

def small_time():
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	root.canvas.itemconfigure(root.label, font=("Helvetica", 30))
	root.canvas.coords(root.label, screen_width - 150, screen_height - 20)

pressed_keys = set()

def key_press_listener(key):
	global pressed_keys
	try:
		pressed_keys.add(key.char)
	except AttributeError:
		pressed_keys.add(key)
	if pressed_keys == {"Super_L", "l"}:
		Lock()
	if pressed_keys == {"Super_L", "Escape"}:
		OnEscape()

def key_release_listener(key):
	global pressed_keys
	try:
		pressed_keys.remove(key.char)
	except KeyError:
		pressed_keys.remove(key)
	except AttributeError:
		pressed_keys.remove(key)

root.bind_all('<Key>', lambda e: reset_screen_off_timer())
root.bind_all('<Motion>', lambda e: reset_screen_off_timer())
root.bind('<Up>', lambda e: big_time())
root.bind('<Down>', lambda e: small_time())

keyboard.Listener(on_press=key_press_listener, on_release=key_release_listener).start()

root.mainloop()