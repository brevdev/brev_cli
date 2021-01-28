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
        # if opts["opt"] == "add":
            # self.type = click.Choice([p["name"] for p in helpers.get_packages()])
        if opts["opt"] == "remove":
            self.type = [p["name"] for p in helpers.get_packages()]
        elif opts["opt"] == "endpoint":
            self.type = click.Choice([e["name"] for e in helpers.get_endpoint_list()])
            self.required = True  # this is used for logs, doesnt affect anything else
        # Note: We don't support projects here yet

        return super(GetOptionsFromType, self).handle_parse_result(ctx, opts, args)



def packageWrapper():
    try:
        return [p["name"] for p in helpers.get_packages()]
    except:
        pass


@click.command(short_help="Add or remove a env variable.")
@click.argument(
    "opt",
    type=click.Choice(["add", "remove"]),
    nargs=1,
    required=True,
    autocompletion=helpers.get_env_vars,
)
@click.argument("env", nargs=1, required=True)
def env(opt, env):
    '''
    Add or remove an environment variable to your project.

    Add environment variable:
        brev env add <var_name> 
        (a prompt will follow for the value)

    Remove an pacakge:
        brev env remove <var_name>

    '''
    # if not utilities.validate_directory():
    #     return

    if opt == "add":
        add(env)

    elif opt == "remove":
        remove(env)


def add(name):
    value = click.prompt(f"Value for variable {name}?")
    with yaspin(Spinners.aesthetic, text=f"Adding variable {name}", color="yellow") as spinner:
        response = helpers.add_variable(name, value)
        create_variables_file(utilities.get_active_project()['name'], utilities.get_active_project()['id'])
        spinner.text=""
        spinner.ok(f"🥞 added package {name}")


def remove(name):
    with yaspin(Spinners.aesthetic, text=f"Removing variable {name}", color="yellow") as spinner:
        variables = helpers.get_variables()
        variable = [v for v in variables if v["name"] == name]
        if len(variable) == 0:
            spinner.fail(f"Variable {name} does not exist on your project. ")
            return
        response = helpers.remove_variable(variable[0]["id"])
        create_variables_file(helpers.get_active_project()['name'], helpers.get_active_project()['id'])
        spinner.text=""
        spinner.ok(f"Variable {name} removed successfully.")
        



def create_variables_file(project_name, project_id, custom_dir=None):
    curr_dir = utilities.get_active_project_dir() if custom_dir==None else custom_dir
    variables = helpers.BrevAPI(config.api_url).get_variables(project_id)
    variables = variables["variables"]
    file_contents = ""
    if len(variables) == 0:
        file_contents = "# no variables defined for this project. Add them here: https://app.brev.dev/variables"
    else:
        file_contents = "# use 'import variables' in the endpoint to use the following values"

        for variable in variables:
            file_contents += f'\n{variable["name"]}="*****"'

    path = os.path.join(curr_dir, "variables.py")
    if not os.path.isfile(path):
        with open(path, "w") as file:
            file.write(file_contents)
            file.close()
        
        click.secho(
            f"\tCreated ~🥞/variables.py",
            fg="bright_green",
        )
    else:
        with open(path, "w") as file:
            file.write(file_contents)
            file.close()
        click.secho(
            f"\t~🥞/variables.py has been updated ",
            fg="bright_green",
        )
