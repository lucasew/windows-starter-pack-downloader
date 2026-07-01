import sys
import traceback

def report_error(e: Exception):
    """
    Centralized error reporting function.
    In a real system, this could connect to Sentry or another error tracking service.
    """
    print(f"ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
