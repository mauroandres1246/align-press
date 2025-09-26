"""
Main Window for AlignPress v2

Single screen layout with visual-first design
"""
from __future__ import annotations

import logging
import tkinter as tk

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    # Fallback to regular tkinter if customtkinter not available
    import tkinter as ctk
    CTK_AVAILABLE = False

from ..controller.app_controller import AppController
from ..controller.event_bus import EventType, get_event_bus
from ..controller.state_manager import AppMode
from .components import create_camera_viewport, create_control_panel

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window using CustomTkinter"""

    def __init__(self, controller: AppController):
        self.controller = controller
        self.event_bus = get_event_bus()

        # Initialize CustomTkinter appearance
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("light")  # "dark" or "light"
            ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
            logger.info("Using CustomTkinter for modern UI")
        else:
            logger.warning("CustomTkinter not available, using standard Tkinter")

        # Create main window
        self.root = ctk.CTk() if CTK_AVAILABLE else tk.Tk()
        self.root.title("AlignPress v2")
        self.root.geometry("1200x800")

        # Configure window
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Initialize components
        self._setup_layout()
        self._setup_components()
        self._setup_event_handlers()

        logger.info("MainWindow initialized")

    def _setup_layout(self):
        """Setup the main UI layout"""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=3)  # Viewport gets more space
        self.root.grid_columnconfigure(1, weight=1)  # Control panel
        self.root.grid_rowconfigure(0, weight=1)     # Main content
        self.root.grid_rowconfigure(1, weight=0)     # Status bar

    def _setup_components(self):
        """Setup the UI components"""
        # Create camera viewport
        self.viewport = create_camera_viewport(self.root, width=800, height=600)
        viewport_frame = self.viewport.get_frame()
        viewport_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Create control panel
        self.control_panel = create_control_panel(self.root)
        control_frame = self.control_panel.get_frame()
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Create status bar
        self._create_status_bar()

        # Connect control panel buttons to actions
        self._connect_control_panel()

    def _create_status_bar(self):
        """Create the status bar"""
        if CTK_AVAILABLE:
            self.status_frame = ctk.CTkFrame(self.root, height=40)
            self.status_label = ctk.CTkLabel(self.status_frame, text="Ready",
                                           font=ctk.CTkFont(size=12))
        else:
            self.status_frame = tk.Frame(self.root, bg="lightblue", height=40)
            self.status_label = tk.Label(self.status_frame, text="Ready",
                                       font=("Arial", 10))

        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.status_label.pack(side="left", padx=10, pady=5)

    def _connect_control_panel(self):
        """Connect control panel buttons to their actions"""
        self.control_panel.set_button_command("start", self._on_start_detection)
        self.control_panel.set_button_command("stop", self._on_stop_detection)
        self.control_panel.set_button_command("calibrate", self._on_calibrate_camera)
        self.control_panel.set_button_command("config", self._on_configuration)
        self.control_panel.set_button_command("reset", self._on_reset_metrics)

    def _on_calibrate_camera(self):
        """Handle calibrate camera button"""
        logger.info("Camera calibration requested")
        # TODO: Implement camera calibration dialog
        self.status_label.configure(text="Camera calibration not implemented yet")

    def _on_reset_metrics(self):
        """Handle reset metrics button"""
        logger.info("Reset metrics requested")
        # Reset detection metrics
        metrics = {
            "total_detections": "0",
            "successful": "0",
            "failed": "0",
            "success_rate": "0%",
            "avg_confidence": "0.00",
            "last_detection": "Never"
        }
        self.control_panel.update_metrics(metrics)
        self.status_label.configure(text="Metrics reset")

    def _setup_event_handlers(self):
        """Setup event handlers"""
        # Subscribe to application events
        self.event_bus.subscribe(EventType.CONFIG_CHANGED, self._on_config_changed)
        self.event_bus.subscribe(EventType.MODE_CHANGED, self._on_mode_changed)
        self.event_bus.subscribe(EventType.DETECTION_RESULT, self._on_detection_result)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._on_error)

        # Keyboard shortcuts
        self.root.bind("<Key>", self._on_key_press)
        self.root.focus_set()  # Enable keyboard events

    def _on_key_press(self, event):
        """Handle keyboard shortcuts"""
        key = event.keysym.lower()

        if key == "space":
            # Toggle detection
            if self.controller.state.mode == AppMode.DETECTING:
                self._on_stop_detection()
            else:
                self._on_start_detection()

        elif key == "f11":
            # Toggle fullscreen
            current = self.root.attributes('-fullscreen')
            self.root.attributes('-fullscreen', not current)

        elif key == "s":
            # Save snapshot (placeholder)
            logger.info("Snapshot requested (not implemented)")

        elif key == "escape":
            # Exit fullscreen
            self.root.attributes('-fullscreen', False)

    def _on_start_detection(self):
        """Handle start detection button"""
        logger.info("Start detection requested")
        success = self.controller.start_detection()
        if success:
            self.status_label.configure(text="Detection started...")
        else:
            self.status_label.configure(text="Failed to start detection")

    def _on_stop_detection(self):
        """Handle stop detection button"""
        logger.info("Stop detection requested")
        self.controller.stop_detection()
        self.status_label.configure(text="Detection stopped")

    def _on_configuration(self):
        """Handle configuration button"""
        logger.info("Configuration requested")
        self._show_simple_config_dialog()

    def _show_simple_config_dialog(self):
        """Show simple configuration dialog"""
        if CTK_AVAILABLE:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Configuration")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()

            # Get current configuration
            config = self.controller.config

            # Show basic config info
            info_text = f"""AlignPress v2 Configuration

Version: {config.version}
Language: {config.system.language}
Theme: {config.system.theme}

Active Platen: {config.session.active_platen_id or 'None'}
Active Style: {config.session.active_style_id or 'None'}
Active Variant: {config.session.active_variant_id or 'None'}

Calibration: {'Available' if config.calibration else 'Not calibrated'}
"""

            text_label = ctk.CTkLabel(dialog, text=info_text, font=ctk.CTkFont(size=12),
                                    justify="left")
            text_label.pack(pady=20, padx=20)

            close_button = ctk.CTkButton(dialog, text="Close", command=dialog.destroy)
            close_button.pack(pady=10)

            # Center dialog
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

    def _on_config_changed(self, event):
        """Handle configuration changes"""
        logger.debug("Configuration changed, updating UI")
        self.update_display()

    def _on_mode_changed(self, event):
        """Handle mode changes"""
        mode_data = event.data
        logger.info(f"Mode changed: {mode_data.old_mode} -> {mode_data.new_mode}")

        # Update control panel with new state
        self.control_panel.update_from_state(self.controller.state)

        # Update status
        self.status_label.configure(text=f"Mode: {mode_data.new_mode.value}")

    def _on_detection_result(self, event):
        """Handle detection results"""
        result_data = event.data
        logger.debug(f"Detection result: {result_data['logo_id']} -> {result_data['success']}")

        # Update status with result
        status = "SUCCESS" if result_data['success'] else "FAILED"
        self.status_label.configure(text=f"Detection: {result_data['logo_id']} - {status}")

        # Update viewport with detection result if available
        if hasattr(result_data, 'detection_result'):
            detection_result = result_data['detection_result']
            self.viewport.set_detection_results([detection_result])

        # Update metrics in control panel
        self._update_detection_metrics(result_data)

    def _on_error(self, event):
        """Handle application errors"""
        error_data = event.data
        logger.error(f"Application error: {error_data['message']}")

        # Update status with error
        self.status_label.configure(text=f"Error: {error_data['message']}")

    def _update_detection_metrics(self, result_data):
        """Update detection metrics in control panel"""
        # This would be connected to a metrics service in a full implementation
        # For now, just show the latest result
        try:
            metrics = {
                "last_detection": "Just now",
                "total_detections": str(getattr(self, '_total_detections', 0) + 1)
            }

            if result_data['success']:
                self._successful_detections = getattr(self, '_successful_detections', 0) + 1
                metrics["successful"] = str(self._successful_detections)
            else:
                self._failed_detections = getattr(self, '_failed_detections', 0) + 1
                metrics["failed"] = str(self._failed_detections)

            # Calculate success rate
            total = self._successful_detections + self._failed_detections
            if total > 0:
                success_rate = (self._successful_detections / total) * 100
                metrics["success_rate"] = f"{success_rate:.1f}%"

            self.control_panel.update_metrics(metrics)
            self._total_detections = getattr(self, '_total_detections', 0) + 1

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def update_display(self):
        """Update the display with current state"""
        try:
            # Update control panel with current state and config
            self.control_panel.update_from_state(self.controller.state)
            self.control_panel.update_from_config(self.controller.config)

            # Update viewport with current target logos if available
            if self.controller.config and self.controller.config.get_active_style():
                style = self.controller.config.get_active_style()
                self.viewport.set_target_logos(style.logos)

            # Update status with current state
            mode = self.controller.state.mode.value
            ready = self.controller.state.is_ready_for_detection
            self.status_label.configure(text=f"Mode: {mode}, Ready: {ready}")

        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def _on_closing(self):
        """Handle window closing"""
        logger.info("Application closing...")
        try:
            self.controller.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            self.root.destroy()

    def run(self):
        """Start the UI event loop"""
        logger.info("Starting UI event loop")

        # Perform initial update
        self.root.after(100, self.update_display)

        # Start the main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self._on_closing()
        except Exception as e:
            logger.error(f"UI error: {e}")
            raise


def create_main_window(controller: AppController) -> MainWindow:
    """Create and return the main window"""
    return MainWindow(controller)