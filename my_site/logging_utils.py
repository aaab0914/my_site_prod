"""
Custom logging handlers for the blog application.

This module extends Django's logging system with a custom handler that
automatically organizes log files into monthly directories and daily files.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

from datetime import datetime
# datetime: Provides date and time utilities, used for generating log file names.

from logging import FileHandler
# FileHandler: Standard Python logging handler that writes log messages to a file.

from pathlib import Path
# Path: Object-oriented filesystem path handling.


# =============================================================================
# CUSTOM LOG HANDLER
# =============================================================================

class DailyMonthlyFileHandler(FileHandler):
    """
    Write logs into logs/YYYY-MM/prefix-YYYY-MM-DD.log.

    The target file is recalculated on each emit so long-running processes
    switch automatically when the day or month changes.
    """

    def __init__(self, log_dir, filename_prefix, mode="a", encoding=None, delay=False):
        """
        Initialize the handler with the log directory and filename prefix.

        Args:
            log_dir: Base directory where log files will be stored.
            filename_prefix: Prefix for the log filename (e.g., 'django').
            mode: File open mode (default: 'a' for append).
            encoding: File encoding (e.g., 'utf-8').
            delay: If True, delays file opening until first log emission.
        """
        self.log_dir = Path(log_dir)
        # log_dir: Converted to a Path object for consistent path operations.

        self.filename_prefix = filename_prefix
        # filename_prefix: Used to construct the full log filename.

        self._current_path = None
        # _current_path: Caches the currently active log file path.

        self.log_dir.mkdir(parents=True, exist_ok=True)
        # Ensure the base log directory exists before creating files.

        # Initialize the parent FileHandler with the first log file path.
        super().__init__(self._build_path(), mode=mode, encoding=encoding, delay=delay)

    def _build_path(self):
        """
        Construct the full log file path based on the current date.

        Returns:
            Path: The full path to the log file for the current day.
        """
        now = datetime.now()
        # Get the current date and time.

        month_dir = self.log_dir / now.strftime("%Y-%m")
        # Create a monthly subdirectory (e.g., logs/2026-07/).

        month_dir.mkdir(parents=True, exist_ok=True)
        # Ensure the monthly directory exists.

        # Return the full path: logs/2026-07/django-2026-07-07.log
        return month_dir / f"{self.filename_prefix}-{now.strftime('%Y-%m-%d')}.log"

    def _refresh_stream_if_needed(self):
        """
        Check if the log file should change (new day or month) and update the stream.
        """
        target_path = self._build_path()
        # Calculate the current expected log file path.

        if self._current_path == target_path:
            return
        # If the path hasn't changed, no action needed.

        self.acquire()
        # Acquire the thread lock to ensure thread-safe file switching.

        try:
            if self.stream:
                self.stream.close()
                self.stream = None
            # Close the existing file stream if it's open.

            self.baseFilename = str(target_path)
            # Update the baseFilename to the new target path.

            self._current_path = target_path
            # Cache the new path for future comparisons.

            if not self.delay:
                self.stream = self._open()
            # Reopen the file stream if delay is disabled.

        finally:
            self.release()
        # Release the thread lock.

    def emit(self, record):
        """
        Log a record, automatically switching to a new log file if the date has changed.

        Args:
            record: The log record to be emitted.
        """
        self._refresh_stream_if_needed()
        # Ensure we're writing to the correct log file for the current date.

        super().emit(record)
        # Delegate to the parent FileHandler to write the record.

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                       my_site/logging_utils.py                             │
# │                   (Custom Logging Handler)                                 │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  datetime                   │  logging                   │  pathlib        │
# │  └─ datetime                │  └─ FileHandler            │  └─ Path        │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                      DailyMonthlyFileHandler (Class)                        │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  Inherits: FileHandler                                                       │
# │                                                                             │
# │  Attributes:                                                                │
# │    - log_dir: Base directory for all log files                             │
# │    - filename_prefix: Prefix used in log filenames                         │
# │    - _current_path: Cached path to the current active log file             │
# │                                                                             │
# │  Constructor:                                                              │
# │    - Creates the base log directory if it doesn't exist.                    │
# │    - Initializes the parent FileHandler with the first log file path.      │
# │                                                                             │
# │  Custom Methods:                                                            │
# │    1. _build_path(): Constructs the daily log file path.                    │
# │       - Creates YYYY-MM monthly subdirectory.                              │
# │       - Returns: logs/YYYY-MM/prefix-YYYY-MM-DD.log                        │
# │                                                                             │
# │    2. _refresh_stream_if_needed(): Compares cached path with current date.  │
# │       - If different, closes old stream and opens new file.                │
# │       - Thread-safe using acquire()/release().                             │
# │                                                                             │
# │    3. emit(record): Overrides FileHandler.emit().                          │
# │       - Calls _refresh_stream_if_needed() before writing.                   │
# │       - Ensures logs always go to the correct daily file.                   │
# │                                                                             │
# │  Purpose:                                                                   │
# │    - Automatically organize log files by month and day.                     │
# │    - Prevent log files from growing indefinitely.                           │
# │    - Support long-running processes with seamless date switching.           │
# └─────────────────────────────────────────────────────────────────────────────┘