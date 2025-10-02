import argparse
import logging
import os

# Import the Flask app factory
from .app import create_app


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
