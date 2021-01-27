import click
import subprocess
from pyfiglet import Figlet
import os
import time, json, copy, yaml
import requests
import difflib
import sys, time, threading
import requests
from . import agent
from . import helpers
from .config import config
from . import utilities
from . import authentication
import urllib.parse as urlparse
from yaspin import yaspin
from yaspin.spinners import Spinners

# with yaspin(Spinners.aesthetic, text=f"Uploading {filename}", color="yellow") as spinner:


@click.command(short_help="Add, remove, or run endpoints.")
@click.argument(
    "opt",
    type=click.Choice(["add", "remove", "run"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument("name", nargs=1, required=True)
def endpoint(opt, name):
    '''
    Create an endpoint:
        brev endpoint add <endpoint_name>

    Remove an endpoint:
        brev endpoint remove <endpoint_name>

    Run an endpoint:
        brev endpoint run <endpoint_name> <http_request_type> <args/json>

    '''
    # if not utilities.validate_directory():
    #     return

    if opt == "add":
        add(name)

    elif opt == "remove":
        remove(name)

    elif opt == "run":
        pass


def add(name):
    with yaspin(Spinners.aesthetic, text=f"Adding endpoint {name}", color="yellow") as spinner:
        response = helpers.add_endpoint(name)
    
        spinner.text=""
        spinner.ok(f"🥞 added endpoint {name}")


def remove(name):
    with yaspin(Spinners.aesthetic, text=f"Removing endpoint {name}", color="yellow") as spinner:
        time.sleep(2)

        endpoint = [e for e in helpers.get_endpoint_list() if e["name"] == name]
        if len(endpoint) == 0:
            click.secho(f"Endpoint {name} does not exist on your project. ", fg="red")
            return
        try:
            response = helpers.remove_endpoint(endpoint[0]["id"])
        except helpers.BrevError as e:
            spinner.fail(f"\n{e}")

        spinner.text=""
        spinner.ok(f"🥞 removed endpoint {name}")


# def run(name):
#     with yaspin(Spinners.aesthetic, text=f"Removing endpoint {name}", color="yellow") as spinner:
#         # spinner.on_color="on_blue"
#         time.sleep(2)