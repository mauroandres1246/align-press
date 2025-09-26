"""
Control Panel Component for AlignPress v2

Displays system metrics, status information, and control buttons
"""
from __future__ import annotations

import logging
import tkinter as tk
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    import tkinter as ctk
    CTK_AVAILABLE = False

from ...config.models import AlignPressConfig
from ...controller.state_manager import AppState, AppMode

logger = logging.getLogger(__name__)


class ControlPanel:
    """Control panel with metrics, status, and controls"""

    def __init__(self, parent):
        self.parent = parent

        # UI components
        self.frame = None
        self.status_labels = {}
        self.metric_labels = {}
        self.control_buttons = {}

        # State tracking
        self.current_config: Optional[AlignPressConfig] = None
        self.current_state: Optional[AppState] = None

        # Setup the control panel
        self._setup_panel()

        logger.info("ControlPanel initialized")

    def _setup_panel(self):
        """Setup the control panel UI"""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent)
            self.frame.configure(corner_radius=10)
        else:
            self.frame = tk.Frame(self.parent, bg="white", relief="raised", bd=2)

        # Create sections
        self._create_title_section()
        self._create_status_section()
        self._create_metrics_section()
        self._create_controls_section()

    def _create_title_section(self):
        """Create the title section"""
        if CTK_AVAILABLE:
            title_label = ctk.CTkLabel(
                self.frame,
                text="AlignPress v2",
                font=ctk.CTkFont(size=18, weight="bold")
            )
        else:
            title_label = tk.Label(
                self.frame,
                text="AlignPress v2",
                font=("Arial", 16, "bold"),
                bg="white"
            )

        title_label.pack(pady=(15, 5))

    def _create_status_section(self):
        """Create the status information section"""
        if CTK_AVAILABLE:
            status_frame = ctk.CTkFrame(self.frame)
            status_title = ctk.CTkLabel(
                status_frame,
                text="System Status",
                font=ctk.CTkFont(size=14, weight="bold")
            )
        else:
            status_frame = tk.Frame(self.frame, bg="lightgray", relief="groove", bd=2)
            status_title = tk.Label(
                status_frame,
                text="System Status",
                font=("Arial", 12, "bold"),
                bg="lightgray"
            )

        status_frame.pack(fill="x", padx=10, pady=5)
        status_title.pack(pady=5)

        # Status labels
        status_info = [
            ("Mode", "IDLE"),
            ("Camera", "Disconnected"),
            ("Calibration", "Not Set"),
            ("Hardware", "Mock"),
            ("Detection", "Stopped")
        ]

        for label_name, default_value in status_info:
            if CTK_AVAILABLE:
                label_frame = ctk.CTkFrame(status_frame, height=25)
                label_frame.pack(fill="x", padx=10, pady=2)

                name_label = ctk.CTkLabel(
                    label_frame,
                    text=f"{label_name}:",
                    font=ctk.CTkFont(size=11),
                    width=80,
                    anchor="w"
                )
                name_label.pack(side="left", padx=5)

                value_label = ctk.CTkLabel(
                    label_frame,
                    text=default_value,
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                value_label.pack(side="left", fill="x", expand=True)
            else:
                label_frame = tk.Frame(status_frame, bg="lightgray")
                label_frame.pack(fill="x", padx=10, pady=1)

                name_label = tk.Label(
                    label_frame,
                    text=f"{label_name}:",
                    font=("Arial", 10),
                    bg="lightgray",
                    width=12,
                    anchor="w"
                )
                name_label.pack(side="left")

                value_label = tk.Label(
                    label_frame,
                    text=default_value,
                    font=("Arial", 10),
                    bg="lightgray",
                    anchor="w"
                )
                value_label.pack(side="left", fill="x", expand=True)

            self.status_labels[label_name.lower()] = value_label

    def _create_metrics_section(self):
        """Create the metrics section"""
        if CTK_AVAILABLE:
            metrics_frame = ctk.CTkFrame(self.frame)
            metrics_title = ctk.CTkLabel(
                metrics_frame,
                text="Detection Metrics",
                font=ctk.CTkFont(size=14, weight="bold")
            )
        else:
            metrics_frame = tk.Frame(self.frame, bg="lightblue", relief="groove", bd=2)
            metrics_title = tk.Label(
                metrics_frame,
                text="Detection Metrics",
                font=("Arial", 12, "bold"),
                bg="lightblue"
            )

        metrics_frame.pack(fill="x", padx=10, pady=5)
        metrics_title.pack(pady=5)

        # Metrics labels
        metrics_info = [
            ("Total Detections", "0"),
            ("Successful", "0"),
            ("Failed", "0"),
            ("Success Rate", "0%"),
            ("Avg Confidence", "0.00"),
            ("Last Detection", "Never")
        ]

        for label_name, default_value in metrics_info:
            if CTK_AVAILABLE:
                label_frame = ctk.CTkFrame(metrics_frame, height=25)
                label_frame.pack(fill="x", padx=10, pady=2)

                name_label = ctk.CTkLabel(
                    label_frame,
                    text=f"{label_name}:",
                    font=ctk.CTkFont(size=11),
                    width=100,
                    anchor="w"
                )
                name_label.pack(side="left", padx=5)

                value_label = ctk.CTkLabel(
                    label_frame,
                    text=default_value,
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                value_label.pack(side="left", fill="x", expand=True)
            else:
                label_frame = tk.Frame(metrics_frame, bg="lightblue")
                label_frame.pack(fill="x", padx=10, pady=1)

                name_label = tk.Label(
                    label_frame,
                    text=f"{label_name}:",
                    font=("Arial", 10),
                    bg="lightblue",
                    width=15,
                    anchor="w"
                )
                name_label.pack(side="left")

                value_label = tk.Label(
                    label_frame,
                    text=default_value,
                    font=("Arial", 10),
                    bg="lightblue",
                    anchor="w"
                )
                value_label.pack(side="left", fill="x", expand=True)

            metric_key = label_name.lower().replace(" ", "_")
            self.metric_labels[metric_key] = value_label

    def _create_controls_section(self):
        """Create the control buttons section"""
        if CTK_AVAILABLE:
            controls_frame = ctk.CTkFrame(self.frame)
            controls_title = ctk.CTkLabel(
                controls_frame,
                text="Controls",
                font=ctk.CTkFont(size=14, weight="bold")
            )
        else:
            controls_frame = tk.Frame(self.frame, bg="lightgreen", relief="groove", bd=2)
            controls_title = tk.Label(
                controls_frame,
                text="Controls",
                font=("Arial", 12, "bold"),
                bg="lightgreen"
            )

        controls_frame.pack(fill="x", padx=10, pady=5)
        controls_title.pack(pady=5)

        # Control buttons
        button_configs = [
            ("Start Detection", "start", "green"),
            ("Stop Detection", "stop", "red"),
            ("Calibrate Camera", "calibrate", "blue"),
            ("Configuration", "config", "gray"),
            ("Reset Metrics", "reset", "orange")
        ]

        for button_text, button_key, button_color in button_configs:
            if CTK_AVAILABLE:
                button = ctk.CTkButton(
                    controls_frame,
                    text=button_text,
                    height=35,
                    fg_color=button_color,
                    hover_color=self._darker_color(button_color),
                    command=lambda k=button_key: self._on_button_click(k)
                )
            else:
                button = tk.Button(
                    controls_frame,
                    text=button_text,
                    bg=button_color,
                    fg="white",
                    font=("Arial", 10),
                    command=lambda k=button_key: self._on_button_click(k)
                )

            button.pack(fill="x", padx=15, pady=3)
            self.control_buttons[button_key] = button

    def _darker_color(self, color: str) -> str:
        """Get a darker version of a color for hover effect"""
        color_map = {
            "green": "#2d5a2d",
            "red": "#8b0000",
            "blue": "#000080",
            "gray": "#404040",
            "orange": "#cc6600"
        }
        return color_map.get(color, "#333333")

    def _on_button_click(self, button_key: str):
        """Handle button clicks"""
        logger.info(f"Control panel button clicked: {button_key}")
        # Button click callbacks will be set by the main window

    def update_status(self, status_updates: Dict[str, Any]):
        """Update status labels"""
        for key, value in status_updates.items():
            if key in self.status_labels:
                self.status_labels[key].configure(text=str(value))

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update metrics labels"""
        for key, value in metrics.items():
            if key in self.metric_labels:
                self.metric_labels[key].configure(text=str(value))

    def set_button_command(self, button_key: str, command):
        """Set command for a specific button"""
        if button_key in self.control_buttons:
            self.control_buttons[button_key].configure(command=command)

    def enable_button(self, button_key: str, enabled: bool = True):
        """Enable or disable a specific button"""
        if button_key in self.control_buttons:
            state = "normal" if enabled else "disabled"
            if CTK_AVAILABLE:
                # CustomTkinter buttons don't have state, use configure
                button = self.control_buttons[button_key]
                if enabled:
                    button.configure(state="normal")
                else:
                    button.configure(state="disabled")
            else:
                self.control_buttons[button_key].configure(state=state)

    def update_from_config(self, config: AlignPressConfig):
        """Update display based on configuration"""
        self.current_config = config

        # Update status based on config
        status_updates = {
            "calibration": "Available" if config.calibration else "Not Set",
            "hardware": "Mock" if hasattr(config.hardware, 'camera') else "None"
        }

        # Update active session info
        if config.session.active_platen_id:
            status_updates["mode"] = "Ready"

        self.update_status(status_updates)

    def update_from_state(self, state: AppState):
        """Update display based on application state"""
        self.current_state = state

        # Update status based on state
        status_updates = {
            "mode": state.mode.value,
            "detection": "Running" if state.mode == AppMode.DETECTING else "Stopped"
        }

        self.update_status(status_updates)

        # Update button states based on mode
        if state.mode == AppMode.DETECTING:
            self.enable_button("start", False)
            self.enable_button("stop", True)
        else:
            self.enable_button("start", state.is_ready_for_detection)
            self.enable_button("stop", False)

    def get_frame(self) -> tk.Frame:
        """Get the control panel frame widget"""
        return self.frame


def create_control_panel(parent) -> ControlPanel:
    """Create a control panel component"""
    return ControlPanel(parent)