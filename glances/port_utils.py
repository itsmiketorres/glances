#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Port utility functions for Glances web server."""

import socket

# Maximum number of ports to try when finding an available port
DEFAULT_PORT_MAX_ATTEMPTS = 20
# Maximum valid TCP port number
MAX_PORT_NUMBER = 65535


def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding.

    Args:
        host: The host address to check
        port: The port number to check

    Returns:
        True if the port is available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_available_port(host: str, start_port: int, max_attempts: int = DEFAULT_PORT_MAX_ATTEMPTS) -> int | None:
    """Find an available port starting from start_port.

    Args:
        host: The host address to bind to
        start_port: The initial port to try
        max_attempts: Maximum number of ports to try (default DEFAULT_PORT_MAX_ATTEMPTS)

    Returns:
        An available port number, or None if no port is available within the range
    """
    for offset in range(max_attempts):
        port = start_port + offset
        # Avoid going beyond valid port range
        if port > MAX_PORT_NUMBER:
            break
        if is_port_available(host, port):
            return port
    return None
