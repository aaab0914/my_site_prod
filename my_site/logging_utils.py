from datetime import datetime
from logging import FileHandler
from pathlib import Path


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
