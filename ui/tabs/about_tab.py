"""
About tab - Complete documentation and help
"""

import tkinter as tk
from tkinter import ttk
import webbrowser


class AboutTab:
    """About and Help tab with complete documentation"""

    def __init__(self, parent, shared_vars, logger, app):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Create notebook for sub-tabs
        self.sub_notebook = ttk.Notebook(self.frame)
        self.sub_notebook.pack(fill=tk.BOTH, expand=True)

        # Create sub-tabs
        self._create_overview_tab()
        self._create_getting_started_tab()
        self._create_download_guide_tab()
        self._create_media_types_tab()
        self._create_performance_guide_tab()
        self._create_settings_guide_tab()
        self._create_troubleshooting_tab()
        self._create_about_app_tab()

    def _create_scrollable_frame(self, parent) -> tuple:
        """Create a scrollable frame with proper mouse/touchpad support"""
        # Create container frame
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure scroll region when frame size changes
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Make the scrollable frame expand to canvas width
        def configure_scroll_region(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_scroll_region)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll function that works with both mouse wheel and touchpad
        def _on_scroll(event):
            # Check if scrolling is possible
            if canvas.yview() == (0.0, 1.0):
                return  # No scrolling needed, content fits

            # Handle different platforms and input devices
            if event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(1, "units")
            else:
                # Windows and MacOS
                # event.delta: positive = scroll up, negative = scroll down
                # Touchpad usually sends smaller delta values
                if event.delta != 0:
                    # Normalize delta for different platforms
                    if abs(event.delta) >= 120:
                        # Mouse wheel (Windows sends 120 per notch)
                        scroll_units = int(-1 * (event.delta / 120))
                    else:
                        # Touchpad (smaller increments)
                        scroll_units = int(-1 * (event.delta / 40))
                        if scroll_units == 0:
                            scroll_units = -1 if event.delta > 0 else 1

                    canvas.yview_scroll(scroll_units, "units")

        # Bind scroll events to canvas
        def _bind_scroll(widget):
            """Recursively bind scroll events to widget and all children"""
            # Windows and MacOS
            widget.bind("<MouseWheel>", _on_scroll, add="+")
            # MacOS touchpad
            widget.bind("<Button-4>", _on_scroll, add="+")
            widget.bind("<Button-5>", _on_scroll, add="+")
            # Two-finger scroll on touchpad (MacOS)
            widget.bind("<Shift-MouseWheel>", _on_scroll, add="+")

            # Bind to all children
            for child in widget.winfo_children():
                _bind_scroll(child)

        # Initial binding
        _bind_scroll(canvas)
        _bind_scroll(scrollable_frame)

        # Bind when entering the canvas area
        def _on_enter(event):
            _bind_scroll(canvas)
            _bind_scroll(scrollable_frame)

        canvas.bind("<Enter>", _on_enter)
        scrollable_frame.bind("<Enter>", _on_enter)

        # Store reference for later binding of new widgets
        scrollable_frame._bind_scroll = _bind_scroll
        scrollable_frame._canvas = canvas

        return scrollable_frame, canvas

    def _create_section(self, parent, title: str, content: str, icon: str = "📌") -> ttk.LabelFrame:
        """Create a documentation section"""
        frame = ttk.LabelFrame(parent, text=f"{icon} {title}", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        label = ttk.Label(
            frame,
            text=content,
            justify=tk.LEFT,
            wraplength=650
        )
        label.pack(anchor=tk.W)

        # Bind scroll events to new widgets
        if hasattr(parent, '_bind_scroll'):
            parent._bind_scroll(frame)
            parent._bind_scroll(label)

        return frame

        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return scrollable_frame, canvas

    def _create_section(self, parent, title: str, content: str, icon: str = "📌") -> ttk.LabelFrame:
        """Create a documentation section"""
        frame = ttk.LabelFrame(parent, text=f"{icon} {title}", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        label = ttk.Label(
            frame,
            text=content,
            justify=tk.LEFT,
            wraplength=650
        )
        label.pack(anchor=tk.W)

        return frame

    def _create_overview_tab(self) -> None:
        """Create Overview sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="📋 Overview")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # Title
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20), padx=5)

        ttk.Label(
            title_frame,
            text="📥 Telegram Media Downloader",
            font=('Arial', 18, 'bold')
        ).pack()

        ttk.Label(
            title_frame,
            text="A powerful tool for downloading media from Telegram channels",
            font=('Arial', 11)
        ).pack(pady=(5, 0))

        # What is this app
        self._create_section(
            scrollable_frame,
            "What is this application?",
            """This application allows you to download media files (audio, video, photos, 
documents, etc.) from Telegram channels that you are a member of.

It uses the Telegram API through the Telethon library to access and download 
content directly from Telegram's servers.

Key capabilities:
• Download single posts or batch download multiple posts
• Support for all media types (audio, video, photos, documents, etc.)
• Parallel downloads for faster batch processing
• Resume capability with skip existing files
• Performance optimization settings
• Multiple session support for different accounts""",
            "ℹ️"
        )

        # How it works
        self._create_section(
            scrollable_frame,
            "How does it work?",
            """The download process works in the following steps:

1️⃣ AUTHENTICATION
   • You provide your Telegram API credentials (API ID & Hash)
   • You login with your phone number and verification code
   • A session file is created to remember your login

2️⃣ CHANNEL ACCESS
   • You specify the channel ID from the Telegram URL
   • The app connects to Telegram and accesses the channel
   • You must be a member of the channel to download

3️⃣ CONTENT DISCOVERY
   • The app scans the channel for posts
   • You can specify post numbers or ranges
   • Media type filters determine what to download

4️⃣ DOWNLOAD EXECUTION
   • Files are downloaded based on your settings
   • Parallel downloads (if enabled) speed up the process
   • Progress is tracked and displayed

5️⃣ FILE SAVING
   • Files are saved to your specified output directory
   • Original filenames are preserved when available
   • Automatic file naming for unnamed content""",
            "⚙️"
        )

        # Quick start
        self._create_section(
            scrollable_frame,
            "Quick Start Guide",
            """Get started in 5 simple steps:

Step 1: Get API Credentials
   → Go to https://my.telegram.org/apps
   → Login and create an application
   → Note your API ID and API Hash

Step 2: Configure the App
   → Go to Settings tab
   → Enter your API ID and API Hash
   → Click "Save Settings"

Step 3: Login to Telegram
   → Enter a session name (e.g., "my_account")
   → Click "Login to Telegram"
   → Enter your phone number and verification code

Step 4: Set Channel & Output
   → Enter the Channel ID from the Telegram URL
   → Choose your output/download directory

Step 5: Start Downloading!
   → Go to Download tab for single posts
   → Go to Batch Download tab for multiple posts
   → Select media types and click download""",
            "🚀"
        )

    def _create_getting_started_tab(self) -> None:
        """Create Getting Started sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="🚀 Getting Started")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # API Credentials
        self._create_section(
            scrollable_frame,
            "Step 1: Getting Telegram API Credentials",
            """You need API credentials to use this application. Here's how to get them:

1. Open your web browser and go to:
   https://my.telegram.org/apps

2. Login with your phone number (same as your Telegram account)

3. You'll receive a verification code in your Telegram app

4. After logging in, you'll see "API Development Tools"

5. If you don't have an app, click "Create new application"

6. Fill in the form:
   • App title: Any name (e.g., "My Downloader")
   • Short name: Any short name
   • Platform: Desktop
   • Description: Optional

7. After creating, you'll see:
   • API ID: A number (e.g., 12345678)
   • API Hash: A string (e.g., "abc123def456...")

8. Copy these credentials - you'll need them in the app

⚠️ IMPORTANT: Keep your API credentials private!
   Never share them with anyone.""",
            "🔑"
        )

        # Understanding URLs
        self._create_section(
            scrollable_frame,
            "Step 2: Understanding Telegram URLs",
            """Telegram channel URLs contain important information:

📍 Private Channel URL Format:
   https://t.me/c/2299347106/2436
                  ↑          ↑
                  │          └── Post Number (2436)
                  └── Channel ID (2299347106)

📍 Public Channel URL Format:
   https://t.me/channel_username/1234
                ↑                 ↑
                │                 └── Post Number
                └── Channel Username

For this app, you need:
   • Channel ID: The number after /c/ (for private channels)
   • Post Number: The last number in the URL

How to get a post URL:
   1. Open the Telegram channel
   2. Right-click on any message
   3. Select "Copy Message Link"
   4. Paste and extract the numbers

Example:
   URL: https://t.me/c/2299347106/2436
   Channel ID: 2299347106
   Post Number: 2436""",
            "🔗"
        )

        # Session setup
        self._create_section(
            scrollable_frame,
            "Step 3: Setting Up Your Session",
            """A session stores your Telegram login state:

What is a Session?
   • A session file (e.g., "my_account.session") stores your authentication
   • You don't need to login again once a session is created
   • Each session represents one Telegram account

Creating a New Session:
   1. Go to Settings tab
   2. In "Session Switcher", type a name (e.g., "personal")
   3. Click "Create & Login"
   4. Enter your phone number (with country code, e.g., +1234567890)
   5. Enter the verification code from Telegram
   6. If you have 2FA, enter your password

Managing Multiple Sessions:
   • You can have multiple sessions for different accounts
   • Use the dropdown to switch between sessions
   • Each session has its own login state

⚠️ Session Security:
   • Session files contain your authentication
   • Keep them private and don't share
   • Delete sessions you no longer need""",
            "👤"
        )

        # First download
        self._create_section(
            scrollable_frame,
            "Step 4: Your First Download",
            """Let's download your first file:

Single Post Download:
   1. Go to the "Download" tab
   2. Enter the post number (e.g., 2436)
   3. Or paste the full URL and click "Parse & Download"
   4. Click "Download Post"
   5. Check the log for progress

Batch Download:
   1. Go to the "Batch Download" tab
   2. Choose a download method:
      • Range: Enter "From" and "To" post numbers
      • Multiple: Enter comma-separated numbers
      • Sequential: Scan channel with skip option
   3. Select media types to download
   4. Click the download button

Tips for First Download:
   ✓ Start with a single post to test
   ✓ Check that your Channel ID is correct
   ✓ Make sure you're a member of the channel
   ✓ Use "Balanced" performance preset initially""",
            "📥"
        )

    def _create_download_guide_tab(self) -> None:
        """Create Download Guide sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="📥 Download Guide")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # Single vs Batch
        self._create_section(
            scrollable_frame,
            "Single Post vs Batch Download",
            """Choose the right method for your needs:

📥 SINGLE POST DOWNLOAD
   Best for: Downloading specific individual posts

   How to use:
   • Enter the post number directly, OR
   • Paste the full URL and click "Parse & Download"

   When to use:
   • You know exactly which post you want
   • Testing if your setup works
   • Downloading a specific file

📦 BATCH DOWNLOAD
   Best for: Downloading multiple files at once

   Three methods available:

   1. Range Download
      • Enter start and end post numbers
      • Downloads all posts in that range
      • Example: 100 to 200 = downloads posts 100-200

   2. Multiple Posts
      • Enter comma-separated post numbers
      • Downloads specific posts you choose
      • Example: 100, 150, 200, 275

   3. Sequential Download
      • Scans the entire channel
      • Skip first N files
      • Download up to max N files
      • Good for resuming interrupted downloads""",
            "🔄"
        )

        # Download options explained
        self._create_section(
            scrollable_frame,
            "Download Options Explained",
            """Understanding the batch download options:

☑️ SKIP EXISTING FILES
   • If enabled: Files already in output folder are skipped
   • If disabled: Files are re-downloaded (may overwrite)
   • Recommended: Keep enabled to avoid re-downloading

☑️ DOWNLOAD OLDEST FIRST
   • If enabled: Starts from oldest messages
   • If disabled: Starts from newest messages
   • Use case: Enable for chronological downloads

📋 MEDIA TYPE SELECTION
   • Choose which types of media to download
   • Multiple types can be selected
   • Unselected types are skipped

   Quick Select buttons:
   • All: Select all media types
   • None: Deselect all
   • Media Only: Just audio, video, and photos

⚠️ TEXT MESSAGES
   • Text-only messages are never downloaded
   • Only messages with media attachments are processed""",
            "⚙️"
        )

        # Recommended approaches
        self._create_section(
            scrollable_frame,
            "Recommended Download Approaches",
            """Best practices for different scenarios:

🎵 DOWNLOADING MUSIC/AUDIO COLLECTION
   Recommended settings:
   • Media type: Audio only
   • Method: Sequential download
   • Skip existing: Enabled
   • Performance: Balanced or Aggressive

   Why: Audio files are usually small, can use faster settings

🎬 DOWNLOADING VIDEOS
   Recommended settings:
   • Media type: Video only
   • Method: Range or Multiple posts
   • Skip existing: Enabled
   • Performance: Balanced
   • Chunk size: 1024 KB or higher

   Why: Large files need bigger chunks, avoid aggressive to prevent timeouts

🖼️ DOWNLOADING PHOTOS
   Recommended settings:
   • Media type: Photo only
   • Method: Sequential or Range
   • Performance: Aggressive

   Why: Photos are small, fast downloads possible

📁 DOWNLOADING EVERYTHING
   Recommended settings:
   • Media type: All
   • Method: Sequential download
   • Skip existing: Enabled
   • Performance: Balanced

   Why: Mixed content sizes, balanced approach is safest

🔄 RESUMING INTERRUPTED DOWNLOAD
   Steps:
   1. Use Sequential download
   2. Set "Skip first N" to number already downloaded
   3. Enable "Skip existing files"
   4. Start download - it will continue from where you left off""",
            "💡"
        )

        # Output and file naming
        self._create_section(
            scrollable_frame,
            "Output Directory & File Naming",
            """How files are saved:

📂 OUTPUT DIRECTORY
   • Set in the Download tab
   • All files are saved here
   • Subfolders are NOT created automatically
   • Make sure you have write permissions

📝 FILE NAMING
   Files are named in this priority:

   1. Original filename (if available)
      Example: "song.mp3", "document.pdf"

   2. Auto-generated name (if no original name)
      Format: {type}_{post_id}.{extension}
      Examples:
      • audio_2436.mp3
      • video_2437.mp4
      • photo_2438.jpg
      • document_2439.pdf

📋 FILE EXTENSIONS
   Extensions are determined by:
   1. Original filename extension
   2. MIME type from Telegram
   3. Default based on media type

⚠️ DUPLICATE NAMES
   • If "Skip existing" is on: File is skipped
   • If "Skip existing" is off: File may be overwritten
   • Consider organizing by folders manually""",
            "📂"
        )

    def _create_media_types_tab(self) -> None:
        """Create Media Types Guide sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="📁 Media Types")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # Audio
        self._create_section(
            scrollable_frame,
            "Audio Files",
            """🎵 AUDIO

   Supported extensions:
   .mp3, .m4a, .wav, .ogg, .flac, .aac, .wma, .opus, .aiff

   What's included:
   • Music files
   • Podcasts
   • Audio recordings
   • Sound effects

   Typical file sizes: 2-15 MB per file

   Recommended performance settings:
   • Parallel downloads: 3-5
   • Chunk size: 512 KB
   • Delay between files: 0.2-0.5s

   Best download method:
   • Sequential for full channel archives
   • Batch for specific albums/collections""",
            "🎵"
        )

        # Video
        self._create_section(
            scrollable_frame,
            "Video Files",
            """🎬 VIDEO

   Supported extensions:
   .mp4, .mkv, .avi, .mov, .webm, .flv, .wmv, .m4v, .3gp

   What's included:
   • Video files
   • Movie clips
   • Recorded videos

   NOT included:
   • Video notes (circular videos) - separate category
   • Animations/GIFs - separate category

   Typical file sizes: 50 MB - 2 GB per file

   Recommended performance settings:
   • Parallel downloads: 2-3 (fewer for large files)
   • Chunk size: 1024-2048 KB
   • Delay between files: 0.5-1.0s
   • Request timeout: 120-300s

   Best download method:
   • Multiple posts for specific videos
   • Range for series/collections

   ⚠️ Tips:
   • Large videos may timeout - increase timeout setting
   • Use Conservative preset for very large files
   • Enable "Keep connection alive" """,
            "🎬"
        )

        # Photo
        self._create_section(
            scrollable_frame,
            "Photos & Images",
            """🖼️ PHOTO

   Supported extensions:
   .jpg, .jpeg, .png, .webp, .gif, .bmp, .tiff, .heic

   What's included:
   • Photos
   • Images
   • Screenshots
   • Static pictures

   NOT included:
   • Animated GIFs (saved as animations)
   • Stickers - separate category

   Typical file sizes: 100 KB - 5 MB per file

   Recommended performance settings:
   • Parallel downloads: 5-8
   • Chunk size: 256-512 KB
   • Delay between files: 0.1-0.3s

   Best download method:
   • Sequential for photo albums
   • Aggressive preset works well

   💡 Note: Telegram compresses photos by default.
   Original quality may not be preserved.""",
            "🖼️"
        )

        # Documents
        self._create_section(
            scrollable_frame,
            "Documents & Files",
            """📄 DOCUMENT

   Supported extensions:
   .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt,
   .zip, .rar, .7z, .tar, .gz, .epub, .mobi, and more

   What's included:
   • PDF documents
   • Office files (Word, Excel, PowerPoint)
   • Archives (ZIP, RAR)
   • E-books
   • Any other file type not categorized elsewhere

   Typical file sizes: Varies widely (1 KB - 2 GB)

   Recommended performance settings:
   • Parallel downloads: 2-3
   • Chunk size: 512-1024 KB
   • Use Balanced preset

   Best download method:
   • Depends on content
   • Use Multiple posts for specific documents

   💡 Note: Documents retain original filenames,
   making organization easier.""",
            "📄"
        )

        # Voice
        self._create_section(
            scrollable_frame,
            "Voice Messages",
            """🎤 VOICE MESSAGE

   Supported extensions:
   .ogg, .opus, .oga

   What's included:
   • Voice recordings
   • Voice notes
   • Audio messages

   Typical file sizes: 50 KB - 2 MB per file

   Recommended performance settings:
   • Parallel downloads: 5-8
   • Chunk size: 256 KB
   • Aggressive preset works well

   Best download method:
   • Sequential for all voice messages
   • Very fast to download due to small size

   💡 Note: Voice messages are usually
   in OGG Opus format.""",
            "🎤"
        )

        # Video Notes
        self._create_section(
            scrollable_frame,
            "Video Notes (Round Videos)",
            """⭕ VIDEO NOTE

   Supported extensions:
   .mp4 (circular video format)

   What's included:
   • Round/circular video messages
   • Video notes (the circular videos in chats)

   NOT included:
   • Regular videos - separate category

   Typical file sizes: 1-10 MB per file

   Recommended performance settings:
   • Parallel downloads: 3-5
   • Chunk size: 512 KB
   • Balanced preset

   💡 Note: These are the circular video messages
   that play inline in Telegram chats.""",
            "⭕"
        )

        # Animations
        self._create_section(
            scrollable_frame,
            "Animations & GIFs",
            """🎞️ ANIMATION / GIF

   Supported extensions:
   .gif, .mp4 (for animated content)

   What's included:
   • Animated GIFs
   • MP4 animations
   • Short looping videos

   Typical file sizes: 500 KB - 10 MB per file

   Recommended performance settings:
   • Parallel downloads: 4-6
   • Chunk size: 512 KB
   • Balanced or Aggressive preset

   💡 Note: Telegram often converts GIFs to MP4
   for better compression. The downloaded file
   may be MP4 even if it was a GIF.""",
            "🎞️"
        )

        # Stickers
        self._create_section(
            scrollable_frame,
            "Stickers",
            """😀 STICKER

   Supported extensions:
   .webp (static stickers)
   .tgs (animated stickers - Lottie format)
   .webm (video stickers)

   What's included:
   • Static stickers
   • Animated stickers
   • Video stickers

   Typical file sizes: 10 KB - 500 KB per file

   Recommended performance settings:
   • Parallel downloads: 8-10
   • Chunk size: 128-256 KB
   • Maximum preset works well

   💡 Note: .tgs files are Lottie animations
   and require special software to view/edit.""",
            "😀"
        )

    def _create_performance_guide_tab(self) -> None:
        """Create Performance Guide sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="⚡ Performance Guide")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # Presets explained
        self._create_section(
            scrollable_frame,
            "Performance Presets Explained",
            """Choose the right preset for your situation:

🐢 CONSERVATIVE
   Settings: 1 download, 256KB chunks, 1.0s delay

   Best for:
   • First-time users
   • Avoiding rate limits
   • Unreliable internet connections
   • Very large files (1GB+)

   Pros: Very safe, rarely triggers limits
   Cons: Slowest download speed

⚖️ BALANCED (Recommended)
   Settings: 3 downloads, 512KB chunks, 0.5s delay

   Best for:
   • Most users
   • Mixed content (audio, video, photos)
   • Regular downloading

   Pros: Good speed with low risk
   Cons: May occasionally hit rate limits

🚀 AGGRESSIVE
   Settings: 5 downloads, 1024KB chunks, 0.2s delay

   Best for:
   • Fast internet connections
   • Small files (audio, photos)
   • When you need speed

   Pros: Much faster downloads
   Cons: Higher chance of rate limits

⚡ MAXIMUM
   Settings: 8 downloads, 2048KB chunks, 0.1s delay

   Best for:
   • Very fast internet
   • Small files only
   • Experienced users

   Pros: Fastest possible
   Cons: High risk of FloodWait errors

   ⚠️ Warning: Use with caution!""",
            "🎚️"
        )

        # Parallel downloads
        self._create_section(
            scrollable_frame,
            "Parallel Downloads",
            """Understanding concurrent downloads:

WHAT IS PARALLEL DOWNLOADING?
   Instead of downloading one file at a time,
   multiple files are downloaded simultaneously.

   Example:
   • Sequential: File1 → File2 → File3 (slow)
   • Parallel (3): File1, File2, File3 together (fast)

MAX CONCURRENT DOWNLOADS
   This controls how many files download at once.

   Recommended values:
   • 1-2: Large files (videos 500MB+)
   • 3-4: Medium files (videos, documents)
   • 5-6: Small files (audio, photos)
   • 7-10: Very small files (stickers, voice)

   ⚠️ Higher is NOT always better!
   • More connections = more rate limit risk
   • Large files may timeout with many parallels
   • Your internet bandwidth is shared

WHEN TO DISABLE PARALLEL DOWNLOADS
   Set to 1 (or disable) when:
   • Downloading very large files
   • Getting frequent timeouts
   • Getting FloodWait errors
   • Internet is slow/unstable""",
            "🔀"
        )

        # Chunk and buffer
        self._create_section(
            scrollable_frame,
            "Chunk Size & Buffer",
            """How data is downloaded in pieces:

DOWNLOAD CHUNK SIZE
   Files are downloaded in chunks (pieces).
   Larger chunks = fewer requests = faster (usually)

   Size recommendations:
   • 128-256 KB: Small files, slow internet
   • 512 KB: Balanced (default)
   • 1024 KB: Large files, fast internet
   • 2048-4096 KB: Very large files, very fast internet

   Choosing the right size:

   Small chunks (128-256 KB):
   ✓ More responsive progress updates
   ✓ Better for unstable connections
   ✗ More overhead (slower overall)

   Large chunks (1024-4096 KB):
   ✓ Faster for big files
   ✓ Less overhead
   ✗ Less responsive updates
   ✗ May timeout on slow connections

BUFFER SIZE
   Memory buffer for writing files.

   Recommendations:
   • 512 KB - 1 MB: Normal use
   • 2-4 MB: Many parallel downloads
   • 4-8 MB: Very large files

   💡 Larger buffer = more RAM usage
   Most users can leave at default (1024 KB)""",
            "📦"
        )

        # Rate limiting
        self._create_section(
            scrollable_frame,
            "Rate Limiting & Delays",
            """Avoiding Telegram's download limits:

WHAT IS RATE LIMITING?
   Telegram limits how fast you can download.
   If you exceed limits, you get "FloodWait" errors.
   FloodWait forces you to wait (sometimes minutes).

DELAY BETWEEN FILES
   Pause between finishing one file and starting next.

   Recommendations:
   • 0.1-0.2s: Fast (risky)
   • 0.5s: Balanced (recommended)
   • 1.0s+: Safe (slow)

DELAY BETWEEN BATCHES
   Pause after downloading a batch of files.
   Gives Telegram's servers a break.

   Recommendations:
   • 0.5-1.0s: Aggressive
   • 2.0s: Balanced (default)
   • 5.0s+: Very safe

BATCH SIZE
   How many files before taking a batch break.

   Recommendations:
   • 5-10: Safe
   • 10-20: Normal
   • 20-50: Aggressive

AUTO-HANDLE FLOODWAIT
   If enabled, the app automatically waits when
   rate limited, then continues.

   ✓ Recommended: Keep enabled
   The app will pause and resume automatically.

💡 TIPS TO AVOID RATE LIMITS:
   • Start with Balanced preset
   • Increase delays if you get FloodWait
   • Download during off-peak hours
   • Use Conservative for large downloads""",
            "⏱️"
        )

        # Connection settings
        self._create_section(
            scrollable_frame,
            "Connection Settings",
            """Network and connection configuration:

CONNECTION RETRIES
   How many times to retry if connection fails.

   Default: 5
   Increase if you have unstable internet.

RETRY DELAY
   Seconds to wait before retrying.

   Default: 1.0 second
   Increase for persistent connection issues.

REQUEST TIMEOUT
   Maximum seconds to wait for a response.

   Default: 60 seconds

   Increase for:
   • Very large files
   • Slow internet
   • High server load

   Recommended:
   • 60s: Normal files
   • 120s: Large videos
   • 300s: Very large files (1GB+)

USE IPV6
   Enable if your network supports IPv6.
   May improve speeds in some regions.

   Default: Disabled
   Try enabling if you have slow speeds.

KEEP CONNECTION ALIVE
   Maintains the connection between downloads.

   ✓ Recommended: Keep enabled
   • Faster batch downloads
   • No reconnection overhead
   • Uses slightly more resources""",
            "🔌"
        )

        # Optimization tips
        self._create_section(
            scrollable_frame,
            "Speed Optimization Tips",
            """Maximize your download speed:

📈 FOR FASTER DOWNLOADS:
   1. Use parallel downloads (3-5 concurrent)
   2. Increase chunk size (1024KB+)
   3. Reduce delays (0.2s between files)
   4. Enable "Keep connection alive"
   5. Use wired internet if possible

🛡️ FOR STABLE DOWNLOADS:
   1. Use fewer parallel downloads (1-2)
   2. Keep chunk size moderate (512KB)
   3. Increase delays (0.5-1.0s)
   4. Increase timeout for large files
   5. Enable auto FloodWait handling

🔧 FOR LARGE FILES (Videos 500MB+):
   1. Use Conservative preset
   2. Set parallel downloads to 1-2
   3. Increase chunk size to 2048KB
   4. Set timeout to 180-300 seconds
   5. Increase retry count to 5-10

📱 FOR SLOW/UNSTABLE INTERNET:
   1. Use Conservative preset
   2. Reduce parallel downloads to 1
   3. Use smaller chunks (256KB)
   4. Increase all delays
   5. Increase retry count and delay

⚡ FOR SMALL FILES (Audio, Photos):
   1. Use Aggressive or Maximum preset
   2. Increase parallel downloads (5-8)
   3. Reduce delays (0.1-0.2s)
   4. Smaller chunks are fine (256-512KB)

🌙 BEST TIME TO DOWNLOAD:
   • Off-peak hours (late night/early morning)
   • Weekdays vs weekends
   • When your internet is least busy""",
            "💡"
        )

    def _create_settings_guide_tab(self) -> None:
        """Create Settings Guide sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="⚙️ Settings Guide")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # API Credentials
        self._create_section(
            scrollable_frame,
            "API Credentials Settings",
            """Your Telegram API authentication:

API ID
   • A numeric identifier for your app
   • Obtained from my.telegram.org
   • Example: 12345678

   ⚠️ Never share your API ID publicly

API HASH
   • A secret string for authentication
   • Obtained from my.telegram.org
   • Example: "abc123def456ghi789..."

   ⚠️ Keep this secret! Never share it.

SHOW/HIDE API HASH
   • Toggle to view or hide the API Hash
   • Hidden by default for security

💡 These credentials are saved locally
   in the config file for convenience.""",
            "🔑"
        )

        # Session management
        self._create_section(
            scrollable_frame,
            "Session Management",
            """Managing your Telegram sessions:

SESSION SWITCHER
   • Dropdown shows all available sessions
   • Displays account name for each session
   • Click to switch between sessions

CREATE NEW SESSION
   • Enter a name for the new session
   • Click "Create & Login"
   • Follow the login prompts

   Naming tips:
   • Use descriptive names: "personal", "work"
   • No spaces or special characters
   • Keep it short and memorable

LOGIN PROCESS
   1. Click "Login" or "Create & Login"
   2. Enter phone number (with country code)
   3. Enter verification code from Telegram
   4. Enter 2FA password if enabled

LOGOUT
   • Removes the session file
   • You'll need to login again
   • Use for security or switching accounts

DELETE SESSION
   • Permanently removes session file
   • Cannot be undone
   • Use when no longer needed

💡 TIPS:
   • Create separate sessions for different accounts
   • Logout from unused sessions for security
   • Session files are stored in the app directory""",
            "👤"
        )

        # Channel configuration
        self._create_section(
            scrollable_frame,
            "Channel Configuration",
            """Setting up your target channel:

CHANNEL ID
   • The numeric ID of the Telegram channel
   • Found in channel URLs after /c/

   Example URL: https://t.me/c/2299347106/100
   Channel ID: 2299347106

HOW TO FIND CHANNEL ID:
   1. Open the channel in Telegram
   2. Right-click any message
   3. Copy the message link
   4. Extract the number after /c/

PUBLIC VS PRIVATE CHANNELS:

   Private channels:
   • URL format: t.me/c/NUMBERS/post
   • Use the number as Channel ID

   Public channels:
   • URL format: t.me/username/post
   • You may need the numeric ID
   • Try the username first

⚠️ REQUIREMENTS:
   • You must be a member of the channel
   • You need permission to view content
   • Some channels may restrict downloads""",
            "📢"
        )

        # Output settings
        self._create_section(
            scrollable_frame,
            "Output Directory Settings",
            """Where your downloads are saved:

OUTPUT DIRECTORY
   • The folder where files are saved
   • Default: "downloads" in app folder
   • Can be changed to any location

CHOOSING A DIRECTORY:
   • Click "Browse..." to select
   • Or type the path directly
   • Use full paths for clarity

   Examples:
   • Windows: C:\\Users\\Name\\Downloads\\Telegram
   • Mac: /Users/Name/Downloads/Telegram
   • Linux: /home/name/Downloads/Telegram

PERMISSIONS:
   • Make sure you have write access
   • The folder will be created if needed
   • Check available disk space

OPEN DOWNLOADS FOLDER:
   • Quick button to open the folder
   • Useful to check downloaded files

💡 ORGANIZATION TIPS:
   • Create separate folders for different channels
   • Use date-based subfolders for large downloads
   • Regularly clean up completed downloads""",
            "📂"
        )

        # Connection test
        self._create_section(
            scrollable_frame,
            "Connection & Testing",
            """Verifying your setup:

TEST CONNECTION
   • Checks if you can connect to Telegram
   • Verifies your session is valid
   • Shows your account name if successful

POSSIBLE RESULTS:

   ✅ "Connected as [Name]"
   • Everything is working
   • You're ready to download

   ⚠️ "Not logged in"
   • Session exists but not authenticated
   • Click "Login" to authenticate

   ❌ "Error: ..."
   • Connection failed
   • Check your internet
   • Verify API credentials

REFRESH SESSIONS
   • Rescans for session files
   • Updates the session dropdown
   • Shows account info for each

💡 TROUBLESHOOTING:
   • If test fails, check internet connection
   • Verify API ID and Hash are correct
   • Try creating a new session
   • Check if Telegram is accessible in your region""",
            "🔌"
        )

    def _create_troubleshooting_tab(self) -> None:
        """Create Troubleshooting sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="🔧 Troubleshooting")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # Common errors
        self._create_section(
            scrollable_frame,
            "Common Errors & Solutions",
            """Fixing the most common issues:

❌ "Failed to get channel"
   Causes:
   • Wrong Channel ID
   • Not a member of the channel
   • Channel is private/restricted

   Solutions:
   • Double-check the Channel ID
   • Make sure you've joined the channel
   • Try accessing the channel in Telegram app first

❌ "FloodWaitError: X seconds"
   Causes:
   • Too many requests too fast
   • Aggressive download settings

   Solutions:
   • Wait for the specified time
   • Enable "Auto-handle FloodWait"
   • Use Conservative preset
   • Increase delays between files

❌ "Not logged in" / "Not authorized"
   Causes:
   • Session expired
   • Session file corrupted
   • First time use

   Solutions:
   • Click "Login to Telegram"
   • Delete session and create new one
   • Check API credentials

❌ "Connection error" / "Timeout"
   Causes:
   • Internet connection issues
   • Telegram servers unreachable
   • Firewall blocking

   Solutions:
   • Check internet connection
   • Try again later
   • Increase timeout setting
   • Check if VPN is needed

❌ "File not found" / "Message not found"
   Causes:
   • Post was deleted
   • Wrong post number
   • No access to the post

   Solutions:
   • Verify post exists in Telegram
   • Check the post number
   • Ensure you have access""",
            "❌"
        )

        # Speed issues
        self._create_section(
            scrollable_frame,
            "Slow Download Speed",
            """Diagnosing and fixing slow downloads:

🐌 SYMPTOMS:
   • Downloads taking too long
   • Progress bar moves slowly
   • Low MB/s speed shown

📋 CHECKLIST:

1. Check your internet speed
   • Run a speed test (speedtest.net)
   • Compare with download speeds
   • Telegram may be slower than direct downloads

2. Check performance settings
   • Are parallel downloads enabled?
   • Is chunk size too small?
   • Are delays too high?

3. Try different presets
   • Start with Balanced
   • If stable, try Aggressive
   • If issues, use Conservative

4. Check for rate limiting
   • Look for FloodWait in logs
   • If rate limited, slow down
   • Try off-peak hours

5. Large file considerations
   • Big files take longer
   • Check file sizes in logs
   • Increase timeout for large files

💡 OPTIMIZATION STEPS:
   1. Use wired connection if possible
   2. Close other bandwidth-heavy apps
   3. Increase parallel downloads (if not rate limited)
   4. Increase chunk size (512KB → 1024KB)
   5. Reduce delays (if not rate limited)
   6. Try downloading at different times""",
            "🐌"
        )

        # Download failures
        self._create_section(
            scrollable_frame,
            "Downloads Failing or Stopping",
            """When downloads fail or stop unexpectedly:

🔴 INDIVIDUAL FILES FAILING:

   Possible causes:
   • File was deleted
   • Temporary server error
   • Timeout (file too large)

   Solutions:
   • Enable "Skip failed files"
   • Increase retry count (3 → 5)
   • Increase timeout for large files
   • Try downloading the file individually

🔴 ALL DOWNLOADS FAILING:

   Possible causes:
   • Lost internet connection
   • Session expired
   • API credentials invalid
   • Banned/restricted by Telegram

   Solutions:
   • Check internet connection
   • Test connection in Settings
   • Re-login to Telegram
   • Wait and try later (if banned)

🔴 DOWNLOADS STOPPING MIDWAY:

   Possible causes:
   • Rate limiting (FloodWait)
   • Connection dropped
   • App crashed

   Solutions:
   • Enable "Auto-handle FloodWait"
   • Use "Skip existing files" to resume
   • Use Sequential download with skip
   • Check logs for specific errors

🔴 INCOMPLETE/CORRUPTED FILES:

   Possible causes:
   • Download interrupted
   • Disk full
   • Write permission issues

   Solutions:
   • Delete incomplete files
   • Check disk space
   • Check folder permissions
   • Re-download the files""",
            "🔴"
        )

        # Session issues
        self._create_section(
            scrollable_frame,
            "Session & Login Issues",
            """Fixing authentication problems:

❌ CAN'T RECEIVE VERIFICATION CODE:
   • Check your Telegram app
   • Code might be in "Saved Messages"
   • Wait a minute and request again
   • Check SMS if Telegram is new

❌ CODE IS INVALID:
   • Codes expire after a few minutes
   • Request a new code
   • Type carefully (no spaces)

❌ 2FA PASSWORD NOT WORKING:
   • Make sure it's the 2FA password, not account password
   • Password is case-sensitive
   • Try resetting 2FA in Telegram if forgotten

❌ SESSION FILE CORRUPTED:
   • Delete the .session file
   • Create a new session
   • Login again

❌ "TOO MANY ATTEMPTS":
   • Wait before trying again (may be hours)
   • Don't repeatedly enter wrong codes
   • Try from a different network

💡 TIPS:
   • Keep session files backed up
   • Don't share session files
   • Logout from unused sessions
   • Use strong 2FA passwords""",
            "👤"
        )

        # Getting help
        self._create_section(
            scrollable_frame,
            "Getting More Help",
            """Where to find additional help:

📚 DOCUMENTATION:
   • Read through all tabs in this About section
   • Check the Performance Guide for speed issues
   • Review Settings Guide for configuration

🔍 LOGS:
   • Check the log output in Download tab
   • Error messages often explain the problem
   • Note any error codes or messages

🌐 ONLINE RESOURCES:
   • Telegram API documentation
   • Telethon library documentation
   • Python asyncio guides

💡 SELF-HELP STEPS:
   1. Read the error message carefully
   2. Search for the error in this guide
   3. Try the suggested solutions
   4. Check your settings and credentials
   5. Try with default/balanced settings
   6. Restart the application
   7. Create a fresh session

🔄 RESET OPTIONS:
   • Reset performance settings to defaults
   • Reset all settings
   • Delete and recreate sessions
   • Reinstall the application (keep config files)""",
            "❓"
        )

    def _create_about_app_tab(self) -> None:
        """Create About App sub-tab"""
        tab = ttk.Frame(self.sub_notebook, padding="10")
        self.sub_notebook.add(tab, text="ℹ️ About App")

        scrollable_frame, canvas = self._create_scrollable_frame(tab)

        # App info
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill=tk.X, pady=20, padx=5)

        ttk.Label(
            title_frame,
            text="📥 Telegram Audio Downloader",
            font=('Arial', 20, 'bold')
        ).pack()

        ttk.Label(
            title_frame,
            text="Version 2.0.0",
            font=('Arial', 12)
        ).pack(pady=(5, 0))

        ttk.Label(
            title_frame,
            text="A powerful media downloader for Telegram channels",
            font=('Arial', 11)
        ).pack(pady=(10, 0))

        # Features
        self._create_section(
            scrollable_frame,
            "Features",
            """• Download any media type from Telegram channels
• Single post and batch download modes
• Parallel downloads for faster processing
• Multiple session support
• Customizable performance settings
• Progress tracking with speed display
• Auto-retry and error handling
• Skip existing files for resume capability
• Cross-platform support (Windows, Mac, Linux)""",
            "✨"
        )

        # Tech stack
        self._create_section(
            scrollable_frame,
            "Technology",
            """Built with:
• Python 3.9+
• Tkinter (GUI framework)
• Telethon (Telegram API library)
• AsyncIO (Asynchronous operations)

Requirements:
• Python 3.9 or higher (3.10 recommended)
• Telegram account
• Telegram API credentials
• Internet connection""",
            "🛠️"
        )

        # Credits
        self._create_section(
            scrollable_frame,
            "Credits & Acknowledgments",
            """This application uses the following open-source projects:

• Telethon - Telegram MTProto API library
  https://github.com/LonamiWebs/Telethon

• Python - Programming language
  https://www.python.org/

Special thanks to:
• Telegram for providing the API
• The open-source community
• All users and contributors""",
            "🙏"
        )

        # Disclaimer
        self._create_section(
            scrollable_frame,
            "Disclaimer",
            """IMPORTANT LEGAL NOTICE:

• This tool is for personal use only
• Respect copyright and intellectual property
• Only download content you have rights to access
• Follow Telegram's Terms of Service
• The developers are not responsible for misuse
• Downloaded content remains property of creators

By using this application, you agree to:
• Use it responsibly and legally
• Not use it for piracy or copyright infringement
• Respect the privacy of channel owners
• Follow all applicable laws in your jurisdiction""",
            "⚖️"
        )

        # Links
        links_frame = ttk.LabelFrame(scrollable_frame, text="🔗 Useful Links", padding="10")
        links_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        links = [
            ("Telegram API", "https://my.telegram.org/apps"),
            ("Telethon Docs", "https://docs.telethon.dev/"),
            ("Python Downloads", "https://www.python.org/downloads/"),
        ]

        for name, url in links:
            link_frame = ttk.Frame(links_frame)
            link_frame.pack(fill=tk.X, pady=2)

            ttk.Label(link_frame, text=f"{name}:").pack(side=tk.LEFT)

            link_label = ttk.Label(
                link_frame,
                text=url,
                foreground="blue",
                cursor="hand2"
            )
            link_label.pack(side=tk.LEFT, padx=(5, 0))
            link_label.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))