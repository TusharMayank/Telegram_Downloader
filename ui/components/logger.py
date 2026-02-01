"""
Logger component for displaying log messages
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from typing import Optional, Any
import platform

from utils.constants import LOG_FONT


class LoggerComponent:
    """Reusable logger component"""

    def __init__(self):
        self.log_widget: Optional[scrolledtext.ScrolledText] = None
        self.root: Any = None

    def create_widget(self, parent: tk.Widget) -> scrolledtext.ScrolledText:
        """Create the log widget"""
        self.log_widget = scrolledtext.ScrolledText(
            parent,
            height=10,
            wrap=tk.WORD,
            font=LOG_FONT,
            state=tk.DISABLED  # Set to read-only
        )
        self.root = parent.winfo_toplevel()
        
        # Setup scrolling bindings
        self._setup_scrolling()
        
        return self.log_widget

    def _setup_scrolling(self) -> None:
        """Setup mouse wheel scrolling"""
        # Bind enter/leave events to handle focus/scrolling
        if self.log_widget:
            self.log_widget.bind('<Enter>', self._on_enter)
            self.log_widget.bind('<Leave>', self._on_leave)

    def _on_enter(self, event) -> None:
        """Handle mouse enter"""
        if not self.log_widget:
            return

        # Bind global mouse wheel events when mouse is over widget
        system = platform.system()
        if system == "Linux":
            self.log_widget.bind_all("<Button-4>", self._on_mousewheel)
            self.log_widget.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.log_widget.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_leave(self, event) -> None:
        """Handle mouse leave"""
        if not self.log_widget:
            return

        # Unbind global mouse wheel events
        system = platform.system()
        if system == "Linux":
            self.log_widget.unbind_all("<Button-4>")
            self.log_widget.unbind_all("<Button-5>")
        else:
            self.log_widget.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event) -> Optional[str]:
        """Handle scroll event"""
        if self.log_widget:
            system = platform.system()
            if system == "Windows":
                self.log_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif system == "Darwin": # macOS
                self.log_widget.yview_scroll(int(-1 * event.delta), "units")
            elif system == "Linux":
                if event.num == 4:
                    self.log_widget.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.log_widget.yview_scroll(1, "units")
            
            return "break" # Prevent event propagation
        return None

    def log(self, message: str) -> None:
        """Add a message to the log"""
        if self.log_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Enable editing temporarily
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_widget.see(tk.END)
            # Disable editing
            self.log_widget.config(state=tk.DISABLED)

            if self.root:
                self.root.update_idletasks()

    def clear(self) -> None:
        """Clear the log"""
        if self.log_widget:
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.delete(1.0, tk.END)
            self.log_widget.config(state=tk.DISABLED)