#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:      shikano.takeki
#
# Created:     26/01/2018
# Copyright:   (c) shikano.takeki 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
from scp import SCPClient, SCPException
from socket import timeout, error
from mylogger import factory
from osfile import fileope
import paramiko

DEFAULT_TIMEOUT = 60.0
PRIVATE_KEY = ''

class SSHConn(object):
    """データ転送関連処理をまとめたクラス."""

    def __init__(self, hostname: str, username: str, password=None, authkey=None,
                 logger=None, loglevel=None):
        """Constructor of SSHConn class.

           password or authkey argument is necessary. raise error to set double.
        Args:
            param1 hostname: connecting target.
            param2 username: ssh user name.
            param3 password: ssh user password.
            param4 authkey: private key for authentication.
            param5 logger: logger instance
            param6 loglevel: re-set log level of logger instance.
        """
        global DEFAULT_TIMEOUT, PRIVATE_KEY
        if password is None and authkey is None:
            raise TypeError("'password' or 'authkey' argument is necessary.")
        if password is not None and authkey is not None:
            raise TypeError("'password' and 'authkey' argument is not set at once.")
        # setup logger.
        self._logger = logger
        if logger is None:
            slog_fac = factory.StdoutLoggerFactory()
            self._logger = slog_fac.create()
        if self._logger is not None and loglevel in {10, 20, 30, 40, 50}:
            self._logger.set_loglevel(loglevel)

        self.hostname = hostname
        self.username = username
        self.password = password
        self.authkey = authkey
        self.timeout = DEFAULT_TIMEOUT

    def __enter__(self):
        """コンテキストマネージャ実装のため."""
        self.ssh_connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャ実装のため."""
        self.ssh_close()

    def ssh_connect(self):
        """do ssh connection.
        Args:

        Return:

        Raises:
            paramiko.BadHostKeyException: if the server's host key could not be
                verified
            paramiko.AuthenticationException:
            paramiko.SSHException: if there was any other error connecting or
                establishing an SSH session
            socket.error: if a socket error occurred while connecting
        """
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # authentication.
        self.client.connect(hostname=self.hostname, username=self.username,
            key_filename=self.authkey,
            password=self.password,
            timeout=self.timeout)
        if self.client is not None:
            self._logger.info("succeeded to ssh connect.")
        self._transport = self.client.get_transport()
        self.scp = self._new_scpclient()
        self.channel = self._open_session()

    def exec_cmd(
        self,
        command: str,
        bufsize=-1,
        timeout=None,
        environment=None,
    ):
        """
        Execute a command on the SSH sever.

        Args:
            param1 command: the command to execute
                type: str
            param2 bufsize:
                type: int
            param3 timeout: set command's timeout value.
                type: int
            param4 environment: set shell environment variables.
                type: dict

        Returns:
            the stdin, stdout , stderr and return code of the executing command,
            as a tupple.

        Raises:
            SSHException: if the server fails to execute the command.
        """
        if timeout is None:
            timeout = self.timeout
        rc = None
        # open a new session
        session = self._transport.open_session(timeout=timeout)
        # set timeout value.
        if timeout is not None:
            session.settimeout(timeout)
        # set environment variables.
        if environment:
            session.update_environment(environment)
        # execute command.
        session.exec_command(command=command)
        # get stdin, stdout, stderr
        stdin = session.makefile('wb', bufsize)
        stdout = session.makefile('r', bufsize)
        stderr = session.makefile_stderr('r', bufsize)
        # get return code
        session.recv(4096)
        if session.exit_status_ready():
            rc = session.recv_exit_status()
        return stdin, stdout, stderr, rc

    def scp_put(self, local_path, remote_path: str, recursive=False):
        """Transfer files to remote host.

        Args:
            param1 local_path:
                type: string or list
            param2 remote_path:
                type: string
            param3 recursive: if local_path is directory ...False
            is list ...True
                type: bool

        Raises:
            paramiko.SSHException
            socket.timeout
            socket.error
            SCPException
        """

        for path in local_path:
            # make out whether path is directory. if path is direcotory,
            # True insert into recursive arg.
            if fileope.dir_exists(path):
                recursive = True
        try:
            self.scp.put(r'{}'.format(local_path), r'{}'.format(remote_path), recursive=recursive)
        except SCPException as scp_e:
            self._logger.error(scp_e)
            raise scp_e
        except paramiko.SSHException as ssh_e:
            self._logger.error(ssh_e)
            raise ssh_e
        except timeout as st:
            self._logger.error(st)
            raise st
        except error as se:
            self._logger.error(se)
            raise se
        else:
            self._logger.info("raise no exception. scp executed.")

    def scp_get(self, remote_path: str, local_path='', recursive=False):
        """Transfer files from remotehost to localhost.

        Args:
            param1 remote_path:
            param2 local_path:
            param3 recursive: default is False.
                type: bool

        Raises:
            paramiko.SSHException
            SCPException
            socket.timeout
            socket.error
        """
        try:
            self.scp.get(r'{}'.format(remote_path), r'{}'.format(local_path), recursive=recursive)
        except SCPException as scp_e:
            self._logger.error(scp_e)
            raise scp_e
        except paramiko.SSHException as ssh_e:
            self._logger.error(ssh_e)
            raise ssh_e
        except timeout as st:
            self._logger.error(st)
            raise st
        except error as se:
            self._logger.error(se)
            raise se
        else:
            self._logger.info("raise no exception. scp executed.")

    def ssh_close(self):
        """close ssh connection."""
        self._logger.info("closing ssh session...")
        # close an SSH Transport.
        self._transport.close()
        # close a SCP connection.
        self.scp.close()
        # close SSH session.
        self.client.close()

    def set_timeout(timeout_value: float):
        """set timeout option for TCP connection.

        Args:
            param1 timeout_value: timeout value. it must be float.
        """
        if not isinstance(timeout_value, float):
            timeout_value = float(timeout_value)
        self.timeout = timeout_value

    def send_cmd(self, cmd: str, retry_cnt=5):
        """send executing command to server.

        Args:
            cmd: executing command.
            retry_cnt: limit of retry. default is 5.

        Returns:
            received data, as a str/bytes.

        Raises:
            paramiko.SSHException
            timeout
        """
        cnt = 0
        msg = ''
        self.channel.settimeout(self.timeout)
        while cnt < retry_cnt:
            try:
                data = self.channel.send(cmd)
                self._confirm_recv()
            except timeout as e:
                self._logger.error("request was rejected.data has no sent.")
                cnt += 1
                continue
            else:
                break

    def _new_scpclient(self):
        """return SCPClient instance."""
        return SCPClient(self._transport)

    def _open_session(self):
        """Start an shell session on the SSH server."""
        return self.client.invoke_shell()

    def _confirm_recv(self):
        """confirm whether the data is sent.
        """
        msg = b''
        try:
            msg = self.channel.recv(4096)
        except timeout as e:
            raise e
        else:
            if msg and msg[0:1] == b'\x00':
                return
            elif msg and msg[0:1] == b'\x01':
                self._logger.error("raise error during confirming the data receieved.")
                raise paramiko.SSHException("raise error during confirming the data receieved.")
            elif self.channel.recv_stderr_ready():
                msg = self.channel.recv_stderr(4096)
                self._logger.error("Return error result of executing command.")
                raise paramiko.SSHException("executed command returns error.")
            elif not msg:
                self._logger.error("no response from remote host.")
                raise paramiko.SSHException("no response from server.")


class SSHConnException(Exception):
    """SSHConn exception class"""
    pass
