#!/usr/bin/env python3
"""
Command-line interface for OCCAM Flask server.
"""

import sys
import argparse


def main():
    """Main entry point for occam-server command."""
    parser = argparse.ArgumentParser(
        description='OCCAM Flask Web Server - Reconstructability Analysis Interface'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port to run the server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1, use 0.0.0.0 for all interfaces)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    args = parser.parse_args()

    # Import app here to avoid loading Flask unless running
    from occam_server.app import app

    print(f"Starting OCCAM Flask server on {args.host}:{args.port}")
    if args.debug:
        print("Debug mode: ON")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
