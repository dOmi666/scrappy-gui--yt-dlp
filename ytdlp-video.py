import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import platform
import os
import json
import threading
import queue
import re
from datetime import datetime
from os.path import expanduser, join, exists
from urllib.parse import urlparse

class YTDLPGui:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_initial_config()
        self.load_settings()
        self.setup_variables()
        self.setup_gui()
        self.setup_threading()
        
    def setup_initial_config(self):
        """Initialize basic configuration"""
        self.THEME = {
            "bg": "#1F1622",
            "panel": "#1D202E",
            "text": "#fdfdfd",
            "text2": "#b9c0cc",
            "text_selected": "#67d884",
            "muted": "#b0b1b3",
            "button_bg": "#161822",
            "button_fg": "#2b2b2b",
            "accent": "#00FF15",
            "ok": "#38b000",
            "err": "#e01e37",
            "info": "#5087ff"
        }
        
        self.cookie_source = "cookies.txt"
        self.yt_dlp = "yt-dlp.exe" if platform.system() == "Windows" else "/usr/bin/yt-dlp"
        self.home = expanduser("~")
        self.default_download_folder = join(self.home, "Downloads/Video/Ytdlp")
        self.settings_file = "ytdlp_settings.json"
        
    def load_settings(self):
        """Load user settings from file"""
        default_settings = {
            "download_folder": self.default_download_folder,
            "default_quality": 720,
            "theme": self.THEME,
            "download_history": []
        }
        
        try:
            if exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    # Merge with defaults to handle new settings
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
            else:
                settings = default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            settings = default_settings
            
        self.download_folder = settings["download_folder"]
        self.default_quality = settings["default_quality"]
        self.THEME = settings["theme"]
        self.download_history = settings.get("download_history", [])
        
    def save_settings(self):
        """Save current settings to file"""
        settings = {
            "download_folder": self.download_folder,
            "default_quality": self.quality_var.get(),
            "theme": self.THEME,
            "download_history": self.download_history[-50:]  # Keep last 50 downloads
        }
        
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def setup_variables(self):
        """Initialize GUI variables"""
        self.quality_var = tk.IntVar(value=self.default_quality)
        self.height_limit = self.default_quality * 1.25
        self.is_downloading = False
        self.current_download_info = {}
        self.download_process = None
        
    def setup_threading(self):
        """Setup threading components"""
        self.download_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.root.after(100, self.process_progress_queue)
        
    def setup_gui(self):
        """Setup the main GUI"""
        self.root.title("YT-DLP GUI")
        self.root.geometry("350x750")
        self.root.resizable(False, False)
        
        # Setup style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
            
        self.create_widgets()
        self.apply_theme()
        self.setup_bindings()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        self.create_menu()
        self.create_toolbar()
        self.create_input_section()
        self.create_quality_section()
        self.create_options_section()
        self.create_progress_section()
        self.create_control_buttons()
        self.create_status_section()
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        menubar.config(bg=self.THEME["panel"],fg=self.THEME["text"])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import URLs from file", command=self.import_urls)
        file_menu.add_command(label="Export Download History", command=self.export_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Update yt-dlp", command=self.update_ytdlp_threaded)
        tools_menu.add_command(label="Check yt-dlp version", command=self.check_version)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Download History", command=self.clear_history)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Download History", command=self.show_history)
        view_menu.add_command(label="Settings", command=self.show_settings)
        
    def create_toolbar(self):
        """Create toolbar with quick actions"""
        toolbar = tk.Frame(self.root, bg=self.THEME["panel"], height=35)
        toolbar.pack(fill="x", padx=5, pady=(5, 0))
        toolbar.pack_propagate(False)
        
        # Quick action buttons
        tk.Button(toolbar, text="🧹 Clear", command=self.clear_all,
                 font=("Arial", 8), bg=self.THEME["button_bg"], fg=self.THEME["text2"],
                 relief=tk.FLAT, padx=8, pady=2).pack(side="left", padx=2)
        
        tk.Button(toolbar, text="🎨 Theme", command=self.pick_theme_color,
                 font=("Arial", 8), bg=self.THEME["button_bg"], fg=self.THEME["text2"],
                 relief=tk.FLAT, padx=8, pady=2).pack(side="left", padx=2)
        
        tk.Button(toolbar, text="📁 Folder", command=self.open_download_folder,
                 font=("Arial", 8), bg=self.THEME["button_bg"], fg=self.THEME["text2"],
                 relief=tk.FLAT, padx=8, pady=2).pack(side="left", padx=2)
        
        if platform.system() == "Windows":
            tk.Button(toolbar, text="🔄 Update", command=self.update_ytdlp_threaded,
                     font=("Arial", 8), bg=self.THEME["button_bg"], fg=self.THEME["text2"],
                     relief=tk.FLAT, padx=8, pady=2).pack(side="right", padx=2)
                     
    def create_input_section(self):
        """Create input section for URLs"""
        input_frame = tk.LabelFrame(self.root, text="Input URLs", bg=self.THEME["bg"], 
                                   fg=self.THEME["text"], font=("Arial", 10, "bold"))
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Single video URL
        tk.Label(input_frame, text="Single Video URL:", bg=self.THEME["bg"], 
                fg=self.THEME["text"]).pack(anchor="w", padx=5, pady=(5, 2))
        
        self.single_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.single_entry.pack(fill="x", padx=5, pady=(0, 5))
        
        # Playlist URL
        tk.Label(input_frame, text="Playlist URL:", bg=self.THEME["bg"], 
                fg=self.THEME["text"]).pack(anchor="w", padx=5, pady=(5, 2))
        
        self.playlist_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.playlist_entry.pack(fill="x", padx=5, pady=(0, 5))
        
        # Batch URLs
        tk.Label(input_frame, text="Batch URLs (one per line):", bg=self.THEME["bg"], 
                fg=self.THEME["text"]).pack(anchor="w", padx=5, pady=(5, 2))
        
        batch_frame = tk.Frame(input_frame, bg=self.THEME["bg"])
        batch_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.batch_text = tk.Text(batch_frame, height=4, font=("Arial", 9))
        batch_scrollbar = tk.Scrollbar(batch_frame, orient="vertical", command=self.batch_text.yview)
        self.batch_text.config(yscrollcommand=batch_scrollbar.set)
        
        self.batch_text.pack(side="left", fill="both", expand=True)
        batch_scrollbar.pack(side="right", fill="y")
        
    def create_quality_section(self):
        """Create quality selection section"""
        quality_frame = tk.LabelFrame(self.root, text="Quality Settings", bg=self.THEME["panel"], 
                                     fg=self.THEME["text"], font=("Arial", 10, "bold"))
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        # Quality options
        self.radio_buttons = []
        quality_options = [
            ("360p", 360), ("480p", 480), ("720p", 720),
            ("1080p", 1080), ("1440p (2K)", 1440), ("2160p (4K)", 2160),
            ("4320p (8K)", 4320), ("Best Available", 99999)
        ]
        
        quality_grid = tk.Frame(quality_frame, bg=self.THEME["panel"])
        quality_grid.pack(fill="x", padx=5, pady=5)
        
        for i, (text, value) in enumerate(quality_options):
            rb = tk.Radiobutton(
                quality_grid, text=text, variable=self.quality_var, value=value,
                command=self.on_quality_change, bg=self.THEME["panel"],
                fg=self.THEME["muted"], selectcolor=self.THEME["text2"],
                activebackground=self.THEME["panel"], font=("Arial", 9)
            )
            rb.grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)
            self.radio_buttons.append(rb)
            
    def create_options_section(self):
        """Create additional options section"""
        options_frame = tk.LabelFrame(self.root, text="Download Options", bg=self.THEME["bg"], 
                                     fg=self.THEME["text"], font=("Arial", 10, "bold"))
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Options checkboxes
        self.audio_only_var = tk.BooleanVar()
        self.embed_subs_var = tk.BooleanVar(value=True)
        self.sponsorblock_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(options_frame, text="Audio Only (m4a)", variable=self.audio_only_var,
                      bg=self.THEME["bg"], fg=self.THEME["muted"], activebackground=self.THEME["bg"],
                      selectcolor=self.THEME["text_selected"]).pack(anchor="w", padx=5)
        
        tk.Checkbutton(options_frame, text="Embed Subtitles", variable=self.embed_subs_var,
                      bg=self.THEME["bg"], fg=self.THEME["text"], 
                      selectcolor=self.THEME["text2"]).pack(anchor="w", padx=5)
        
        tk.Checkbutton(options_frame, text="Skip Sponsors (SponsorBlock)", variable=self.sponsorblock_var,
                      bg=self.THEME["bg"], fg=self.THEME["text"], 
                      selectcolor=self.THEME["text2"]).pack(anchor="w", padx=5)
        
        # Destination folder
        dest_frame = tk.Frame(options_frame, bg=self.THEME["bg"])
        dest_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(dest_frame, text="Download Folder:", bg=self.THEME["bg"], 
                fg=self.THEME["text"]).pack(anchor="w")
        
        folder_frame = tk.Frame(dest_frame, bg=self.THEME["bg"])
        folder_frame.pack(fill="x", pady=2)
        
        self.folder_label = tk.Label(folder_frame, text=self.download_folder, 
                                   bg="white", fg="black", relief="sunken", anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(folder_frame, text="Browse", command=self.select_directory,
                 bg=self.THEME["button_bg"], fg=self.THEME["text2"]).pack(side="right")
                 
    def create_progress_section(self):
        """Create enhanced progress section"""
        progress_frame = tk.LabelFrame(self.root, text="Download Progress", bg=self.THEME["bg"], 
                                      fg=self.THEME["text"], font=("Arial", 10, "bold"))
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        # Main progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # Progress info grid
        info_frame = tk.Frame(progress_frame, bg=self.THEME["bg"])
        info_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Left column - Status and current file
        left_frame = tk.Frame(info_frame, bg=self.THEME["bg"])
        left_frame.pack(side="left", fill="both", expand=True)
        
        self.progress_label = tk.Label(left_frame, text="Ready", bg=self.THEME["bg"], 
                                     fg=self.THEME["info"], font=("Arial", 9))
        self.progress_label.pack(anchor="w")
        
        self.current_file_label = tk.Label(left_frame, text="", bg=self.THEME["bg"], 
                                         fg=self.THEME["text2"], font=("Arial", 8),
                                         wraplength=250)
        self.current_file_label.pack(anchor="w")
        
        # Right column - Speed and ETA
        right_frame = tk.Frame(info_frame, bg=self.THEME["bg"])
        right_frame.pack(side="right", fill="y")
        
        self.speed_label = tk.Label(right_frame, text="", bg=self.THEME["bg"], 
                                  fg=self.THEME["muted"], font=("Arial", 8))
        self.speed_label.pack(anchor="e")
        
        self.eta_label = tk.Label(right_frame, text="", bg=self.THEME["bg"], 
                                fg=self.THEME["muted"], font=("Arial", 8))
        self.eta_label.pack(anchor="e")
        
        # Detailed info section (collapsible)
        detail_frame = tk.Frame(progress_frame, bg=self.THEME["bg"])
        detail_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Size info
        size_frame = tk.Frame(detail_frame, bg=self.THEME["bg"])
        size_frame.pack(fill="x")
        
        self.size_label = tk.Label(size_frame, text="", bg=self.THEME["bg"], 
                                 fg=self.THEME["text2"], font=("Arial", 8))
        self.size_label.pack(side="left")
        
        self.percent_label = tk.Label(size_frame, text="", bg=self.THEME["bg"], 
                                    fg=self.THEME["accent"], font=("Arial", 8, "bold"))
        self.percent_label.pack(side="right")
        
    def create_control_buttons(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.root, bg=self.THEME["bg"])
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Download button
        self.download_btn = tk.Button(button_frame, text="🚀 Start Download", 
                                    command=self.start_download,
                                    bg=self.THEME["accent"], 
                                    font=("Arial", 11, "bold"), pady=8)
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Cancel button
        self.cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                                  command=self.cancel_download,
                                  bg=self.THEME["err"], fg="white", 
                                  font=("Arial", 10), pady=8, state="disabled")
        self.cancel_btn.pack(side="right", padx=(5, 0))
        
    def create_status_section(self):
        """Create status section"""
        status_frame = tk.Frame(self.root, bg=self.THEME["panel"], height=25)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", bg=self.THEME["panel"], 
                                   fg=self.THEME["info"], font=("Arial", 9))
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Connection status
        self.connection_label = tk.Label(status_frame, text="●", bg=self.THEME["panel"], 
                                       fg=self.THEME["ok"], font=("Arial", 12))
        self.connection_label.pack(side="right", padx=10, pady=5)
        
    def setup_bindings(self):
        """Setup keyboard bindings and drag-drop"""
        self.root.bind("<Control-v>", self.paste_url)
        self.root.bind("<Return>", lambda e: self.start_download())
        self.root.bind("<Escape>", lambda e: self.cancel_download())
        
        # Bind entries for Enter key
        self.single_entry.bind("<Return>", lambda e: self.start_download())
        self.playlist_entry.bind("<Return>", lambda e: self.start_download())
        
        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    # Progress Parsing Functions
    def parse_yt_dlp_output(self, line):
        """Parse yt-dlp output line and extract progress information"""
        line = line.strip()
        if not line:
            return None
            
        progress_info = {}
        
        # Download progress pattern
        download_pattern = r'\[download\]\s+(\d+\.?\d*)%\s+of\s+([^\s]+)\s+at\s+([^\s]+)\s+ETA\s+([^\s]+)'
        match = re.search(download_pattern, line)
        if match:
            progress_info = {
                'type': 'progress',
                'percent': float(match.group(1)),
                'size': match.group(2),
                'speed': match.group(3),
                'eta': match.group(4)
            }
            return progress_info
        
        # Alternative download progress pattern (simpler)
        simple_progress_pattern = r'\[download\]\s+(\d+\.?\d*)%'
        match = re.search(simple_progress_pattern, line)
        if match:
            progress_info = {
                'type': 'progress',
                'percent': float(match.group(1))
            }
            return progress_info
        
        # File extraction pattern
        if '[download] Destination:' in line:
            filename = line.split('[download] Destination:')[1].strip()
            progress_info = {
                'type': 'file_info',
                'filename': os.path.basename(filename)
            }
            return progress_info
        
        # Starting download pattern
        if '[download]' in line and 'Downloading' in line:
            progress_info = {
                'type': 'start',
                'message': line
            }
            return progress_info
            
        # Finished download pattern
        if '[download] 100%' in line or 'has already been downloaded' in line:
            progress_info = {
                'type': 'complete',
                'message': line
            }
            return progress_info
            
        # Error pattern
        if 'ERROR:' in line:
            progress_info = {
                'type': 'error',
                'message': line
            }
            return progress_info
            
        # Info pattern
        if '[info]' in line:
            progress_info = {
                'type': 'info',
                'message': line
            }
            return progress_info
            
        return None
        
    # Event Handlers
    def on_quality_change(self):
        """Handle quality selection change"""
        selected_value = self.quality_var.get()
        self.height_limit = selected_value * 1.25 if selected_value != 99999 else 999999
        
        # Update radio button colors
        for rb in self.radio_buttons:
            if rb.cget("value") == selected_value:
                rb.config(fg=self.THEME["accent"])
            else:
                rb.config(fg=self.THEME["muted"])
                
    def on_closing(self):
        """Handle window closing"""
        self.save_settings()
        if self.is_downloading:
            if messagebox.askokcancel("Quit", "Download in progress. Do you want to cancel and quit?"):
                self.cancel_download()
                self.root.destroy()
        else:
            self.root.destroy()
            
    # URL Validation
    def validate_url(self, url):
        """Validate if URL is supported"""
        if not url.strip():
            return False, "Empty URL"
            
        # Basic URL validation
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False, "Invalid URL format"
        except Exception:
            return False, "Invalid URL format"
            
        # Check for supported platforms (you can extend this)
        supported_domains = [
            'youtube.com', 'youtu.be', 'youtube-nocookie.com',
            'vimeo.com', 'dailymotion.com', 'twitch.tv'
        ]
        
        domain = result.netloc.lower()
        domain = domain.replace('www.', '')
        
        if not any(supported in domain for supported in supported_domains):
            return True, "URL might not be supported, but will try"
            
        return True, "Valid URL"
        
    def get_urls_to_download(self):
        """Get all URLs from input fields"""
        urls = []
        
        # Single video
        single_url = self.single_entry.get().strip()
        if single_url:
            urls.append(single_url)
            
        # Playlist
        playlist_url = self.playlist_entry.get().strip()
        if playlist_url:
            urls.append(playlist_url)
            
        # Batch URLs
        batch_text = self.batch_text.get("1.0", tk.END).strip()
        if batch_text:
            batch_urls = [url.strip() for url in batch_text.split('\n') if url.strip()]
            urls.extend(batch_urls)
            
        return urls
        
    # Download Functions
    def get_download_parameters(self, url):
        """Get yt-dlp parameters based on settings"""
        params = ["--no-warnings", "--ignore-errors", "--newline"]
        
        # Quality settings
        if self.quality_var.get() != 99999:
            if self.audio_only_var.get():
                params.extend(["-f", "ba[ext=m4a]"])
            else:
                params.extend(["-f", f"bv[height<{self.height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv]/bv[height<{self.height_limit}]+ba/b"])
        else:
            if self.audio_only_var.get():
                params.extend(["-f", "ba[ext=m4a]"])
            else:
                params.extend(["-f", f"bv[height<{self.height_limit}][ext=mkv]+ba[ext=m4a]/b[ext=mkv]/bv[height<{self.height_limit}]+ba/b"])
                
        # Additional options
        if self.embed_subs_var.get():
            params.extend(["--write-subs", "--write-auto-subs", "--sub-lang", "en,tr"])
            
        if self.sponsorblock_var.get():
            params.extend(["--sponsorblock-remove", "all,-music_offtopic"])
            
        # Metadata and thumbnails
        if not self.audio_only_var.get():
            params.extend(["--embed-thumbnail", "--embed-metadata"])
            
        # Output template
        if "playlist" in url.lower() or "list=" in url:
            params.extend(["-o", "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"])
        else:
            params.extend(["-o", "%(channel)s/%(title)s - %(width)s x %(height)sp.%(ext)s"])
            
        # Download path
        params.extend(["-P", self.download_folder])
        
        # Cookies if available
        if exists(self.cookie_source):
            params.extend(["--cookies", self.cookie_source])
            
        # Rate limiting
        params.extend(["--sleep-interval", "1", "--max-sleep-interval", "5"])
        
        return params
        
    def start_download(self):
        """Start download process"""
        if self.is_downloading:
            messagebox.showwarning("Download in Progress", "A download is already in progress!")
            return
            
        urls = self.get_urls_to_download()
        if not urls:
            messagebox.showerror("No URLs", "Please enter at least one URL to download!")
            return
            
        # Validate URLs
        invalid_urls = []
        for url in urls:
            is_valid, message = self.validate_url(url)
            if not is_valid:
                invalid_urls.append(f"{url}: {message}")
                
        if invalid_urls and len(invalid_urls) == len(urls):
            messagebox.showerror("Invalid URLs", "All URLs are invalid:\n\n" + "\n".join(invalid_urls))
            return
        elif invalid_urls:
            result = messagebox.askyesno("Some Invalid URLs", 
                                       f"Some URLs might be invalid:\n\n" + "\n".join(invalid_urls) + 
                                       "\n\nDo you want to continue with valid URLs?")
            if not result:
                return
                
        # Start download in separate thread
        self.is_downloading = True
        self.download_btn.config(state="disabled", text="Downloading...")
        self.cancel_btn.config(state="normal")
        self.progress_bar.config(mode="determinate", value=0)
        
        # Reset progress display
        self.current_file_label.config(text="")
        self.speed_label.config(text="")
        self.eta_label.config(text="")
        self.size_label.config(text="")
        self.percent_label.config(text="")
        
        download_thread = threading.Thread(target=self.download_worker, args=(urls,))
        download_thread.daemon = True
        download_thread.start()
        
    def download_worker(self, urls):
        """Worker function for downloading with real-time progress"""
        try:
            for i, url in enumerate(urls):
                if not self.is_downloading:  # Check if cancelled
                    break
                    
                self.progress_queue.put(("status", f"Processing URL {i+1}/{len(urls)}"))
                self.progress_queue.put(("current_url", url))
                
                # Validate URL again
                is_valid, _ = self.validate_url(url)
                if not is_valid:
                    self.progress_queue.put(("error", f"Skipping invalid URL: {url}"))
                    continue
                    
                # Get parameters and build command
                params = self.get_download_parameters(url)
                command = [self.yt_dlp] + params + [url]
                
                # Execute download with real-time output
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    self.download_process = process
                    
                    # Read output line by line
                    for line in iter(process.stdout.readline, ''):
                        if not self.is_downloading:  # Check if cancelled
                            process.terminate()
                            break
                            
                        if line:
                            # Parse the output line
                            progress_info = self.parse_yt_dlp_output(line)
                            if progress_info:
                                self.progress_queue.put(("progress_update", progress_info))
                                
                    # Wait for process to complete
                    process.wait()
                    
                    if process.returncode == 0 and self.is_downloading:
                        self.progress_queue.put(("success", f"Downloaded: {url}"))
                        # Add to history
                        self.download_history.append({
                            "url": url,
                            "timestamp": datetime.now().isoformat(),
                            "status": "success"
                        })
                    elif self.is_downloading:  # Failed but not cancelled
                        self.progress_queue.put(("error", f"Failed to download: {url}"))
                        self.download_history.append({
                            "url": url,
                            "timestamp": datetime.now().isoformat(),
                            "status": "failed"
                        })
                        
                except Exception as e:
                    self.progress_queue.put(("error", f"Error downloading {url}: {str(e)}"))
                    self.download_history.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed",
                        "error": str(e)
                    })
                    
        except Exception as e:
            self.progress_queue.put(("error", f"Unexpected error: {str(e)}"))
        finally:
            self.download_process = None
            self.progress_queue.put(("complete", "Download process completed"))
            
    def cancel_download(self):
        """Cancel current download"""
        if self.is_downloading:
            self.is_downloading = False
            if self.download_process:
                try:
                    self.download_process.terminate()
                    self.download_process.wait(timeout=5)
                except:
                    try:
                        self.download_process.kill()
                    except:
                        pass
            self.progress_queue.put(("cancelled", "Download cancelled by user"))
            
    def process_progress_queue(self):
        """Process messages from download thread"""
        try:
            while True:
                message_type, message = self.progress_queue.get_nowait()
                
                if message_type == "status":
                    self.set_status(message, "info")
                elif message_type == "current_url":
                    self.current_file_label.config(text=f"URL: {message[:60]}...")
                elif message_type == "progress_update":
                    self.update_progress_display(message)
                elif message_type == "success":
                    self.set_status(message, "ok")
                elif message_type == "error":
                    self.set_status(message, "err")
                elif message_type == "cancelled":
                    self.set_status(message, "err")
                    self.reset_download_ui()
                elif message_type == "complete":
                    self.set_status("All downloads completed!", "ok")
                    self.reset_download_ui()
                    self.show_completion_dialog()
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_progress_queue)
            
    def update_progress_display(self, progress_info):
        """Update the progress display with parsed information"""
        if progress_info['type'] == 'progress':
            percent = progress_info.get('percent', 0)
            self.progress_bar.config(value=percent)
            self.percent_label.config(text=f"{percent:.1f}%")
            
            if 'speed' in progress_info:
                self.speed_label.config(text=f" {progress_info['speed']}")
            if 'eta' in progress_info:
                self.eta_label.config(text=f"ETA: {progress_info['eta']}")
            if 'size' in progress_info:
                self.size_label.config(text=f"Size: {progress_info['size']}")
                
        elif progress_info['type'] == 'file_info':
            filename = progress_info.get('filename', '')
            self.current_file_label.config(text=f"File: {filename[:50]}...")
            
        elif progress_info['type'] == 'start':
            self.progress_label.config(text="Starting download...", fg=self.THEME["info"])
            self.progress_bar.config(value=0)
            
        elif progress_info['type'] == 'complete':
            self.progress_label.config(text="Download completed", fg=self.THEME["ok"])
            self.progress_bar.config(value=100)
            self.percent_label.config(text="100%")
            
        elif progress_info['type'] == 'error':
            self.progress_label.config(text="Error occurred", fg=self.THEME["err"])
            
        elif progress_info['type'] == 'info':
            # Extract useful info messages
            message = progress_info.get('message', '')
            if 'Downloading' in message:
                self.progress_label.config(text="Downloading...", fg=self.THEME["info"])
                
    def reset_download_ui(self):
        """Reset UI after download completion/cancellation"""
        self.is_downloading = False
        self.download_btn.config(state="normal", text="🚀 Start Download")
        self.cancel_btn.config(state="disabled")
        self.progress_bar.config(value=0)
        
        # Clear progress info if cancelled
        if not self.is_downloading:
            self.current_file_label.config(text="")
            self.speed_label.config(text="")
            self.eta_label.config(text="")
            self.size_label.config(text="")
            self.percent_label.config(text="")
        
    def show_completion_dialog(self):
        """Show completion dialog with options"""
        result = messagebox.askyesno(
            "Download Complete!", 
            "Your downloads are ready!\n\nWould you like to open the download folder?",
            icon="question"
        )
        if result:
            self.open_download_folder()
            
    # Utility Functions
    def set_status(self, text, level="info"):
        """Update status label"""
        color = self.THEME.get(level, self.THEME["info"])
        self.status_label.config(text=text, foreground=color)
        if level != "info":  # Don't update progress label for routine info
            self.progress_label.config(text=text, foreground=color)
        
    def clear_all(self):
        """Clear all input fields"""
        self.single_entry.delete(0, tk.END)
        self.playlist_entry.delete(0, tk.END)
        self.batch_text.delete("1.0", tk.END)
        
    def select_directory(self):
        """Select download directory"""
        new_folder = filedialog.askdirectory(initialdir=self.download_folder)
        if new_folder:
            self.download_folder = new_folder
            self.folder_label.config(text=new_folder)
            
    def open_download_folder(self):
        """Open download folder in file explorer"""
        try:
            if platform.system() == "Windows":
                os.startfile(self.download_folder)
            elif platform.system() == "Darwin":
                subprocess.run(["open", self.download_folder])
            else:
                subprocess.run(["xdg-open", self.download_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
            
    def paste_url(self, event=None):
        """Paste URL from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                # Determine which field to paste to
                focused_widget = self.root.focus_get()
                if focused_widget == self.single_entry:
                    self.single_entry.delete(0, tk.END)
                    self.single_entry.insert(0, clipboard_text)
                elif focused_widget == self.playlist_entry:
                    self.playlist_entry.delete(0, tk.END)
                    self.playlist_entry.insert(0, clipboard_text)
                else:
                    # Default to single entry
                    self.single_entry.delete(0, tk.END)
                    self.single_entry.insert(0, clipboard_text)
        except Exception:
            pass
            
    def update_ytdlp_threaded(self):
        """Update yt-dlp in separate thread"""
        def update_worker():
            try:
                self.progress_queue.put(("status", "Checking for yt-dlp updates..."))
                result = subprocess.run([self.yt_dlp, "-U"], capture_output=True, text=True, check=True)
                self.progress_queue.put(("success", "yt-dlp updated successfully!"))
            except subprocess.CalledProcessError as e:
                self.progress_queue.put(("error", f"Update failed: {e.stderr}"))
            except Exception as e:
                self.progress_queue.put(("error", f"Update error: {str(e)}"))
                
        threading.Thread(target=update_worker, daemon=True).start()
        
    def check_version(self):
        """Check yt-dlp version"""
        def version_worker():
            try:
                result = subprocess.run([self.yt_dlp, "--version"], capture_output=True, text=True, check=True)
                version = result.stdout.strip()
                self.progress_queue.put(("success", f"yt-dlp version: {version}"))
            except Exception as e:
                self.progress_queue.put(("error", f"Could not get version: {str(e)}"))
                
        threading.Thread(target=version_worker, daemon=True).start()
        
    def import_urls(self):
        """Import URLs from text file"""
        file_path = filedialog.askopenfilename(
            title="Select URL file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f.readlines() if line.strip()]
                    
                if urls:
                    current_text = self.batch_text.get("1.0", tk.END).strip()
                    if current_text:
                        urls.insert(0, current_text)
                        
                    self.batch_text.delete("1.0", tk.END)
                    self.batch_text.insert("1.0", "\n".join(urls))
                    self.set_status(f"Imported {len(urls)} URLs", "ok")
                else:
                    messagebox.showwarning("No URLs", "No valid URLs found in the file!")
                    
            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import URLs: {str(e)}")
                
    def export_history(self):
        """Export download history to file"""
        if not self.download_history:
            messagebox.showinfo("No History", "No download history to export!")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save history",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.download_history, f, indent=2, ensure_ascii=False)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for entry in self.download_history:
                            f.write(f"{entry['timestamp']} - {entry['status']} - {entry['url']}\n")
                            
                self.set_status("History exported successfully!", "ok")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export history: {str(e)}")
                
    def clear_history(self):
        """Clear download history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all download history?"):
            self.download_history.clear()
            self.set_status("History cleared", "ok")
            
    def show_history(self):
        """Show download history in a new window"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Download History")
        history_window.geometry("800x500")
        history_window.transient(self.root)
        
        # Create treeview for history
        columns = ("Time", "Status", "URL")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200 if col != "URL" else 400)
            
        # Populate history
        for entry in reversed(self.download_history[-100:]):  # Show last 100
            status = "✅" if entry['status'] == 'success' else "❌"
            time_str = entry['timestamp'][:19].replace('T', ' ')  # Format timestamp
            tree.insert("", "end", values=(time_str, status, entry['url']))
            
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(history_window, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Close button
        tk.Button(history_window, text="Close", command=history_window.destroy).pack(pady=5)
        
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Theme section
        theme_frame = tk.LabelFrame(settings_window, text="Theme", font=("Arial", 10, "bold"))
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(theme_frame, text="Change Background Color", 
                 command=self.pick_theme_color).pack(pady=5)
        tk.Button(theme_frame, text="Reset to Default Theme", 
                 command=self.reset_theme).pack(pady=5)
                 
        # Advanced options
        advanced_frame = tk.LabelFrame(settings_window, text="Advanced", font=("Arial", 10, "bold"))
        advanced_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_update_var = tk.BooleanVar()
        tk.Checkbutton(advanced_frame, text="Check for updates on startup", 
                      variable=self.auto_update_var).pack(anchor="w", padx=5, pady=2)
        
        self.notification_var = tk.BooleanVar(value=True)
        tk.Checkbutton(advanced_frame, text="Show completion notifications", 
                      variable=self.notification_var).pack(anchor="w", padx=5, pady=2)
        
        # Buttons
        button_frame = tk.Frame(settings_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(button_frame, text="Save", command=lambda: [self.save_settings(), settings_window.destroy()]).pack(side="right", padx=5)
        tk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side="right")
        
    def pick_theme_color(self):
        """Pick theme color"""
        color = colorchooser.askcolor(title="Choose background color", initialcolor=self.THEME["bg"])[1]
        if color:
            self.THEME["bg"] = color
            # Adjust other colors based on brightness
            self.adjust_theme_colors()
            self.apply_theme()
            
    def adjust_theme_colors(self):
        """Adjust theme colors based on background"""
        # This is a simple implementation - you could make it more sophisticated
        bg_color = self.THEME["bg"]
        # Convert hex to RGB to determine if it's light or dark
        bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        brightness = sum(bg_rgb) / 3
        
        if brightness > 128:  # Light background
            self.THEME["text"] = "#000000"
            self.THEME["text2"] = "#333333"
            self.THEME["panel"] = "#f0f0f0"
        else:  # Dark background
            self.THEME["text"] = "#ffffff"
            self.THEME["text2"] = "#cccccc"
            self.THEME["panel"] = "#2C3044"
            
    def reset_theme(self):
        """Reset theme to default"""
        self.THEME = {
            "bg": "#161822",
            "panel": "#2C3044",
            "text": "#fdfdfd",
            "text2": "#b9c0cc",
            "text_selected": "#67d884",
            "muted": "#b0b1b3",
            "button_bg": "#161822",
            "button_fg": "#2b2b2b",
            "accent": "#00FF2A",
            "ok": "#38b000",
            "err": "#e01e37",
            "info": "#5087ff"
        }
        self.apply_theme()
        
    def apply_theme(self):
        """Apply current theme to all widgets"""
        # Root window
        self.root.config(bg=self.THEME["bg"])
        
        # Update ttk styles
        self.style.configure("TProgressbar", 
                           troughcolor=self.THEME["panel"], 
                           background=self.THEME["accent"])
        
        # Update all widgets recursively
        self.update_widget_colors(self.root)
        
    def update_widget_colors(self, widget):
        """Recursively update widget colors"""
        try:
            widget_class = widget.winfo_class()
            
            if widget_class == "Frame":
                widget.config(bg=self.THEME["bg"])
            elif widget_class == "Label":
                if "status" in str(widget).lower():
                    pass  # Don't change status label colors
                else:
                    widget.config(bg=self.THEME["bg"], fg=self.THEME["text"])
            elif widget_class == "LabelFrame":
                widget.config(bg=self.THEME["bg"], fg=self.THEME["text"])
            elif widget_class == "Button":
                widget.config(bg=self.THEME["button_bg"], fg=self.THEME["text"],
                            activebackground=self.THEME["text_selected"], activeforeground=self.THEME["text"])
            elif widget_class == "Checkbutton":
                widget.config(bg=self.THEME["bg"], fg=self.THEME["text"],
                            selectcolor=self.THEME["text2"], activebackground=self.THEME["text_selected"])
                if widget.cget("variable") == False:
                    widget.config(fg=self.THEME["err"], bg=self.THEME["err"], selectcolor=self.THEME["err"])        
                else:
                    widget.config(fg=self.THEME["text"], bg=self.THEME["bg"], selectcolor=self.THEME["ok"])
            elif widget_class == "Radiobutton":
                widget.config(bg=self.THEME["panel"], activebackground=self.THEME["text_selected"])
                # Update radio button colors based on selection
                if hasattr(self, 'quality_var') and widget.cget("value") == self.quality_var.get():
                    widget.config(fg=self.THEME["accent"])
                else:
                    widget.config(fg=self.THEME["muted"])
                    
        except tk.TclError:
            pass  # Some widgets might not support certain options
            
        # Recursively update children
        for child in widget.winfo_children():
            self.update_widget_colors(child)
            
    def run(self):
        """Start the GUI application"""
        # Check if yt-dlp exists
        try:
            subprocess.run([self.yt_dlp, "--version"], capture_output=True, check=True)
            self.connection_label.config(fg=self.THEME["ok"], text="●")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.connection_label.config(fg=self.THEME["err"], text="●")
            messagebox.showwarning("yt-dlp Not Found", 
                                 f"yt-dlp not found at {self.yt_dlp}.\nPlease install yt-dlp or update the path.")
            
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Start main loop
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = YTDLPGui()
        app.run()
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main()