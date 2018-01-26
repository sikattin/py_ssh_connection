# -*- coding: utf-8 -*-
import unittest
from connection.sshconn import SSHConn

class TestSSHConn(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        """entering process"""
        self.ssh_conn = SSHConn(loglevel=10)

    def tearDown(self):
        """exiting process"""
        del self.ssh_conn

    def test_ssh_connect(self):
        self.assertIsInstance(self.ssh_conn, SSHConn)

    def test_set_timeout(self):
        float_val1 = 3.0
        self.ssh_conn.set_timeout(6.0)
        float_val2 = self.ssh_conn.timeout

        assertIs(float_val1, float_val2)

    def test_send_cmd(self):
        msg = ''
        response = self.ssh_conn.send_cmd(cmd='ls')
        assertRegex(response, '.+')


if __name__ == '__main__':
    unittest.main()