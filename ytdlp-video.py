import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import platform
import os
from os.path import expanduser, join

# =========================
# THEME: 
# =========================
THEME = {
    "bg": "#161822",          
    "panel": "#2C3044",       
    "text": "#fdfdfd",
    "text2": "#b9c0cc",
    "text-selected": "#ff00c8",       
    "muted": "#b0b1b3",       
    "button_bg": "#161822",   
    "button_fg": "#2b2b2b",   
    "accent": "#00FF2A",      
    "ok": "#38b000",          
    "err": "#e01e37",         
    "info": "#5087ff"         
}

# =========================
# General
# =========================
cookie_source = "cookies.txt"

# The directory and file name of yt-dlp
if platform.system() == "Windows":
    yt_dlp = "yt-dlp.exe"
else:
    yt_dlp = "/usr/bin/yt-dlp"

# User's home directory and download folder
home = expanduser("~")
download_folder = join(home, "Downloads/Video/Ytdlp")

# If the user doesn't choose any quality option, the default is 720p
default_res = 720
height_limit = 720 * 1.25


# =========================
# Funcs.
# =========================
def select_directory():
    global download_folder
    download_folder = filedialog.askdirectory()
    return download_folder

def update_ytdlp():
    command = ["yt_dlp", "-U"]
    messagebox.showinfo("Update", "Checking new version of yt-dlp ..")
    subprocess.run(command, check=True)

def user_input():
    """Returns user input and appropriate yt-dlp parameters based on the entered link."""
    if entry.get() and not entryplaylist.get():
        return entry.get(), get_single_video_parameters()
    elif not entry.get() and entryplaylist.get():
        return entryplaylist.get(), get_playlist_parameters()
    else:
        return "", []

def set_status(text, level="info"):
    """Update the status label."""
    color = THEME.get(level, THEME["info"])
    status_label.config(text=text, foreground=color)
    root.update_idletasks()

def run_download(event=None):
    """Runs the download process and provides real-time feedback to the user."""  
    user_input_value, ytdlp_parameters = user_input()
    if user_input_value:
        set_status("Preparing download...", "info")
        command = [yt_dlp, user_input_value] + ytdlp_parameters
        try:
            progress_bar.start()
            subprocess.run(command, check=True)
            progress_bar.stop()
            set_status("Download complete!", "ok")
            show_completion_message()
        except subprocess.CalledProcessError as e:
            progress_bar.stop()
            set_status(f"Error: {e}", "err")
        finally:
            root.update_idletasks()
    else:
        set_status("No valid input provided!", "err")

def show_completion_message():
    messagebox.showinfo("All Set!", "Your downloads are ready!\nEnjoy your content!")
    open_folder_prompt()

def open_folder_prompt():
    open_folder = messagebox.askyesno("Open Downloads Folder", "Do you want to open the Downloads folder?")
    if open_folder:
        open_destination_folder()

def open_destination_folder():
    if platform.system() == "Windows":
        os.startfile(download_folder)
    elif platform.system() == "Darwin":
        subprocess.run(["open", download_folder])
    else:
        subprocess.run(["xdg-open", download_folder])

def clicked():
    """Updates the quality label when a radio button is clicked."""
    global height_limit
    height_limit = qualityis.get() * 1.25
    selected_value = qualityis.get()

    # Tüm butonları dolaş
    for rb in radio_buttons:
        if rb.cget("value") == selected_value:
            rb.config(fg=THEME["accent"])   # seçilen: yeşil yazı
        else:
            rb.config(fg=THEME["muted"])   # diğerleri: beyaz


def get_single_video_parameters():
    return [
        "--cookies", cookie_source,
        "--sleep-interval", "2",
        "--sponsorblock-remove", "all,-music_offtopic",
        "--sponsorblock-mark", "all",
        "--embed-thumbnail",
        "--embed-metadata",
        "-f", f"bv[height<{height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv]/bv[height<{height_limit}]+ba/b",
        "-o", "%(channel)s/%(title)s - %(width)s x %(height)sp.%(ext)s",
        "-P", download_folder
    ]

def get_playlist_parameters():
    return [
        "--cookies", cookie_source,
        "--sleep-interval", "5",
        "--sponsorblock-remove", "all,-music_offtopic",
        "--sponsorblock-mark", "all",
        "--embed-thumbnail",
        "--embed-metadata",
        "-f", f"bv[height<{height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv]/bv[height<{height_limit}]+ba/b",
        "-o", "%(channel)s/%(playlist)s/%(playlist_index)s - %(title)s - %(width)s x %(height)sp.%(ext)s",
        "-P", download_folder
    ]

def clear_entry():
    entry.delete(0, tk.END)
    entryplaylist.delete(0, tk.END)

def pick_bg_color():
    """(Opsiyonel) Tek tıkla arka plan rengi değiştir."""
    color = colorchooser.askcolor(title="Choose background color", initialcolor=THEME["bg"])[1]
    if color:
        THEME["bg"] = color
        apply_theme()  # temayı yeniden uygula


# =========================
# GUI setup
# =========================
root = tk.Tk(className="ytdlp-Vids")
root.title("YT-DLP GUI for Videos")
window_width = 350
window_height = 400
root.geometry(f"{window_width}x{window_height}")
root.resizable(False, False)

# ttk style
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("TProgressbar", troughcolor=THEME["panel"], background=THEME["accent"])

def apply_theme():
    """Apply the selected theme."""
    root.config(bg=THEME["bg"], padx=5, pady=5)

    
    for btn in (button_update, clear_button, choose_dest_button, download_button, theme_button):
        try:
            btn.config(bg=THEME["button_bg"], fg=THEME["text2"],
                       activebackground=THEME["panel"], activeforeground=THEME["text"])
        except Exception:
            pass

    
    for w in (label_single, label_playlist, label_quality, status_label):
        w.config(bg=THEME["bg"], fg=THEME["text"])

    entry.config(bg="white", fg="black")           # making entry boxes light usually better
    entryplaylist.config(bg="white", fg="black")

    quality_frame.config(bg=THEME["panel"])
    for rb in radio_buttons:
        if rb.cget("value") == qualityis.get():
            rb.config(fg=THEME["accent"])

    # ttk progressbar settings already setted in the style

    root.update_idletasks()




# Update Button (Only on Windows OS)
button_update = tk.Button(
    root, text="↻ Update", command=update_ytdlp, font=("Bahnschrift", 8),
    bg=THEME["button_bg"], fg=THEME["button_fg"], relief=tk.FLAT, padx=2, pady=2
)
if platform.system() == "Windows":
    button_update.place(x=(window_width - 75), y=5)

# Clear Button
clear_button = tk.Button(
    root, text="CLEAR ALL 🧼", command=clear_entry, font=("Bahnschrift", 8),
    bg=THEME["button_bg"], fg=THEME["button_fg"], relief=tk.FLAT, padx=2, pady=2
)
clear_button.place(x=5, y=5)

# Theme button
theme_button = tk.Button(
    root, text="🎨 Theme", command=pick_bg_color, font=("Bahnschrift", 8),
    bg=THEME["button_bg"], fg=THEME["button_fg"], relief=tk.FLAT, padx=2, pady=2
)
theme_button.place(x=100, y=5)

# Input
label_single = tk.Label(root, text="Enter Link for Single Video:")
label_single.pack(pady=(35, 5))
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=0)
entry.bind("<Return>", run_download)
entry.bind("<KP_Enter>", run_download)

label_playlist = tk.Label(root, text="Enter Link for Playlist:")
label_playlist.pack(pady=5)
entryplaylist = tk.Entry(root, width=50)
entryplaylist.pack(padx=10, pady=0)
entryplaylist.bind("<Return>", run_download)
entryplaylist.bind("<KP_Enter>", run_download)

# Quality Options
label_quality = tk.Label(root, text="Select Quality:", font=("Bahnschrift", 10, "bold"))
label_quality.pack(pady=2)

qualityis = tk.IntVar(value=default_res)
quality_frame = tk.Frame(root, bg=THEME["panel"])
quality_frame.pack(pady=5)

global radio_buttons
radio_buttons = []  # global list


quality_options = [
    ("360p", 360), ("480p", 480), ("720p", 720),
    ("1080p", 1080), ("1440p - 2K", 1440), ("2160p - 4K", 2160),
    ("4320p - 8K", 4320), ("6480p - 12K", 6480), ("8640p - 16K", 8640)
]


for i, (text, value) in enumerate(quality_options):
    rb = tk.Radiobutton(
        quality_frame,
        text=text,
        command=clicked,
        bg=THEME["panel"],
        fg=THEME["muted"],         # varsayılan beyaz/grimsi
        selectcolor=THEME["text2"],  # seçildiğinde işaret yeşil
        activebackground=THEME["panel"],
        activeforeground="white",
        variable=qualityis,
        value=value,
        font=("Bahnschrift", 9)
    )
    rb.grid(row=i // 3, column=i % 3, padx=2, pady=2)
    radio_buttons.append(rb)




# Destination folder
choose_dest_button = tk.Button(root, text="Choose destination folder ...", command=select_directory,fg="#B3B3B3")
choose_dest_button.pack(pady=10)

# Progress and status
progress_bar = ttk.Progressbar(root, mode="determinate")
progress_bar.pack(pady=4, fill="x")

status_label = tk.Label(root, text="Ready", bg=THEME["bg"], fg=THEME["info"])
status_label.pack(pady=0)

# Download button
download_button = tk.Button(root, text="Download IT", command=run_download)
download_button.pack(pady=4)

apply_theme()
root.mainloop()
