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
def localWrapper():
    print([ep["name"] for ep in helpers.get_endpoint_list()])

    try:
        return [ep["name"] for ep in helpers.get_endpoint_list()]
    except:
        pass


class GetOptionsFromType(click.Argument):
    def __init__(self, *args, **kwargs):
        self.previous_argument = kwargs.pop("previous_argument")
        assert self.previous_argument, "'previous_argument' parameter required"
        super(GetOptionsFromType, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if opts["opt"] == "remove" or opts["opt"] == "run":
            self.type = click.Choice([ep["name"] for ep in helpers.get_endpoint_list()])
        elif opts["opt"] == "add":
            pass

        return super(GetOptionsFromType, self).handle_parse_result(ctx, opts, args)

class GetArgumentsFromRequestType(click.Option):
    def __init__(self, *args, **kwargs):
        self.previous_argument = kwargs.pop("previous_argument")
        assert self.previous_argument, "'previous_argument' parameter required"
        super(GetArgumentsFromRequestType, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        # print(opts)
        if len(args) > 1:
            # print(f"1: {args[1]}")
            # print(f"2: {args[2]}")
            # print(f"3: {args[3]}")
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



@click.command(short_help="Add, remove, or run endpoints.")
@click.argument(
    "opt",
    type=click.Choice(["add", "remove", "run"]),
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
# @click.argument(
#     "httptype",
#     type=click.Choice(["GET", "POST", "PUT", "DELETE"]),
#     nargs=1,
#     required=True,
#     autocompletion=helpers.get_env_vars,
# )
# @click.option(
#     "--body",
#     "-b",
#     required=False,
#     cls=GetArgumentsFromRequestType,
#     previous_argument="httptype",
# )
# @click.option("--args", "-a", multiple=True)
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
        run(name,httptype,body,args)


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
            spinner.fail(f"Endpoint {name} does not exist on your project.")
            return
        try:
            response = helpers.remove_endpoint(endpoint[0]["id"])
        except helpers.BrevError as e:
            spinner.fail(f"\n{e}")

        spinner.text=""
        spinner.ok(f"🥞 removed endpoint {name}")


# brev run
def run(endpoint,httptype,body,args):
    curr_dir = helpers.get_active_project_dir()
    endpoint_url = helpers.get_endpoint_list()
    ep = [ep for ep in endpoint_url if ep["name"] == endpoint][0]
    
    url = f"{helpers.get_active_project()['domain']}{ep['uri']}"
    args_dict = {}
    for arg in args:
        splitArg = arg.split("=")
        args_dict[splitArg[0]] = splitArg[1]
    if len(urlparse.urlencode(args_dict)) > 0:
        url = f"{url}?{urlparse.urlencode(args_dict)}"

    try:
        local_file = open(
            f"{curr_dir}/{ep['name']}.py", "r"
        )
        local_code = local_file.read()
        local_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")

    try:
        module_file = open(
            f"{curr_dir}/shared.py", "r"
        )
        shared_code = module_file.read()
        module_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")

    # if not stale == True: 
    try:
        click.secho("Updating endpoint/shared code before running remote ...")
        agent.BrevAPI(config.api_url).update_endpoint(
            code=local_code,
            name=ep["name"],
            project_id=ep["project_id"],
            id=ep["id"],
            methods=ep["methods"],
            uri=ep["uri"],
        )
        click.echo("endpoint updated!")

    except:
        click.secho("Couldn't update endpoint.", fg="bright_red")

    try:
        helpers.update_module(shared_code, helpers.get_active_project()['id'])
        click.echo("shared code updated!")
    except:
        click.secho("Couldn't update shared code.", fg="bright_red")


    
    if httptype == "GET":
        response = requests.get(url)
        click.echo(response) # if this isn't here, the pancake still shows
        helpers.print_response(response)

    elif httptype == "POST" or httptype == "PUT":
        jsonBody = {}
        if not body == None:
            with open(body, "r") as f:
                try:
                    jsonBody = json.loads(f.read())
                    f.close()
                except:
                    f.close()
                    click.echo(
                        click.style(f"The file ", fg="bright_red")
                        + click.style(f"{body} ", fg="red")
                        + click.style(f"is not valid json.", fg="bright_red")
                    )
                    return
        response = (
            requests.post(url, json=jsonBody)
            if httptype == "POST"
            else requests.post(url, json=jsonBody)
        )
        click.echo(response)
        helpers.print_response(response)

    # elif httptype == "DELETE":
    #     response = (
    #         requests.delete(url, json=jsonBody)
    #         if httptype == "POST"
    #         else requests.post(url, json=jsonBody)
    #     )
    #     click.echo(response)
    #     helpers.print_response(response)
