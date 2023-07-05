import socket
import sys
from typing import Any, Dict

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Loads config from yaml file and returns its content as a dict
    ----------
    :param config_path: path to config file
    """
    try:
        with open(config_path, "r") as config_handler:
            return yaml.safe_load(config_handler)
    except FileNotFoundError:
        print("Specified config was not found, make sure you've actually created it")
        sys.exit(1)


def ensure_oncall_is_running(oncall_host: str, oncall_port: int) -> None:
    """
    Tries to ensure Oncall instance is up and running
    ----------
    :param oncall_host: IP Address or hostname of Oncall instance
    :param oncall_port: port number Oncall is listening on
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((oncall_host, oncall_port))
        print("OK! Oncall is ready to accept API requests")
    except socket.error:
        print(f"Oncall instance is not available on {oncall_host}:{oncall_port}")
        sys.exit(2)
    finally:
        sock.close()
