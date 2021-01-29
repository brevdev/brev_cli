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

class GetOptionsFromType(click.Argument):
    def __init__(self, *args, **kwargs):
        self.previous_argument = kwargs.pop("previous_argument")
        assert self.previous_argument, "'previous_argument' parameter required"
        super(GetOptionsFromType, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if opts["opt"] == "remove":
            self.type = click.Choice([p["name"] for p in helpers.get_packages()])
        elif opts["opt"] == "add":
            pass


        return super(GetOptionsFromType, self).handle_parse_result(ctx, opts, args)



def packageWrapper():
    try:
        return [p["name"] for p in helpers.get_packages()]
    except:
        pass


@click.command(short_help="Add or remove a package.")
@click.argument(
    "opt",
    type=click.Choice(["add", "remove"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument(
    "name", 
    nargs=1,
    required=True,
    cls=GetOptionsFromType,
    previous_argument="opt"
)

def package(opt, name):
    '''
    Pip install a package to your remote environment.

    Add a package:
        brev package add <package_name>

    Remove an pacakge:
        brev package remove <package_name>

    '''
    # if not utilities.validate_directory():
    #     return

    if opt == "add":
        add(name)

    elif opt == "remove":
        remove(name)


def add(name):
    with yaspin(Spinners.aesthetic, text=f"Adding package {name}", color="yellow") as spinner:
        response = helpers.add_package(name)
    
        spinner.text=""
        spinner.ok(f"🥞 added package {name}")


def remove(name):
    with yaspin(Spinners.aesthetic, text=f"Removing package {name}", color="yellow") as spinner:
        time.sleep(2)

        packages = helpers.get_packages()
        package = [p for p in packages if p["name"] == name]
        if len(package) == 0:
            spinner.fail(f"Package {name} does not exist on your project. ")
            return

        try:
            response = helpers.remove_package(package[0]["id"])
        except helpers.BrevError as e:
            spinner.fail(f"\n{e}")

        spinner.text=""
        spinner.ok(f"🥞 removed package {name}")
