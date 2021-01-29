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
        # Note: We don't support projects here yet

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

def localWrapper():
    try:
        return [ep["name"] for ep in helpers.get_endpoint_list()]
    except:
        pass

def projectWrapper():
    try:
        return [p["name"] for p in helpers.get_remote_only_projects()]
    except:
        pass

spin = spinner.Spinner()

def validate_directory():
    if helpers.get_active_project_dir() == None:
        helpers.not_in_brev_error_message()
        return False
    return True
        # raise click.Abort()

@click.command(short_help="Initialize a Brev directory.")
@click.argument(
    "project",
    type=click.Choice(projectWrapper()),
    nargs=1,
    required=False,
    autocompletion=helpers.get_env_vars,
)
def init(project):
    curr_dir = os.getcwd()
    try:
        if not project == None:
            # create folder for project
            curr_dir = f"{curr_dir}/{project}"
            os.mkdir(curr_dir)
            os.mkdir(f"{curr_dir}/.brev")
            helpers.new("project", project, curr_dir, create=False)
            endpoints = helpers.get_endpoints(write=True, init=True, custom_dir=curr_dir) # inits the .brev/endpoints.json file
            project = helpers.get_active_project(curr_dir)
            ## now add the endpoints
            for endpoint in endpoints:
                if endpoint["archived"] != True:
                    helpers.create_endpoint_file(endpoint, project, curr_dir)

        else:        
            # create the .brev directory here
            if not os.path.isdir(f"{curr_dir}/.brev"):
                os.mkdir(f"{curr_dir}/.brev")
            
            # create new project with foldername as project name
            folder_name = os.path.basename(curr_dir)
            helpers.new("project", folder_name, curr_dir)
            helpers.get_endpoints(write=True, init=True) # inits the .brev/endpoints.json file
            
    except helpers.BrevError as BErr:
        click.secho(str(BErr), fg="green")
    except:
        click.echo("An error occured. Please try again or reach out to support. Text us: 415-818-0207")

@click.command(short_help="Login to Brev CLI")
def login():
    click.echo("LOGIN ")
    authentication.Auth().login()
    helpers.init_necessary_files()
    helpers.setup_shell()
    
    root = os.path.expanduser("~")
    with open(f"{root}/.brev/active_projects.json", "w") as file:
        file.write(json.dumps([]))
        file.close()


@click.command(short_help="deploy your changes to remote")
def push(entire_dir=False):
    if not validate_directory():
        return
    helpers.push(entire_dir=entire_dir)

@click.command(short_help="pull changes to match remote")
def pull(entire_dir=False):
    if not validate_directory():
        return
    helpers.pull(entire_dir=entire_dir)


@click.command(short_help="Check current environment settings")
def status():
    if not validate_directory():
        return
    try:
        helpers.status()
    except:
        helpers.not_in_brev_error_message()

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
    if not validate_directory():
        return
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
    if not validate_directory():
        return
    helpers.list(type)


@click.command(short_help="View a diff of your current environment from remote")
def diff():
    if not validate_directory():
        return
    helpers.diff()

@click.command(short_help="Also View Project Logs (sometimes people add an 's')")
def logs():
    """
       View Project Logs\n
    """
    if not validate_directory():
        return
    helpers.logs()

@click.command(short_help="View Project Logs")
def log():
    """
       View Project Logs
    """
    if not validate_directory():
        return
    helpers.logs()


def rename():
    pass

def update_renamed():
    helpers.get_endpoints(write=True)

@click.command(short_help="Refresh Endpoints")
def refresh():
    if not validate_directory():
        return
    helpers.refresh()

