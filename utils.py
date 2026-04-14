import sys
import traceback


def report_error(e: Exception):
    """
    Centralized error reporting function.
    In a real project, this might log to Sentry or another error tracking service.
    """
    print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
