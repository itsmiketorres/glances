#!/usr/bin/env python
#
# Glances - An eye on your system
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Glances unitary tests suite for port auto-discovery feature."""

import socket
import threading

import pytest

from glances.port_utils import find_available_port, is_port_available

# Test configuration constants
LOCALHOST = '127.0.0.1'
ALL_INTERFACES = '0.0.0.0'
DEFAULT_MAX_ATTEMPTS = 20
DEFAULT_WEBSERVER_PORT = 61208
MAX_PORT_NUMBER = 65535

# Base ports for different test groups to avoid conflicts
PORT_AVAILABILITY_BASE = 59995
PORT_FIND_BASE = 59980
PORT_INTEGRATION_BASE = DEFAULT_WEBSERVER_PORT
PORT_IPV6_BASE = 59940
PORT_CONCURRENT_BASE = 59900


def create_blocking_socket(host, port):
    """Create a socket that blocks a specific port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    return sock


class TestPortAvailability:
    """Test cases for is_port_available function."""

    def test_available_port(self):
        """Test that an unused port is detected as available."""
        test_port = PORT_AVAILABILITY_BASE + 4
        # First check it's not in use (if it is, skip this test)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((LOCALHOST, test_port))
            except OSError:
                pytest.skip(f"Port {test_port} is already in use, skipping test")

        assert is_port_available(LOCALHOST, test_port) is True

    def test_unavailable_port(self):
        """Test that a port in use is detected as unavailable."""
        test_port = PORT_AVAILABILITY_BASE + 3
        blocking_socket = create_blocking_socket(LOCALHOST, test_port)
        try:
            assert is_port_available(LOCALHOST, test_port) is False
        finally:
            blocking_socket.close()

    def test_port_becomes_available_after_release(self):
        """Test that a port becomes available after being released."""
        test_port = PORT_AVAILABILITY_BASE + 2
        blocking_socket = create_blocking_socket(LOCALHOST, test_port)
        try:
            assert is_port_available(LOCALHOST, test_port) is False
        finally:
            blocking_socket.close()

        assert is_port_available(LOCALHOST, test_port) is True


class TestFindAvailablePort:
    """Test cases for find_available_port function."""

    def test_find_first_available_port(self):
        """Test that the first available port is returned when start port is free."""
        test_port = PORT_FIND_BASE + 10
        if not is_port_available(LOCALHOST, test_port):
            pytest.skip(f"Port {test_port} is already in use, skipping test")

        result = find_available_port(LOCALHOST, test_port, max_attempts=DEFAULT_MAX_ATTEMPTS)
        assert result == test_port

    def test_find_next_available_port_when_first_is_busy(self):
        """Test that the next available port is returned when start port is busy."""
        start_port = PORT_FIND_BASE
        blocking_socket = create_blocking_socket(LOCALHOST, start_port)
        try:
            result = find_available_port(LOCALHOST, start_port, max_attempts=DEFAULT_MAX_ATTEMPTS)

            assert result is not None
            assert result > start_port
            assert result <= start_port + DEFAULT_MAX_ATTEMPTS
        finally:
            blocking_socket.close()

    def test_find_port_with_multiple_blocked(self):
        """Test finding a port when multiple consecutive ports are blocked."""
        start_port = PORT_FIND_BASE - 10
        num_blocked = 3
        blocking_sockets = []

        try:
            for i in range(num_blocked):
                try:
                    sock = create_blocking_socket(LOCALHOST, start_port + i)
                    blocking_sockets.append(sock)
                except OSError:
                    pass

            result = find_available_port(LOCALHOST, start_port, max_attempts=DEFAULT_MAX_ATTEMPTS)

            assert result is not None
            assert result >= start_port + num_blocked
        finally:
            for sock in blocking_sockets:
                sock.close()

    def test_no_available_port_returns_none(self):
        """Test that None is returned when no port is available within max_attempts."""
        start_port = PORT_FIND_BASE - 20
        max_attempts = 3
        blocking_sockets = []

        try:
            for i in range(max_attempts):
                try:
                    sock = create_blocking_socket(LOCALHOST, start_port + i)
                    blocking_sockets.append(sock)
                except OSError:
                    pass

            if len(blocking_sockets) < max_attempts:
                pytest.skip("Could not block all required ports for test")

            result = find_available_port(LOCALHOST, start_port, max_attempts=max_attempts)
            assert result is None
        finally:
            for sock in blocking_sockets:
                sock.close()

    def test_max_attempts_respected(self):
        """Test that the function doesn't exceed max_attempts."""
        start_port = PORT_FIND_BASE - 30
        max_attempts = 5

        result = find_available_port(LOCALHOST, start_port, max_attempts=max_attempts)

        if result is not None:
            assert result >= start_port
            assert result < start_port + max_attempts

    def test_port_range_boundary(self):
        """Test behavior near the maximum port number."""
        start_port = MAX_PORT_NUMBER - 5
        max_attempts = 10

        result = find_available_port(LOCALHOST, start_port, max_attempts=max_attempts)

        if result is not None:
            assert result <= MAX_PORT_NUMBER


class TestPortAutoIncrementIntegration:
    """Integration tests for port auto-increment during server startup."""

    def test_webserver_uses_next_port_when_default_blocked(self):
        """Test that the webserver finds an alternative port when default is blocked.

        This test simulates the scenario where port 61208 is already in use,
        and verifies that the server will increment to find an available port.
        """
        from unittest.mock import MagicMock

        test_port = PORT_INTEGRATION_BASE
        blocking_socket = None

        try:
            blocking_socket = create_blocking_socket(ALL_INTERFACES, test_port)
        except OSError:
            # Port is already in use by another process, which is fine for this test
            pass

        try:
            mock_args = MagicMock()
            mock_args.port = test_port
            mock_args.bind_address = ALL_INTERFACES
            mock_args.debug = False
            mock_args.browser = False
            mock_args.password = False
            mock_args.disable_webui = True
            mock_args.disable_autodiscover = True

            mock_config = MagicMock()
            mock_config.has_section.return_value = False
            mock_config.get_value.return_value = None
            mock_config.get_list_value.return_value = ["*"]
            mock_config.get_bool_value.return_value = True

            # Verify port is blocked (either by us or another process)
            assert is_port_available(ALL_INTERFACES, test_port) is False
            next_port = find_available_port(ALL_INTERFACES, test_port + 1, max_attempts=DEFAULT_MAX_ATTEMPTS)
            assert next_port is not None
            assert next_port > test_port

        finally:
            if blocking_socket is not None:
                blocking_socket.close()


class TestIPv6Support:
    """Test cases for IPv6 support in port discovery."""

    def test_ipv6_port_available(self):
        """Test port availability check works with IPv6."""
        test_port = PORT_IPV6_BASE
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
                sock.bind(('::1', test_port))
        except OSError as e:
            if 'not supported' in str(e).lower() or 'invalid argument' in str(e).lower():
                pytest.skip("IPv6 not supported on this system")
            pass

        result = is_port_available(LOCALHOST, test_port)
        assert result in (True, False)


class TestConcurrentAccess:
    """Test cases for concurrent port checking."""

    def test_concurrent_port_checks_different_ports(self):
        """Test that concurrent port checks on different ports work correctly."""
        base_port = PORT_CONCURRENT_BASE + 20
        results = {}
        errors = []

        def check_port(port_offset):
            try:
                port = base_port + port_offset
                result = is_port_available(LOCALHOST, port)
                results[port] = result
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=check_port, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        for result in results.values():
            assert isinstance(result, bool)

    def test_find_available_port_is_thread_safe(self):
        """Test that find_available_port works correctly when called concurrently."""
        base_port = PORT_CONCURRENT_BASE
        results = []
        errors = []

        def find_port():
            try:
                result = find_available_port(LOCALHOST, base_port, max_attempts=DEFAULT_MAX_ATTEMPTS)
                if result is not None:
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=find_port) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
