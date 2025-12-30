"""
Performance settings tab UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from config.performance import (
    PerformanceConfig,
    PerformanceConfigManager,
    PERFORMANCE_PRESETS,
    get_preset
)


class PerformanceTab:
    """Performance settings tab"""

    def __init__(self, parent, shared_vars, logger, app):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app

        # Load performance config
        self.perf_manager = PerformanceConfigManager()

        # Create variables
        self.perf_vars = self._create_variables()

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

        # Load current values
        self._load_values()

    def _create_variables(self) -> Dict[str, tk.Variable]:
        """Create Tkinter variables for settings"""
        return {
            # Parallel Downloads
            'enabled_parallel': tk.BooleanVar(value=True),
            'max_concurrent': tk.IntVar(value=3),

            # Connection
            'connection_retries': tk.IntVar(value=5),
            'retry_delay': tk.DoubleVar(value=1.0),
            'request_timeout': tk.IntVar(value=60),

            # Chunk/Buffer
            'chunk_size': tk.IntVar(value=512),
            'buffer_size': tk.IntVar(value=1024),

            # Rate Limiting
            'delay_between_files': tk.DoubleVar(value=0.5),
            'delay_between_batches': tk.DoubleVar(value=2.0),
            'batch_size': tk.IntVar(value=10),
            'auto_flood_wait': tk.BooleanVar(value=True),

            # Network
            'use_ipv6': tk.BooleanVar(value=False),

            # Progress
            'show_file_progress': tk.BooleanVar(value=True),
            'progress_interval': tk.DoubleVar(value=0.5),

            # Advanced
            'keep_alive': tk.BooleanVar(value=True),
            'max_retries': tk.IntVar(value=3),
            'skip_failed': tk.BooleanVar(value=True),

            # Preset
            'preset': tk.StringVar(value='balanced')
        }

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Create canvas with scrollbar for many settings
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Make scrollable frame expand to canvas width
        def configure_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll function for mouse wheel and touchpad
        def _on_scroll(event):
            # Check if scrolling is possible
            if canvas.yview() == (0.0, 1.0):
                return

            # Handle different platforms
            if event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(1, "units")
            else:
                # Windows and MacOS
                if event.delta != 0:
                    if abs(event.delta) >= 120:
                        # Mouse wheel (Windows sends 120 per notch)
                        scroll_units = int(-1 * (event.delta / 120))
                    else:
                        # Touchpad (smaller increments)
                        scroll_units = int(-1 * (event.delta / 40))
                        if scroll_units == 0:
                            scroll_units = -1 if event.delta > 0 else 1
                    canvas.yview_scroll(scroll_units, "units")

        # Bind scroll to all widgets recursively
        def bind_scroll(widget):
            widget.bind("<MouseWheel>", _on_scroll, add="+")
            widget.bind("<Button-4>", _on_scroll, add="+")  # Linux
            widget.bind("<Button-5>", _on_scroll, add="+")  # Linux
            for child in widget.winfo_children():
                bind_scroll(child)

        # Initial binding
        bind_scroll(canvas)
        bind_scroll(scrollable_frame)

        # Re-bind when entering the area
        def on_enter(event):
            bind_scroll(scrollable_frame)

        canvas.bind("<Enter>", on_enter)
        scrollable_frame.bind("<Enter>", on_enter)

        # Store for later use
        self._bind_scroll = bind_scroll
        self._canvas = canvas

        # === Presets Section ===
        preset_frame = ttk.LabelFrame(
            scrollable_frame,
            text="⚡ Quick Presets",
            padding="10"
        )
        preset_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(
            preset_frame,
            text="Select a preset configuration:",
        ).pack(anchor=tk.W)

        preset_btn_frame = ttk.Frame(preset_frame)
        preset_btn_frame.pack(fill=tk.X, pady=5)

        presets = [
            ('🐢 Conservative', 'conservative', 'Slow but safe, avoids rate limits'),
            ('⚖️ Balanced', 'balanced', 'Good balance of speed and safety'),
            ('🚀 Aggressive', 'aggressive', 'Faster, may trigger rate limits'),
            ('⚡ Maximum', 'maximum', 'Fastest, higher risk of limits')
        ]

        for label, preset_name, tooltip in presets:
            btn = ttk.Button(
                preset_btn_frame,
                text=label,
                command=lambda p=preset_name: self._apply_preset(p),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=5)
            self._create_tooltip(btn, tooltip)

        # === Parallel Downloads Section ===
        parallel_frame = ttk.LabelFrame(
            scrollable_frame,
            text="🔀 Parallel Downloads",
            padding="10"
        )
        parallel_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Checkbutton(
            parallel_frame,
            text="Enable parallel downloads",
            variable=self.perf_vars['enabled_parallel']
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(parallel_frame, text="Max concurrent downloads:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )

        concurrent_frame = ttk.Frame(parallel_frame)
        concurrent_frame.grid(row=1, column=1, sticky=tk.W, pady=2)

        concurrent_scale = ttk.Scale(
            concurrent_frame,
            from_=1,
            to=10,
            variable=self.perf_vars['max_concurrent'],
            orient=tk.HORIZONTAL,
            length=150
        )
        concurrent_scale.pack(side=tk.LEFT)

        ttk.Label(
            concurrent_frame,
            textvariable=self.perf_vars['max_concurrent'],
            width=3
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            parallel_frame,
            text="⚠️ Higher values = faster but more likely to hit rate limits",
            foreground="orange"
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        # === Chunk/Buffer Settings ===
        chunk_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📦 Chunk & Buffer Settings",
            padding="10"
        )
        chunk_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(chunk_frame, text="Download chunk size (KB):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )

        chunk_combo = ttk.Combobox(
            chunk_frame,
            textvariable=self.perf_vars['chunk_size'],
            values=[128, 256, 512, 1024, 2048, 4096],
            width=10,
            state='readonly'
        )
        chunk_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(
            chunk_frame,
            text="Larger = faster for big files, smaller = more responsive",
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, pady=2, padx=5)

        ttk.Label(chunk_frame, text="Buffer size (KB):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )

        buffer_combo = ttk.Combobox(
            chunk_frame,
            textvariable=self.perf_vars['buffer_size'],
            values=[512, 1024, 2048, 4096, 8192],
            width=10,
            state='readonly'
        )
        buffer_combo.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        # === Rate Limiting Section ===
        rate_frame = ttk.LabelFrame(
            scrollable_frame,
            text="⏱️ Rate Limiting & Delays",
            padding="10"
        )
        rate_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(rate_frame, text="Delay between files (seconds):").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            rate_frame,
            textvariable=self.perf_vars['delay_between_files'],
            from_=0.0,
            to=5.0,
            increment=0.1,
            width=8
        ).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(rate_frame, text="Delay between batches (seconds):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            rate_frame,
            textvariable=self.perf_vars['delay_between_batches'],
            from_=0.0,
            to=10.0,
            increment=0.5,
            width=8
        ).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(rate_frame, text="Batch size (files per batch):").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            rate_frame,
            textvariable=self.perf_vars['batch_size'],
            from_=1,
            to=100,
            increment=5,
            width=8
        ).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Checkbutton(
            rate_frame,
            text="Auto-handle FloodWait errors (wait and retry)",
            variable=self.perf_vars['auto_flood_wait']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

        # === Connection Settings ===
        conn_frame = ttk.LabelFrame(
            scrollable_frame,
            text="🔌 Connection Settings",
            padding="10"
        )
        conn_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(conn_frame, text="Connection retries:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            conn_frame,
            textvariable=self.perf_vars['connection_retries'],
            from_=1,
            to=10,
            width=8
        ).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(conn_frame, text="Retry delay (seconds):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            conn_frame,
            textvariable=self.perf_vars['retry_delay'],
            from_=0.5,
            to=10.0,
            increment=0.5,
            width=8
        ).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(conn_frame, text="Request timeout (seconds):").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            conn_frame,
            textvariable=self.perf_vars['request_timeout'],
            from_=10,
            to=300,
            increment=10,
            width=8
        ).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Checkbutton(
            conn_frame,
            text="Use IPv6 (if available)",
            variable=self.perf_vars['use_ipv6']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Checkbutton(
            conn_frame,
            text="Keep connection alive between downloads",
            variable=self.perf_vars['keep_alive']
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

        # === Progress Settings ===
        progress_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📊 Progress & Display",
            padding="10"
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Checkbutton(
            progress_frame,
            text="Show per-file progress",
            variable=self.perf_vars['show_file_progress']
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(progress_frame, text="Progress update interval (seconds):").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            progress_frame,
            textvariable=self.perf_vars['progress_interval'],
            from_=0.1,
            to=2.0,
            increment=0.1,
            width=8
        ).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        # === Error Handling ===
        error_frame = ttk.LabelFrame(
            scrollable_frame,
            text="⚠️ Error Handling",
            padding="10"
        )
        error_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(error_frame, text="Max retries per file:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            error_frame,
            textvariable=self.perf_vars['max_retries'],
            from_=0,
            to=10,
            width=8
        ).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Checkbutton(
            error_frame,
            text="Skip failed files and continue (vs. stop on error)",
            variable=self.perf_vars['skip_failed']
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # === Buttons ===
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=10, padx=5)

        ttk.Button(
            btn_frame,
            text="💾 Save Settings",
            command=self._save_settings
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🔄 Reset to Defaults",
            command=self._reset_settings
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="📋 Apply to Current Session",
            command=self._apply_settings
        ).pack(side=tk.LEFT, padx=5)

        # === Info Section ===
        info_frame = ttk.LabelFrame(
            scrollable_frame,
            text="ℹ️ Performance Tips",
            padding="10"
        )
        info_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        tips_text = """
    💡 Tips for faster downloads:

    • Start with "Balanced" preset and adjust if needed
    • If you get rate limited often, use "Conservative"
    • For large files (videos), increase chunk size
    • Parallel downloads speed up batches significantly
    • Keep delays low but not zero to avoid limits
    • Enable "Keep connection alive" for batch downloads
    • If downloads fail, increase retry count and delay

    ⚠️ Warning: "Maximum" preset may trigger rate limits.
       Use with caution and be prepared for FloodWait errors.
        """

        ttk.Label(
            info_frame,
            text=tips_text,
            justify=tk.LEFT,
            wraplength=500
        ).pack(anchor=tk.W)

        # Bind scroll to all widgets after creation
        self._bind_scroll(scrollable_frame)

    def _create_tooltip(self, widget, text: str) -> None:
        """Create a simple tooltip for a widget"""

        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = ttk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                padding=5
            )
            label.pack()

            widget.tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def _load_values(self) -> None:
        """Load values from config to variables"""
        config = self.perf_manager.config

        self.perf_vars['enabled_parallel'].set(config.enabled_parallel)
        self.perf_vars['max_concurrent'].set(config.max_concurrent_downloads)
        self.perf_vars['connection_retries'].set(config.connection_retries)
        self.perf_vars['retry_delay'].set(config.retry_delay)
        self.perf_vars['request_timeout'].set(config.request_timeout)
        self.perf_vars['chunk_size'].set(config.download_chunk_size)
        self.perf_vars['buffer_size'].set(config.buffer_size)
        self.perf_vars['delay_between_files'].set(config.delay_between_files)
        self.perf_vars['delay_between_batches'].set(config.delay_between_batches)
        self.perf_vars['batch_size'].set(config.batch_size)
        self.perf_vars['auto_flood_wait'].set(config.auto_handle_flood_wait)
        self.perf_vars['use_ipv6'].set(config.use_ipv6)
        self.perf_vars['show_file_progress'].set(config.show_file_progress)
        self.perf_vars['progress_interval'].set(config.progress_update_interval)
        self.perf_vars['keep_alive'].set(config.keep_connection_alive)
        self.perf_vars['max_retries'].set(config.max_retries_per_file)
        self.perf_vars['skip_failed'].set(config.skip_failed_files)

    def _get_config_from_vars(self) -> PerformanceConfig:
        """Create config from current variable values"""
        return PerformanceConfig(
            enabled_parallel=self.perf_vars['enabled_parallel'].get(),
            max_concurrent_downloads=self.perf_vars['max_concurrent'].get(),
            connection_retries=self.perf_vars['connection_retries'].get(),
            retry_delay=self.perf_vars['retry_delay'].get(),
            request_timeout=self.perf_vars['request_timeout'].get(),
            download_chunk_size=self.perf_vars['chunk_size'].get(),
            buffer_size=self.perf_vars['buffer_size'].get(),
            delay_between_files=self.perf_vars['delay_between_files'].get(),
            delay_between_batches=self.perf_vars['delay_between_batches'].get(),
            batch_size=self.perf_vars['batch_size'].get(),
            auto_handle_flood_wait=self.perf_vars['auto_flood_wait'].get(),
            use_ipv6=self.perf_vars['use_ipv6'].get(),
            show_file_progress=self.perf_vars['show_file_progress'].get(),
            progress_update_interval=self.perf_vars['progress_interval'].get(),
            keep_connection_alive=self.perf_vars['keep_alive'].get(),
            max_retries_per_file=self.perf_vars['max_retries'].get(),
            skip_failed_files=self.perf_vars['skip_failed'].get()
        )

    def _apply_preset(self, preset_name: str) -> None:
        """Apply a preset configuration"""
        preset = get_preset(preset_name)
        self.perf_manager.config = preset
        self._load_values()
        self.perf_vars['preset'].set(preset_name)
        self.logger.log(f"⚡ Applied '{preset_name}' performance preset")

    def _save_settings(self) -> None:
        """Save current settings to file"""
        self.perf_manager.config = self._get_config_from_vars()

        if self.perf_manager.save():
            self.logger.log("✅ Performance settings saved!")
            messagebox.showinfo("Success", "Performance settings saved!")
        else:
            self.logger.log("❌ Failed to save performance settings")
            messagebox.showerror("Error", "Failed to save settings")

    def _reset_settings(self) -> None:
        """Reset to default settings"""
        if messagebox.askyesno("Confirm", "Reset all performance settings to defaults?"):
            self.perf_manager.reset()
            self._load_values()
            self.logger.log("🔄 Performance settings reset to defaults")

    def _apply_settings(self) -> None:
        """Apply settings to current session without saving"""
        self.perf_manager.config = self._get_config_from_vars()
        self.logger.log("✅ Performance settings applied to current session")
        messagebox.showinfo("Applied", "Settings applied to current session.\nUse 'Save' to persist changes.")

    def get_performance_config(self) -> PerformanceConfig:
        """Get current performance configuration"""
        return self._get_config_from_vars()