"""
Logger component for displaying log messages
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from typing import Optional

from utils.constants import LOG_FONT


class LoggerComponent:
    """Reusable logger component"""

    def __init__(self):
        self.log_widget: Optional[scrolledtext.ScrolledText] = None
        self.root: Optional[tk.Tk] = None

    def create_widget(self, parent: tk.Widget) -> scrolledtext.ScrolledText:
        """Create the log widget"""
        self.log_widget = scrolledtext.ScrolledText(
            parent,
            height=10,
            wrap=tk.WORD,
            font=LOG_FONT
        )
        self.root = parent.winfo_toplevel()
        return self.log_widget

    def log(self, message: str) -> None:
        """Add a message to the log"""
        if self.log_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_widget.see(tk.END)

            if self.root:
                self.root.update_idletasks()

    def clear(self) -> None:
        """Clear the log"""
        if self.log_widget:
            self.log_widget.delete(1.0, tk.END)