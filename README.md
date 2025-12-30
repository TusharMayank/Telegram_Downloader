# Telegram Media Downloader

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

A powerful, user-friendly GUI application built with Python and Tkinter to download various types of media (Audio, Video, Photos, Documents, etc.) from Telegram channels. It utilizes the Telethon library to interact directly with the Telegram API, offering high-performance parallel downloads and session management.

## 🌟 Features

* **Comprehensive Media Support**: Download Audio, Video, Photos, Documents, Voice Messages, Video Notes, Animations (GIFs), and Stickers.
* **Download Modes**:
    * **Single Post**: Download a specific message by ID or URL.
    * **Batch Range**: Download a sequence of posts (e.g., from ID 100 to 200).
    * **Multiple Specific**: Download a comma-separated list of post IDs.
    * **Sequential Scan**: Scan a channel chronologically with options to skip existing files.
* **High Performance**:
    * **Parallel Downloading**: Download multiple files simultaneously.
    * **Configurable Speed**: Adjust chunk sizes, buffer sizes, and concurrency limits.
    * **Performance Presets**: Choose from Conservative, Balanced, Aggressive, or Maximum profiles.
* **Session Management**: Support for multiple Telegram accounts with a built-in session switcher.
* **Smart Resume**: "Skip Existing" feature prevents re-downloading files that are already completed.
* **GUI Authentication**: Login via phone number and OTP directly within the application (supports 2FA).
* **Cross-Platform**: Works on Windows, macOS, and Linux.

## 📋 Requirements

* Python 3.9, 3.10, or 3.11 (3.10 Recommended)
* A Telegram Account
* Telegram API ID and API Hash (see [Configuration](#-configuration))

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/telegram_downloader.git](https://github.com/yourusername/telegram_downloader.git)
    cd telegram_downloader
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

To use this application, you need to obtain your own API credentials from Telegram.

1.  Go to **https://my.telegram.org/apps**.
2.  Log in with your Telegram account.
3.  Click on **API development tools**.
4.  Create a new application (if you haven't already).
5.  Copy the **App api_id** and **App api_hash**.

## 🚀 Usage

1.  **Start the Application**
    ```bash
    python main.py
    ```

2.  **Setup Credentials**
    * Go to the **Settings** tab.
    * Enter your **API ID** and **API Hash**.
    * Click **Save Settings**.

3.  **Login**
    * In the **Settings** tab, enter a name for your session (e.g., "MainAccount").
    * Click **Create & Login**.
    * Enter your phone number (with country code) and the OTP code sent to your Telegram app.

4.  **Download Media**
    * **Single File**: Go to the **Download** tab, enter the Post ID (or full URL) and Channel ID.
    * **Batch**: Go to the **Batch Download** tab. Select the media types you want (Audio, Video, etc.) and choose your download method (Range, Sequential, etc.).

## 📂 Project Structure

```text
telegram_downloader/
├── config/                 # Configuration management
|   ├── __init__.py  
│   ├── settings.py         # App settings loader
│   └── performance.py      # Performance profiles
├── core/                   # Backend logic
|   |── __init__.py  
│   ├── client.py           # Telegram client wrapper
│   ├── downloader.py       # Base download logic
│   └── parallel_downloader.py # Async parallel download logic
├── ui/                     # Graphical User Interface
|   ├── __init__.py  
│   ├── app.py              # Main window controller
│   ├── tabs/               # Individual tab logic
|   |   ├── __init__.py  
|   |   ├── about_tab.py
|   |   ├── batch_tab.py
|   |   ├── download_tab.py
|   |   ├── performance_tab.py
|   |   ├── settings_tab.py
│   ├── components/         # Reusable UI widgets (Login, Logger, etc)
|   |   ├── __init__.py
|   |   ├── logger.py
|   |   ├── login_dialog.py
|   |   ├── media_type_selector.py
|   |   ├── session_switcher.py
├── utils/                  # Helper functions
|   ├── __init__.py  
│   ├── media_types.py      # Media type enums and extensions
│   └── helpers.py          # URL parsing and file handling
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```


## ⚡ Performance Tuning

The application includes a **Performance** tab where you can fine-tune download behavior:

* **Max Concurrent Downloads**: How many files to download at once.
* **Chunk Size**: Larger chunks are faster for big files but use more RAM.
* **Rate Limiting**: Adjust delays between files to avoid `FloodWait` errors from Telegram.

### Presets

* 🐢 **Conservative**: Slow, safe, prevents rate limits.
* ⚖️ **Balanced**: Recommended for general use.
* 🚀 **Aggressive**: Fast, for small files.
* ⚡ **Maximum**: Experimental, highest speed.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal use only.

* Respect copyright and intellectual property rights.
* Only download content you have permission to access.
* The developers are not responsible for any misuse of this tool.
* This application uses the Telegram API but is not endorsed or certified by Telegram.

Copyright (c) 2025 TUSHAR MAYANK
