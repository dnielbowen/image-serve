import argparse
import logging
import os
from waitress import serve

# Import the Flask app (ROOT_DIR is captured from current working directory at import time)
from .app import app as application


def configure_logging(verbose: bool = False) -> None:
    """Configure logging to show only access logs from the WSGI server.

    - Suppress Flask/Werkzeug development server noise.
    - Keep Waitress access logs at INFO level.
    """
    root_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=root_level, format="%(message)s")

    # Silence general server chatter; keep only access logs visible
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)
    logging.getLogger("waitress").setLevel(logging.WARNING)
    logging.getLogger("waitress.access").setLevel(logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve images in the current working directory as a simple gallery."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("IMGSERVE_HOST", "0.0.0.0"),
        help="Host/IP to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("IMGSERVE_PORT", 8000)),
        help="Port to bind (default: 8000)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=int(os.environ.get("IMGSERVE_THREADS", 8)),
        help="Number of worker threads (default: 8)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose server logs (still hides dev server banners)",
    )

    args = parser.parse_args()

    configure_logging(verbose=args.verbose)

    # Serve the WSGI application using Waitress (production-ready WSGI server)
    serve(
        application,
        host=args.host,
        port=args.port,
        threads=args.threads,
        ident="imgserve",
    )


if __name__ == "__main__":
    main()
