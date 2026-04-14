import sys
import traceback

def report_error(e: Exception):
    """
    Centralized error reporting function.
    All code paths that handle unexpected errors MUST funnel through this function.
    """
    # For now, just print the exception to stderr. In a more complete project,
    # this might report to Sentry, DataDog, etc.
    print(f"Error captured: {e}", file=sys.stderr)
    traceback.print_exc()
