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
from scp import SCPClient
from socket import timeout
from mylogger import Logger
import paramiko

DEFAULT_TIMEOUT = 5.0


class SSHConn(object):
    """データ転送関連処理をまとめたクラス."""

    def __init__(self, hostname: str, username: str, password=None, authkey=None,
                 loglevel=None):
        """Constructor of SSHConn class.

        Args
            param1 hostname: connecting target.
            param2 username: ssh user name.
            param3 password: ssh user password.
            param4 authkey: private key for authentication.
        """
        # setup logger. loglevel sets 30(warning)
        if loglevel is None:
            loglevel = 30
        Logger.loglevel = loglevel
        self._logger = Logger(str(self))

        if password is None:
            self.password = ''
        self.hostame = hostname
        self.username = username
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
            paramiko.AuthenticationException: if authentication failed
            paramiko.SSHException: if there was any other error connecting or
                establishing an SSH session
            socket.error: if a socket error occurred while connecting
        """
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 鍵認証でない場合.
        if self.authkey is None:
            self.client.connect(hostname=self.host, username=self.username,
                           password=self.password, timeout=self.timeout)
        # 鍵認証の場合.
        else:
            self.client.connect(hostname=self.host, username=self.username,
                           pkey=self.authkey, timeout=self.timeout)
        self.scp = self._new_scpclient()
        self.channel = self._open_session()

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
        """
        for path in local_path:
            # make out whether path is directory. if path is direcotory,
            # recursive insert into True.
            if fileope.dir_exists(path):
                recursive = True

        self.scp.put(r'{}'.format(local_path), r'{}'.format(remote_path), recursive=recursive)



    def scp_get(self, remote_path: str, local_path='', recursive=False):
        """Transfer files from remotehost to localhost.

        Args:
            param1 remote_path:
            param2 local_path:
            param3 recursive: default is False.
                type: bool
        """
        self.scp.get(r'{}'.format(remote_path), r'{}'.format(local_path), recursive=recursive)

    def ssh_close(self):
        """close ssh connection."""
        self.client.close()
        self.scp.close()

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
        """
        cnt = 0
        msg = ''
        self.channel.settimeout(self.timeout)
        while cnt < retry_cnt:
            try:
                self.channel.send(cmd)
            except timeout as e:
                print("request was rejected.data has no sent.")
                cnt += 1
                continue
            else:
                if self.channel.recv_ready():
                    msg = self.channel.recv(2048)
                if self.channel.recv.stderr_ready():
                    msg = self.channel.recv_stderr(2048)
                    raise paramiko.SSHException("executed command returns error.")
                elif not msg:
                    raise paramiko.SSHException("no response from server.")
                break
        return msg

    def _new_scpclient(self):
        return SCPClient(self.client.get_transport())

    def _open_session(self):
        """Start an shell session on the SSH server."""
        return self.client.invoke_shell()

    def _confirm_recv(self):
        """confirm command response.

        Args:

        Return:
            if command is finished normally, return True.
        """
        if self.channel.recv_ready():
            return True