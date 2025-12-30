"""
Multi-select dropdown for media types
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

from utils.media_types import (
    MediaType,
    MEDIA_TYPE_INFO,
    get_media_type_label,
    get_media_type_short_label,
    get_all_media_types
)


class MediaTypeSelector:
    """Multi-select dropdown for choosing media types to download"""

    def __init__(
            self,
            parent: tk.Widget,
            on_change: Optional[Callable[[List[MediaType]], None]] = None
    ):
        self.parent = parent
        self.on_change = on_change

        # Track selected types
        self.selected_types: List[MediaType] = [MediaType.AUDIO]  # Default
        self.checkbox_vars: dict = {}

        # Create main frame
        self.frame = ttk.LabelFrame(
            parent,
            text="Media Types to Download",
            padding="10"
        )

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the selector widgets"""
        # Info label
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            info_frame,
            text="⚠️ Note: Text messages will not be downloaded",
            foreground="orange"
        ).pack(side=tk.LEFT)

        # Quick select buttons
        quick_frame = ttk.Frame(self.frame)
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quick_frame, text="Quick Select:").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            quick_frame,
            text="All",
            width=8,
            command=self._select_all
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quick_frame,
            text="None",
            width=8,
            command=self._select_none
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quick_frame,
            text="Media Only",
            width=10,
            command=self._select_media_only
        ).pack(side=tk.LEFT, padx=2)

        # Checkboxes frame with grid layout
        checkbox_frame = ttk.Frame(self.frame)
        checkbox_frame.pack(fill=tk.BOTH, expand=True)

        # Create checkboxes in 2 columns
        media_types = get_all_media_types()

        for idx, media_type in enumerate(media_types):
            row = idx // 2
            col = idx % 2

            # Create variable
            var = tk.BooleanVar(value=(media_type == MediaType.AUDIO))
            self.checkbox_vars[media_type] = var

            # Get info
            info = MEDIA_TYPE_INFO.get(media_type, {})
            icon = info.get('icon', '')
            label = info.get('label', media_type.value)
            extensions = info.get('extensions', '')

            # Create frame for each option
            option_frame = ttk.Frame(checkbox_frame)
            option_frame.grid(row=row, column=col, sticky=tk.W, padx=5, pady=3)

            # Checkbox
            cb = ttk.Checkbutton(
                option_frame,
                text=f"{icon} {label}",
                variable=var,
                command=self._on_checkbox_change
            )
            cb.pack(side=tk.LEFT)

            # Extensions label
            ext_label = ttk.Label(
                option_frame,
                text=f"({extensions})",
                foreground="gray",
                font=('Arial', 8)
            )
            ext_label.pack(side=tk.LEFT, padx=(5, 0))

        # Selected summary
        self.summary_var = tk.StringVar()
        self._update_summary()

        summary_frame = ttk.Frame(self.frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            summary_frame,
            text="Selected:",
            font=('Arial', 9, 'bold')
        ).pack(side=tk.LEFT)

        ttk.Label(
            summary_frame,
            textvariable=self.summary_var,
            font=('Arial', 9),
            wraplength=400
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _on_checkbox_change(self) -> None:
        """Handle checkbox state change"""
        self.selected_types = [
            media_type
            for media_type, var in self.checkbox_vars.items()
            if var.get()
        ]

        self._update_summary()

        if self.on_change:
            self.on_change(self.selected_types)

    def _update_summary(self) -> None:
        """Update the selected summary text"""
        if not self.selected_types:
            self.summary_var.set("None selected")
        elif len(self.selected_types) == len(MediaType):
            self.summary_var.set("All media types")
        else:
            labels = [
                get_media_type_short_label(t)
                for t in self.selected_types
            ]
            self.summary_var.set(", ".join(labels))

    def _select_all(self) -> None:
        """Select all media types"""
        for var in self.checkbox_vars.values():
            var.set(True)
        self._on_checkbox_change()

    def _select_none(self) -> None:
        """Deselect all media types"""
        for var in self.checkbox_vars.values():
            var.set(False)
        self._on_checkbox_change()

    def _select_media_only(self) -> None:
        """Select only common media types (audio, video, photo)"""
        media_only = [MediaType.AUDIO, MediaType.VIDEO, MediaType.PHOTO]

        for media_type, var in self.checkbox_vars.items():
            var.set(media_type in media_only)

        self._on_checkbox_change()

    def get_selected(self) -> List[MediaType]:
        """Get list of selected media types"""
        return self.selected_types.copy()

    def set_selected(self, types: List[MediaType]) -> None:
        """Set selected media types"""
        for media_type, var in self.checkbox_vars.items():
            var.set(media_type in types)
        self._on_checkbox_change()


class MediaTypeSelectorCompact:
    """Compact version with dropdown-style display"""

    def __init__(
            self,
            parent: tk.Widget,
            on_change: Optional[Callable[[List[MediaType]], None]] = None
    ):
        self.parent = parent
        self.on_change = on_change

        self.selected_types: List[MediaType] = [MediaType.AUDIO]
        self.checkbox_vars: dict = {}
        self.popup: Optional[tk.Toplevel] = None

        self.frame = ttk.Frame(parent)
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create compact selector widgets"""
        # Main button/display
        self.display_var = tk.StringVar(value="🎵 Audio")

        display_frame = ttk.Frame(self.frame)
        display_frame.pack(fill=tk.X)

        ttk.Label(display_frame, text="Download:").pack(side=tk.LEFT, padx=(0, 5))

        self.display_btn = ttk.Button(
            display_frame,
            textvariable=self.display_var,
            command=self._toggle_popup,
            width=40
        )
        self.display_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            display_frame,
            text="▼",
            width=3,
            command=self._toggle_popup
        ).pack(side=tk.LEFT)

    def _toggle_popup(self) -> None:
        """Toggle the selection popup"""
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
            self.popup = None
        else:
            self._show_popup()

    def _show_popup(self) -> None:
        """Show the selection popup"""
        self.popup = tk.Toplevel(self.parent)
        self.popup.title("Select Media Types")
        self.popup.resizable(False, False)
        self.popup.transient(self.parent.winfo_toplevel())

        # Position near the button
        x = self.display_btn.winfo_rootx()
        y = self.display_btn.winfo_rooty() + self.display_btn.winfo_height()
        self.popup.geometry(f"+{x}+{y}")

        # Create content
        main_frame = ttk.Frame(self.popup, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Warning
        ttk.Label(
            main_frame,
            text="⚠️ Text messages will not be downloaded",
            foreground="orange"
        ).pack(pady=(0, 10))

        # Quick buttons
        quick_frame = ttk.Frame(main_frame)
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            quick_frame, text="All", width=8,
            command=self._select_all
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quick_frame, text="None", width=8,
            command=self._select_none
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quick_frame, text="Media Only", width=10,
            command=self._select_media_only
        ).pack(side=tk.LEFT, padx=2)

        # Checkboxes
        for media_type in get_all_media_types():
            info = MEDIA_TYPE_INFO.get(media_type, {})

            var = tk.BooleanVar(value=(media_type in self.selected_types))
            self.checkbox_vars[media_type] = var

            cb_frame = ttk.Frame(main_frame)
            cb_frame.pack(fill=tk.X, pady=2)

            ttk.Checkbutton(
                cb_frame,
                text=f"{info.get('icon', '')} {info.get('label', '')}",
                variable=var,
                command=self._on_checkbox_change
            ).pack(side=tk.LEFT)

            ttk.Label(
                cb_frame,
                text=f"({info.get('extensions', '')})",
                foreground="gray",
                font=('Arial', 8)
            ).pack(side=tk.LEFT, padx=(5, 0))

        # Close button
        ttk.Button(
            main_frame,
            text="Done",
            command=self._close_popup
        ).pack(pady=(10, 0))

        # Close on focus out
        self.popup.bind('<FocusOut>', lambda e: self._delayed_close())

    def _delayed_close(self) -> None:
        """Close popup after a small delay (to allow button clicks)"""
        if self.popup:
            self.popup.after(200, self._check_and_close)

    def _check_and_close(self) -> None:
        """Check if popup should close"""
        if self.popup and self.popup.winfo_exists():
            try:
                if not self.popup.focus_get():
                    self._close_popup()
            except:
                pass

    def _close_popup(self) -> None:
        """Close the popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None

    def _on_checkbox_change(self) -> None:
        """Handle checkbox change"""
        self.selected_types = [
            media_type
            for media_type, var in self.checkbox_vars.items()
            if var.get()
        ]

        self._update_display()

        if self.on_change:
            self.on_change(self.selected_types)

    def _update_display(self) -> None:
        """Update the display button text"""
        if not self.selected_types:
            self.display_var.set("None selected")
        elif len(self.selected_types) == len(MediaType):
            self.display_var.set("📁 All media types")
        elif len(self.selected_types) <= 3:
            labels = [
                get_media_type_short_label(t)
                for t in self.selected_types
            ]
            self.display_var.set(", ".join(labels))
        else:
            self.display_var.set(f"{len(self.selected_types)} types selected")

    def _select_all(self) -> None:
        """Select all"""
        for var in self.checkbox_vars.values():
            var.set(True)
        self._on_checkbox_change()

    def _select_none(self) -> None:
        """Select none"""
        for var in self.checkbox_vars.values():
            var.set(False)
        self._on_checkbox_change()

    def _select_media_only(self) -> None:
        """Select media only"""
        media_only = [MediaType.AUDIO, MediaType.VIDEO, MediaType.PHOTO]
        for media_type, var in self.checkbox_vars.items():
            var.set(media_type in media_only)
        self._on_checkbox_change()

    def get_selected(self) -> List[MediaType]:
        """Get selected types"""
        return self.selected_types.copy()

    def set_selected(self, types: List[MediaType]) -> None:
        """Set selected types"""
        self.selected_types = types.copy()
        for media_type, var in self.checkbox_vars.items():
            var.set(media_type in types)
        self._update_display()