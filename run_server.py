"""WebSocket Server Launcher Script for Kung Fu Chess.

This executable script configures application logging, instantiates the WebSocket server,
registers operating system signal handlers (for SIGINT / SIGTERM), and runs the async
event loop until a shutdown signal is received.
"""

import asyncio
import logging
import signal
import sys

from logger_config import setup_logging
from server.config import DEFAULT_HOST, DEFAULT_PORT
from server.ws_server import WebSocketServer

logger = logging.getLogger(__name__)


async def main() -> None:
    """Async main entry point for running the WebSocket server.

    Sets up logging, instantiates the server, configures termination signal listeners,
    and handles graceful shutdown on user interruption (KeyboardInterrupt / SIGINT / SIGTERM).
    """
    setup_logging()
    server = WebSocketServer(host=DEFAULT_HOST, port=DEFAULT_PORT)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _on_signal() -> None:
        """Signal handler callback to trigger server shutdown event."""
        logger.info("Termination signal received.")
        stop_event.set()

    # Register OS signal handlers where supported by event loop implementation
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            # Signal handlers not implemented on Windows SelectorEventLoop for all signals
            pass

    await server.start()
    print(f"Kung Fu Chess WebSocket Server running at ws://{DEFAULT_HOST}:{DEFAULT_PORT}")
    print("Press Ctrl+C to stop.")

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Keyboard interrupt received.")
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down cleanly.")
        sys.exit(0)
