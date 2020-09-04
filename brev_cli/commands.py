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
from . import spinner
from . import authentication
import urllib.parse as urlparse



class GetOptionsFromType(click.Argument):
    def __init__(self, *args, **kwargs):
        self.previous_argument = kwargs.pop("previous_argument")
        assert self.previous_argument, "'previous_argument' parameter required"
        super(GetOptionsFromType, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if opts["type"] == "package":
            self.type = click.Choice([p["name"] for p in helpers.get_packages()])
        elif opts["type"] == "variable":
            self.type = click.Choice([v["name"] for v in helpers.get_variables()])
        elif opts["type"] == "endpoint":
            self.type = click.Choice([e["name"] for e in helpers.get_endpoint_list()])
            self.required = True  # this is used for logs, doesnt affect anything else
        elif opts["type"] == "project":
            self.type = click.Choice(helpers.get_project_list())
            # self.type = click.Choice([p["name"] for p in get_project_list()])

        return super(GetOptionsFromType, self).handle_parse_result(ctx, opts, args)


class GetArgumentsFromRequestType(click.Option):
    def __init__(self, *args, **kwargs):
        self.previous_argument = kwargs.pop("previous_argument")
        assert self.previous_argument, "'previous_argument' parameter required"
        super(GetArgumentsFromRequestType, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        # print(opts)
        if len(args) > 1:
            if args[1] == "POST" or args[1] == "PUT":
                self.type = click.Choice(
                    [
                        f
                        for f in os.listdir(".")
                        if os.path.isfile(f)
                        if f.endswith("json")
                    ]
                )

        return super(GetArgumentsFromRequestType, self).handle_parse_result(
            ctx, opts, args
        )

def localProjectWrapper():
    try:
        return helpers.get_project_list()
    except:
        click.secho("there is no active project", fg="red")


def localWrapper():
    try:
        return [ep["name"] for ep in helpers.get_endpoint_list()]
    except:
        pass


spin = spinner.Spinner()

@click.command(short_help="Initialize your Brev home, and retrieve all resources.")
def init():
    helpers.init_home()
    helpers.setup_shell()
    helpers.pull(entire_dir=True)
    helpers.set_default_project()


@click.command(short_help="Login to Brev CLI")
def login():
    authentication.Auth().login()
    helpers.init_home()
    helpers.setup_shell()
    helpers.pull(entire_dir=True)
    helpers.set_default_project()


@click.command(short_help="override local or remote")
@click.argument(
    "location",
    type=click.Choice(["remote", "local"]),
    nargs=1,
    required=False,
    autocompletion=helpers.get_env_vars,
)
def override(location, entire_dir=False):
    if location == "remote":
        push(entire_dir=entire_dir)
    elif location == "local":
        pull(entire_dir=entire_dir)


def pull(entire_dir=False):
    helpers.pull(entire_dir=entire_dir)


def push(entire_dir=False):
    helpers.push(entire_dir=entire_dir)


@click.command(short_help="Check current environment settings")
def status():
    helpers.status()


@click.command(short_help="Set active project")
@click.argument(
    "project",
    type=click.Choice(localProjectWrapper()),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
def set(project):
    """
        Set your active project\n
        \tPROJECT NAME: project you wish to set as active.\n
        \tActive project is used for \n-running endpoints,\n-getting variables,\n-getting packages,\n-getting shared code
        \tex: \n
        \t\tbrev set default #sets project 'default' to be active
    """
    helpers.set(project)

@click.command(short_help="run endpoints")
@click.argument(
    "endpoint",
    type=click.Choice(localWrapper()),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument(
    "httptype",
    type=click.Choice(["GET", "POST", "PUT", "DELETE"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.option(
    "--body",
    "-b",
    required=False,
    cls=GetArgumentsFromRequestType,
    previous_argument="httptype",
)
@click.option("--args", "-a", multiple=True)
@click.option('--stale', '-s', is_flag=True, help="Do not update remote before running.")
def run(endpoint, httptype, body, args, stale):
    helpers.run(endpoint,httptype,body,args,stale)


@click.command(short_help="list projects, endpoints, or packages")
@click.argument(
    "type",
    type=click.Choice(["package", "project", "endpoint"]),
    nargs=1,
    required=False,
    autocompletion=helpers.get_env_vars,
)
def list(type):
    helpers.list(type)


@click.command(short_help="View a diff of your current environment from remote")
def diff():
    helpers.diff()


@click.command(short_help="Create a new project")
@click.argument(
    "type",
    type=click.Choice(["project"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument("name", nargs=1, required=True)
def new(type, name):
    """
        Create new project\n
        \tTYPE: 'project'\n
        \tname: whatever you wish to name the project\n
        \tex: \n
        \t\tbrev new project myNewProj #creates new project named myNewProj
    """
    helpers.new(type,name)


@click.command(short_help="Add a package, variable, or endpoint")
@click.argument(
    "type",
    type=click.Choice(["package", "variable", "endpoint"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument("name", nargs=1, required=True)
def add(type, name):
    """
        Add a package or variable or endpoint\n
        \tTYPE: 'package', 'variable', or 'endpoint'\n
        \tname: package, variable, or endpoint name\n
        \tex: \n
        \t\tbrev add Arrow # pip installs Arrow to your project
    """
    helpers.add(type,name)


@click.command(short_help="Remove a package, variable, or endpoint")
@click.argument(
    "type",
    type=click.Choice(["package", "variable", "endpoint"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument(
    "name",
    nargs=1,
    required=True,
    cls=GetOptionsFromType,
    previous_argument=type,
)
def remove(type, name):
    """
        Remove a package, variable, or endpoint\n
        \tTYPE: 'package', 'varaible', 'endpoint'\n
        \tname: package, variable, or endpoint name\n
        \tex: \n
        \t\tbrev remve Arrow # removes package Arrow from your project environment
    """
    helpers.remove(type,name)

