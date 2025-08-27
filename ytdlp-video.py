import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import platform
import os
from os.path import expanduser, join


global cookie_source
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


def clear_entry():
    entry.delete(0, tk.END)
    entryplaylist.delete(0, tk.END)

def select_directory():
    global download_folder
    download_folder = filedialog.askdirectory()
    return download_folder


# if you using yt-dlp binary app with your package manager (chocolate, snap, flatpak, apt, pacman etc) there is no need to use update button
def update_ytdlp():
    command = ["yt-dlp", "-U"]
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



def run_download(event=None):
    """Runs the download process and provides real-time feedback to the user."""  
    user_input_value, ytdlp_parameters = user_input()
    if user_input_value:
        status_label.config(text="Preparing download...", foreground="blue")
        root.update_idletasks()
        command = [yt_dlp, user_input_value] + ytdlp_parameters
        try:
            progress_bar.start()
            subprocess.run(command, check=True)
            progress_bar.stop()
            status_label.config(text="Download complete!", foreground="green")
            show_completion_message()
        except subprocess.CalledProcessError as e:
            progress_bar.stop()
            status_label.config(text=f"Error: {e}", foreground="red")
        finally:
            root.update_idletasks()
    else:
        status_label.config(text="No valid input provided!", foreground="red")


def show_completion_message():
    """Displays a notification when the download is finished and asks to open the folder."""
    messagebox.showinfo("All Set!", "Your downloads are ready!\nEnjoy your content!")
    open_folder_prompt()


def open_folder_prompt():
    """Prompts the user to open the downloads folder."""
    open_folder = messagebox.askyesno(
        "Open Downloads Folder", "Do you want to open the Downloads folder?"
    )
    if open_folder:
        open_destination_folder()


def open_destination_folder():
    """Opens the destination folder in the system's file manager."""
    if platform.system() == "Windows":
        os.startfile(download_folder)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", download_folder])
    else:  # Linux
        subprocess.run(["xdg-open", download_folder])


def clicked():
    """Updates the quality label when a radio button is clicked."""
    global height_limit
    height_limit = qualityis.get() * 1.25


def get_single_video_parameters():
    """Returns yt-dlp parameters for a single video."""
    return [
        "--cookies", cookie_source,
        "--sleep-interval", "2",
        "--sponsorblock-remove", "all,-music_offtopic",
        "--sponsorblock-mark", "all",
        "--embed-thumbnail",
        "--embed-metadata",
        "-f", f"bv[height<{height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv] / bv[height<{height_limit}]+ba/b",
        "-o", "%(channel)s/%(title)s - %(width)s x %(height)sp.%(ext)s",
        "-P", download_folder
    ]


def get_playlist_parameters():
    """Returns yt-dlp parameters for a playlist."""
    return [
        "--cookies", cookie_source,
        "--sleep-interval", "5",  
        "--sponsorblock-remove", "all,-music_offtopic",
        "--sponsorblock-mark", "all",
        "--embed-thumbnail",
        "--embed-metadata",
        "-f", f"bv[height<{height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv] / bv[height<{height_limit}]+ba/b",
        "-o", "%(channel)s/%(playlist)s/%(playlist_index)s - %(title)s - %(width)s x %(height)sp.%(ext)s",
        "-P", download_folder
    ]

# Create the main window
root = tk.Tk(className="ytdlp-Vids")
root.title("YT-DLP GUI for Videos")
root.config(bg="#161822", padx=5, pady=5)
window_width = 350
window_height = 380
root.geometry(f"{window_width}x{window_height}")  # Set window size
root.resizable(False, False)  # Disable resizing

# Update Button
if platform.system() == "Windows":
    button_update = tk.Button(
    root, text="↻ Update", command=update_ytdlp, font=("Bahnschrift", 8),
    bg="#161822", fg="#2b2b2b", relief=tk.FLAT, padx=2, pady=2
)
    button_update.pack(padx=1,pady=1)
    button_update.place(x=(window_width-75), y=5)



# Clear Button
clear_button = tk.Button(
    root, text="CLEAR ALL 🧼", command=clear_entry, font=("Bahnschrift", 8),
    bg="#161822", fg="#2b2b2b", relief=tk.FLAT, padx=2, pady=2
)
clear_button.pack(padx=1,pady=1)
clear_button.place(x=5, y=5)


# Input for single video
tk.Label(root, text="Enter Link for Single Video:").pack(pady=5)
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=0)
entry.bind("<Return>", run_download)
entry.bind("<KP_Enter>", run_download)

# Input for playlist
tk.Label(root, text="Enter Link for Playlist:").pack(pady=5)
entryplaylist = tk.Entry(root, width=50)
entryplaylist.pack(padx=10, pady=0)
entryplaylist.bind("<Return>", run_download)
entryplaylist.bind("<KP_Enter>", run_download)


# Quality selection with modern style
tk.Label(root, text="Select Quality:", font=("Bahnschrift", 10, "bold")).pack(pady=2)
qualityis = tk.IntVar(value=default_res)
quality_frame = tk.Frame(root, bg="#2C3044")
quality_frame.pack(pady=5)

quality_options = [
    ("360p", 360), ("480p", 480), ("720p", 720),
    ("1080p", 1080), ("1440p - 2K", 1440), ("2160p - 4K", 2160),
    ("4320p - 8K", 4320), ("6480p - 12K", 6480), ("8640p - 16K", 8640)
]

# Grid layout: 3 items per row
for i, (text, value) in enumerate(quality_options):
    tk.Radiobutton(
        quality_frame, text=text, command=clicked, background="#fdfdfd",
        variable=qualityis, value=value, font=("Bahnschrift", 9)
    ).grid(row=i // 3, column=i % 3, padx=2, pady=2)


for text, value in quality_options:
    tk.Radiobutton(
        quality_frame, text=text, command=clicked, background="#25dd25",
        variable=qualityis, value=value
    )


# Select destination for vids
tk.Button(root, text="Choose destination folder ...", command=select_directory).pack(pady=10)


# Progress bar and status
progress_bar = ttk.Progressbar(root, mode="determinate")
progress_bar.pack(pady=4, fill="x")
status_label = tk.Label(root, text="Ready", foreground="blue")
status_label.pack(pady=0)

# Download button
tk.Button(root, text="Download IT", command=run_download).pack(pady=4)

# Run the GUI
root.mainloop()
