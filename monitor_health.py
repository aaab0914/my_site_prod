"""
Health monitoring script for Django application.

This script performs periodic HTTP health checks on critical application
endpoints and logs the results to a timestamped log file. It is designed
to be executed from a cron job or container health check system.

Exit codes:
    0: All health checks passed successfully.
    1: One or more health checks failed (server error or network issue).
"""

# ============================================================================
# IMPORTS
# ============================================================================

from pathlib import Path
# Path: Object-oriented filesystem path abstraction.
# Used to construct log file paths in a cross-platform manner.
# Provides .parent, .mkdir(), and path joining via the / operator.

from datetime import datetime
# datetime: Provides date and time handling.
# Used to generate year-month directory names for log rotation.
# Example: datetime.now().strftime("%Y-%m") returns "2026-07".

import sys
# sys: System-specific parameters and functions.
# Used to read command-line arguments (sys.argv) and exit with status codes.

from urllib.error import HTTPError, URLError
# HTTPError: Raised when the HTTP server returns an error status (4xx or 5xx).
# URLError: Raised for network-level issues (DNS failure, connection refused).
# Both are subclasses of OSError and are caught to handle failures gracefully.

from urllib.request import Request, urlopen
# Request: Represents an HTTP request, allowing custom headers like User-Agent.
# urlopen: Performs the actual network request and returns an HTTPResponse object.
# Supports timeout parameter to prevent infinite hanging.

# ============================================================================
# GLOBAL PATH CONFIGURATION
# ============================================================================

# PROJECT_ROOT: Absolute path to the project root directory.
# __file__ is the script's own path; .resolve() resolves symlinks; .parent goes up one level.
# Assumes this script is located at the project root.
PROJECT_ROOT = Path(__file__).resolve().parent

# MONTH_DIR: Log directory grouped by year and month (e.g., "logs/2026-07").
# This structure enables easy log rotation and archival by month.
MONTH_DIR = PROJECT_ROOT / "logs" / datetime.now().strftime("%Y-%m")

# Create the monthly log directory if it does not already exist.
# parents=True creates all intermediate directories (e.g., "logs/", "logs/2026-07/").
# exist_ok=True suppresses errors if the directory already exists.
MONTH_DIR.mkdir(parents=True, exist_ok=True)

# MONITOR_LOG: Full filesystem path to the health check log file.
# All health check results are appended to this file.
MONITOR_LOG = MONTH_DIR / "monitor-health.log"

# ============================================================================
# LOGGING FUNCTION
# ============================================================================

def log(message: str) -> None:
    """
    Write a log message to both stdout and the health check log file.

    Dual-writes ensure that:
        - The log file retains persistent history for auditing.
        - stdout provides real-time visibility in cron job outputs.

    Args:
        message: The log message string to write. Timestamps are not added
                 here; they are assumed to be handled by the execution context
                 (e.g., cron adds its own timestamps).

    Returns:
        None
    """
    # Open the log file in append mode ("a").
    # This prevents overwriting previous logs and avoids race conditions
    # by opening and closing the file on each write.
    with MONITOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{message}\n")
    # Also write to stdout so that cron or container logs capture the output.
    print(message)


# ============================================================================
# HEALTH CHECK FUNCTION
# ============================================================================

def check_url(url: str, name: str) -> bool:
    """
    Perform an HTTP health check on a given URL and log the result.

    This function sends a GET request with a custom User-Agent and evaluates
    the response. It distinguishes between:
        - Server errors (HTTP 5xx) → failure
        - Client errors (HTTP 4xx) → success (service is reachable)
        - Network errors (timeout, DNS failure) → failure

    Args:
        url: The complete URL to check (e.g., "http://localhost:8000/blog/").
        name: A short identifier for the target service used in logs
              (e.g., "blog_home", "login_page").

    Returns:
        True if the service responds without server-side errors.
        False if a 5xx error occurs or the request times out/fails.
    """
    try:
        # Build an HTTP request with a custom User-Agent header.
        # Some services may block default Python user agents, so this ensures
        # our monitoring requests are identified clearly.
        request = Request(url, headers={"User-Agent": "my-site-monitor/1.0"})

        # Execute the request with a 10-second timeout.
        # The timeout applies to both connection establishment and data reading.
        # If the server does not respond within this window, URLError is raised.
        response = urlopen(request, timeout=10)

        # Check if the status code is a server error (500-599).
        # These indicate application-level failures that require intervention.
        if response.status >= 500:
            log(f"ALERT {name} returned server error {response.status}: {url}")
            return False

        # All other status codes (2xx, 3xx, 4xx) are acceptable because they
        # demonstrate that the service is running and reachable.
        log(f"OK {name} returned {response.status}: {url}")
        return True

    except HTTPError as exc:
        # HTTPError is raised for HTTP status codes 400 and above.
        # 4xx errors (e.g., 401 Unauthorized, 404 Not Found) are considered
        # "successful" from a health-check perspective because they prove
        # the application is running and handling requests.
        if exc.code >= 500:
            log(f"ALERT {name} returned server error {exc.code}: {url}")
            return False
        # 4xx errors are logged as OK.
        log(f"OK {name} returned {exc.code}: {url}")
        return True

    except URLError as exc:
        # URLError captures network-level issues such as:
        #   - Connection refused (server not listening)
        #   - DNS resolution failure (hostname unknown)
        #   - Connection timeout (server unreachable)
        # Any of these indicates the service is unavailable.
        log(f"ALERT {name} probe failed: {url} ({exc})")
        return False


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main() -> int:
    """
    Main entry point for the health check script.

    This function:
        1. Reads the base URL from the command line (or uses a default).
        2. Builds a list of endpoint URLs to check.
        3. Executes all health checks.
        4. Returns a unified exit code.

    Command line usage:
        python monitor_health.py [base_url]

    If base_url is omitted, defaults to "http://127.0.0.1:8000".

    Returns:
        0: All health checks passed.
        1: One or more health checks failed.
    """
    # Parse base URL from command-line arguments.
    # sys.argv[0] is the script name, sys.argv[1] is the first argument.
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

    # Define the list of endpoints to check.
    # Each tuple contains:
    #   - The full URL (constructed from base_url + endpoint path)
    #   - A human-readable name for logging purposes
    checks = [
        (f"{base_url}/blog/", "blog_home"),          # Blog homepage
        (f"{base_url}/users/login/", "login_page"),  # User authentication page
        # Add more endpoints here as needed:
        # (f"{base_url}/api/health/", "api_health"),
        # (f"{base_url}/admin/", "admin_page"),
    ]

    # Run all checks and evaluate the aggregate result.
    # all() returns True only if every check returned True.
    ok = all(check_url(url, name) for url, name in checks)

    # Return 0 for success, 1 for failure.
    # This exit code can be consumed by cron, systemd, or container orchestrators.
    return 0 if ok else 1


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # raise SystemExit() is the preferred way to exit with a status code.
    # It avoids the need to import sys.exit() and works consistently in all
    # Python versions (including when running under PyPy or embedded interpreters).
    raise SystemExit(main())

# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                      monitor_health.py - Code Structure Diagram                    │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  1. MODULE DOCSTRING                                                                │
# │     └── Purpose, exit codes, execution context                                      │
# │                                                                                     │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 2. IMPORT SECTION                                                             │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  pathlib.Path          → Cross-platform path operations                       │  │
# │  │  datetime.datetime     → Date/time manipulation for log rotation              │  │
# │  │  sys                   → Command-line args and exit codes                     │  │
# │  │  urllib.error          → HTTPError (HTTP status errors)                       │  │
# │  │  urllib.error          → URLError (network-level errors)                     │  │
# │  │  urllib.request        → Request (HTTP request builder)                       │  │
# │  │  urllib.request        → urlopen (HTTP client)                               │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                        │                                             │
# │                                        ▼                                             │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 3. GLOBAL PATH CONFIGURATION                                                   │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  PROJECT_ROOT = Path(__file__).resolve().parent                               │  │
# │  │       │                                                                        │  │
# │  │       ▼                                                                        │  │
# │  │  MONTH_DIR = PROJECT_ROOT / "logs" / datetime.now().strftime("%Y-%m")         │  │
# │  │       │                                                                        │  │
# │  │       ▼                                                                        │  │
# │  │  MONITOR_LOG = MONTH_DIR / "monitor-health.log"                               │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                        │                                             │
# │                                        ▼                                             │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 4. FUNCTION: log(message: str) -> None                                        │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  Purpose: Write to both log file and stdout                                   │  │
# │  │  Input:   message string                                                      │  │
# │  │  Output:  None (side-effect only)                                             │  │
# │  │  Behavior:                                                                     │  │
# │  │    ┌──────────────────────────────────────────────────────────────────────┐   │  │
# │  │    │  MONITOR_LOG.open("a")  → append to file                            │   │  │
# │  │    │  print(message)          → output to stdout                         │   │  │
# │  │    └──────────────────────────────────────────────────────────────────────┘   │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                        │                                             │
# │                                        ▼                                             │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 5. FUNCTION: check_url(url: str, name: str) -> bool                           │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  Purpose: Perform single HTTP health check                                    │  │
# │  │  Inputs:  url (full endpoint), name (log identifier)                          │  │
# │  │  Output:  True = healthy, False = unhealthy                                  │  │
# │  │                                                                              │  │
# │  │  ┌────────────────────────────────────────────────────────────────────────┐  │  │
# │  │  │  try:                                                                  │  │  │
# │  │  │    Request(url, headers={"User-Agent": ...})                         │  │  │
# │  │  │    urlopen(request, timeout=10)  ← Network call                       │  │  │
# │  │  │      │                                                                 │  │  │
# │  │  │      ├── response.status >= 500  → ALERT, return False                │  │  │
# │  │  │      └── response.status < 500   → OK, return True                    │  │  │
# │  │  │  except HTTPError as exc:                                              │  │  │
# │  │  │    ├── exc.code >= 500  → ALERT, return False                         │  │  │
# │  │  │    └── exc.code < 500   → OK, return True (4xx is acceptable)         │  │  │
# │  │  │  except URLError as exc:                                               │  │  │
# │  │  │    └── ALERT, return False (network down)                             │  │  │
# │  │  └────────────────────────────────────────────────────────────────────────┘  │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                        │                                             │
# │                                        ▼                                             │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 6. FUNCTION: main() -> int                                                    │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  Purpose: Script entry point, orchestrates all checks                         │  │
# │  │  Input:  sys.argv[1] (optional base URL)                                      │  │
# │  │  Output: 0 (all OK) or 1 (failure)                                            │  │
# │  │                                                                              │  │
# │  │  ┌────────────────────────────────────────────────────────────────────────┐  │  │
# │  │  │  base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000" │  │  │
# │  │  │  checks = [(base_url + "/blog/", "blog_home"), ...]                    │  │  │
# │  │  │  ok = all(check_url(url, name) for url, name in checks)                │  │  │
# │  │  │  return 0 if ok else 1                                                 │  │  │
# │  │  └────────────────────────────────────────────────────────────────────────┘  │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                        │                                             │
# │                                        ▼                                             │
# │  ┌────────────────────────────────────────────────────────────────────────────────┐  │
# │  │ 7. SCRIPT ENTRY POINT                                                         │  │
# │  ├────────────────────────────────────────────────────────────────────────────────┤  │
# │  │  if __name__ == "__main__":                                                   │  │
# │  │      raise SystemExit(main())                                                │  │
# │  └────────────────────────────────────────────────────────────────────────────────┘  │
# │                                                                                     │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#
#
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                           DATA FLOW DIAGRAM                                        │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌─────────────┐                                                                   │
# │  │  Command    │                                                                   │
# │  │  Line Args  │ ──────────────────────────────────────────────┐                  │
# │  │  (sys.argv) │                                               │                  │
# │  └─────────────┘                                               │                  │
# │                                │                                │                  │
# │                                ▼                                ▼                  │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐  │
# │  │                         main()                                              │  │
# │  │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
# │  │  │  base_url = args[1] or "http://127.0.0.1:8000"                    │   │  │
# │  │  │  checks = [                                                       │   │  │
# │  │  │    (base_url + "/blog/", "blog_home"),                            │   │  │
# │  │  │    (base_url + "/users/login/", "login_page")                     │   │  │
# │  │  │  ]                                                               │   │  │
# │  │  └─────────────────────────────────────────────────────────────────────┘   │  │
# │  └─────────────────────────────────────────────────────────────────────────────┘  │
# │                                │                                                   │
# │                                ▼                                                   │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐  │
# │  │                    check_url() called for each endpoint                     │  │
# │  │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
# │  │  │  HTTP GET → URL (timeout=10s)                                      │   │  │
# │  │  │      │                                                             │   │  │
# │  │  │      ├── 2xx/3xx/4xx  → log("OK")     → True                      │   │  │
# │  │  │      ├── 5xx          → log("ALERT")  → False                     │   │  │
# │  │  │      └── Network fail → log("ALERT")  → False                     │   │  │
# │  │  └─────────────────────────────────────────────────────────────────────┘   │  │
# │  └─────────────────────────────────────────────────────────────────────────────┘  │
# │                                │                                                   │
# │                                ▼                                                   │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐  │
# │  │                         log(message)                                        │  │
# │  │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
# │  │  │  ┌───────────────────┐    ┌───────────────────┐                    │   │  │
# │  │  │  │  MONITOR_LOG      │    │  stdout           │                    │   │  │
# │  │  │  │  (append mode)    │    │  (console output) │                    │   │  │
# │  │  │  └───────────────────┘    └───────────────────┘                    │   │  │
# │  │  └─────────────────────────────────────────────────────────────────────┘   │  │
# │  └─────────────────────────────────────────────────────────────────────────────┘  │
# │                                │                                                   │
# │                                ▼                                                   │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐  │
# │  │                        Exit Code                                           │  │
# │  │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
# │  │  │  0 = All checks passed                                              │   │  │
# │  │  │  1 = One or more checks failed                                     │   │  │
# │  │  └─────────────────────────────────────────────────────────────────────┘   │  │
# │  └─────────────────────────────────────────────────────────────────────────────┘  │
# │                                                                                     │
# └─────────────────────────────────────────────────────────────────────────────────────┘