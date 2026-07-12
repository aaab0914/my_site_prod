"""
Custom logging handlers for the blog application.

This module extends Django's logging system with a custom handler that
automatically organizes log files into monthly directories and daily files.
"""

from datetime import datetime
from logging import FileHandler
from pathlib import Path
import re


NOISY_404_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^/metrics$",
        r"^/robots\.txt$",
        r"^/\.env$",
        r"^/\.git(?:/|$)",
        r"^/\.idea(?:/|$)",
        r"^/\.vscode(?:/|$)",
        r"^/\.ftpconfig$",
        r"^/\.remote-sync\.json$",
        r"^/\+CSCOE\+(?:/|$)",
        r"^/\+CSCOT\+(?:/|$)",
        r"^/AHT(?:/|$)",
        r"^/CACHE(?:/|$)",
        r"^/EndUserPortal\.jsp$",
        r"^/Guest\.aspx$",
        r"^/Login(?:\.jsp|/Login)?$",
        r"^/Orion/Login\.aspx$",
        r"^/RASHTML5Gateway(?:/|$)",
        r"^/WebInterface/login\.html$",
        r"^/_layouts/15/error\.aspx$",
        r"^/admin(?:_login\.html)?$",
        r"^/api/v2/cmdb/system/admin(?:/admin)?$",
        r"^/appliance$",
        r"^/auth(?:\.html|/admin(?:/master/console/)?)?$",
        r"^/authorization\.do$",
        r"^/cgi-bin/welcome$",
        r"^/cgi-mod/index\.cgi$",
        r"^/client$",
        r"^/configurations(?:\.do)?$",
        r"^/dana-na(?:/|$)",
        r"^/deployment-config\.json$",
        r"^/fpui/jsp/login\.jsp$",
        r"^/global-protect/login\.esp$",
        r"^/wsman$",
    )
]


class SkipNoisy404Filter:
    def filter(self, record):
        message = record.getMessage()
        if 'Not Found:' not in message:
            return True
        path = message.split('Not Found:', 1)[1].strip()
        return not any(pattern.match(path) for pattern in NOISY_404_PATTERNS)


class DailyMonthlyFileHandler(FileHandler):
    """
    Write logs into logs/YYYY-MM/prefix-YYYY-MM-DD.log.

    The target file is recalculated on each emit so long-running processes
    switch automatically when the day or month changes.
    """

    def __init__(self, log_dir, filename_prefix, mode="a", encoding=None, delay=False):
        self.log_dir = Path(log_dir)
        self.filename_prefix = filename_prefix
        self._current_path = None
        self.log_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(self._build_path(), mode=mode, encoding=encoding, delay=delay)

    def _build_path(self):
        now = datetime.now()
        month_dir = self.log_dir / now.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir / f"{self.filename_prefix}-{now.strftime('%Y-%m-%d')}.log"

    def _refresh_stream_if_needed(self):
        target_path = self._build_path()
        if self._current_path == target_path:
            return
        self.acquire()
        try:
            if self.stream:
                self.stream.close()
                self.stream = None
            self.baseFilename = str(target_path)
            self._current_path = target_path
            if not self.delay:
                self.stream = self._open()
        finally:
            self.release()

    def emit(self, record):
        self._refresh_stream_if_needed()
        super().emit(record)
