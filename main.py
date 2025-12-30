#!/usr/bin/env python3
"""
Telegram Audio Downloader
Entry point for the application
"""

import tkinter as tk
from ui.app import TelegramAudioDownloaderApp


def main():
    root = tk.Tk()
    app = TelegramAudioDownloaderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()