import argparse
import logging
import os

# Import the Flask app factory
from .app import create_app


def configure_logging(verbose: bool = False) -> None:
    """Configure logging.

    - Suppress Flask/Werkzeug development server noise.
    - By default, run quietly (no access logs or app logs).
    - With --verbose, show access logs and directory statistics.
    """
    root_level = logging.WARNING  # Always quiet at root level
    logging.basicConfig(level=root_level, format="%(message)s")

    # Silence general server chatter
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)
    logging.getLogger("waitress").setLevel(logging.WARNING)

    if verbose:
        # Verbose mode: show access logs and app logs
        logging.getLogger("waitress.access").setLevel(logging.INFO)
        logging.getLogger("imgserve").setLevel(logging.INFO)
    else:
        # Quiet mode (default): disable access logs and app logs
        logging.getLogger("waitress.access").setLevel(logging.WARNING)
        logging.getLogger("imgserve").setLevel(logging.WARNING)


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
        help="Show directory statistics and image counts in logs",
    )
    parser.add_argument(
        "--index-file",
        help="Path to JSON index file to serve from (instead of CWD). Use 'generate_index.py' to create one.",
    )

    args = parser.parse_args()

    # Create the app with the specified mode
    application = create_app(index_file=args.index_file)

    configure_logging(verbose=args.verbose)

    print(f"Server running at http://{args.host}:{args.port}")
    # Serve the WSGI application using Waitress (production-ready WSGI server)
    try:
        from waitress import serve
        serve(
            application,
            host=args.host,
            port=args.port,
            threads=args.threads,
            ident="imgserve",
        )
    except Exception as e:
        print(f"Error: Failed to start server with Waitress: {e}")
        print("Ensure Waitress is installed: pip install waitress")
        return


if __name__ == "__main__":
    main()
