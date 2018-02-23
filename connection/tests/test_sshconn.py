# -*- coding: utf-8 -*-
import unittest
from connection.sshconn import SSHConn
from getpass import getpass

DEFAULT_TIMEOUT = 5.0
PRIVATE_KEY = '/home/Nxj_ToS_TS1/.ssh/id_rsa'

class TestSSHConn(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        """entering process"""
        self.test_ssh_connect()

    def tearDown(self):
        """exiting process"""
        del self.ssh_conn

    def test_ssh_connect(self):
        self.ssh_conn = SSHConn(loglevel=10,
                                hostname='172.16.30.7',
                                username='Nxj_ToS_TS1',
                                authkey=PRIVATE_KEY)
        self.assertIsInstance(self.ssh_conn, SSHConn)

    def test_exec_cmd(self):
        """"""
        stdin, stdout, stderr, rc = self.ssh_conn.exec_cmd(command="ls")
        assertIsInstance(stdin, bytes)
        assertIsInstance(stdout, str)
        assertIsInstance(stderr, str)
        assertIsNotNone(rc)

    def test_set_timeout(self):
        float_val1 = 3.0
        self.ssh_conn.set_timeout(6.0)
        float_val2 = self.ssh_conn.timeout

        assertIs(float_val1, float_val2)

    def test_send_cmd(self):
        response = self.ssh_conn.send_cmd(cmd='ls')
        assertNotEqual(len(response), 0)
        # assertRegex(response, '.+')


if __name__ == '__main__':
    unittest.main()