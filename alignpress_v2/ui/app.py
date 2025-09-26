"""
Application Launcher for AlignPress v2 UI

Orchestrates the UI components and connects to the controller
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from ..controller.app_controller import AppController
from .main_window import create_main_window

logger = logging.getLogger(__name__)


class AlignPressApp:
    """Main application class that manages UI lifecycle"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.controller: Optional[AppController] = None
        self.main_window = None

        logger.info("AlignPressApp initialized")

    def initialize(self) -> bool:
        """Initialize the application"""
        try:
            # Create controller
            logger.info("Creating application controller...")
            self.controller = AppController(self.config_path)

            # Create main window
            logger.info("Creating main window...")
            self.main_window = create_main_window(self.controller)

            logger.info("Application initialization complete")
            return True

        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            return False

    def run(self) -> None:
        """Run the application"""
        if not self.main_window:
            logger.error("Application not properly initialized")
            return

        try:
            logger.info("Starting AlignPress v2 UI...")
            self.main_window.run()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Clean shutdown of the application"""
        logger.info("Shutting down AlignPress v2...")

        try:
            if self.controller:
                self.controller.shutdown()
        except Exception as e:
            logger.error(f"Error during controller shutdown: {e}")

        logger.info("Application shutdown complete")


def main(config_path: Optional[str] = None) -> None:
    """Main entry point for the AlignPress v2 UI application"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('alignpress_v2.log')
        ]
    )

    logger.info("=" * 50)
    logger.info("AlignPress v2 - Visual Logo Detection System")
    logger.info("=" * 50)

    # Convert config path to Path object if provided
    config_path_obj = Path(config_path) if config_path else None

    # Create and run application
    app = AlignPressApp(config_path_obj)

    if not app.initialize():
        logger.error("Failed to initialize application")
        sys.exit(1)

    try:
        app.run()
    except Exception as e:
        logger.error(f"Unhandled application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AlignPress v2 - Visual Logo Detection System"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (optional)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    main(args.config)