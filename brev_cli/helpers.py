import click
import subprocess
from pyfiglet import Figlet
import os
import time, json, copy, yaml
import requests
from .config import config
from . import agent
import difflib
from getpass import getpass
import sys, time, threading
from pathlib import Path
from . import authentication
import urllib.parse as urlparse
from . import spinner
import subprocess

root = os.path.expanduser("~")
showAnimation = True
global_endpoints = {}
global_projects = []
spin = spinner.Spinner()

class BrevAPI(agent.BrevAPI):
    def __init__(self, domain=None):
        if not os.path.exists(authentication.brev_home):
            click.echo(
                click.style("Seems like you're not initialized:", fg="red")
                + click.style(
                    "Would you like to set up your local Brev directory?",
                    fg="green",
                ),
            )
            res = yes_no_prompt()
            if res:
                init_home()
                pull(entire_dir=True)

        def should_login_callback():
            click.echo(
                click.style("Unauthenticated:", fg="red")
                + click.style(
                    "Would you like to login to your Brev.Dev account?\nTo create a new account visit https://app.brev.dev/signup",
                    fg="green",
                ),
            )
            res = yes_no_prompt()
            return res

        super().__init__(should_login_callback, domain=domain)


def yes_no_prompt():
    response = None
    while response is None:
        value = click.prompt(f"yes(y)/no(n)")
        response = filter_yes_no(value)
        if response is None:
            click.secho("Please enter yes(y)/no(n)", fg="yellow")

    if response == "y":
        return True
    elif response == "n":
        return False
    else:
        # should never happen
        raise Exception("im a little teapot")


def filter_yes_no(value):
    value = value.strip().lower()
    if value == "yes" or value == "y":
        return "y"
    elif value == "no" or value == "n":
        return "n"
    else:
        return None


def get_env_vars(ctx, args, incomplete):
    return [k for k in os.environ.keys() if incomplete in k]


def get_packages():
    packages = BrevAPI(config.api_url).get_packages(get_active_project()["id"])
    return packages["packages"]


def add_package(pkg_name):
    packages = BrevAPI(config.api_url).add_packages(get_active_project()["id"], pkg_name)
    return packages


def remove_package(pkg_id):
    packages = BrevAPI(config.api_url).remove_package(pkg_id)
    return packages


def get_variables():
    variables = BrevAPI(config.api_url).get_variables(get_active_project()["id"])
    return variables["variables"]


def add_variable(name, value):
    variables = BrevAPI(config.api_url).add_variables(
        get_active_project()["id"], name, value
    )
    return variables


def remove_variable(var_id):
    variables = BrevAPI(config.api_url).remove_variables(var_id)
    return variables


def format_endpoint_data(endpoints, projects):
    project_names = {p["id"]: p["name"] for p in projects}
    output = {}
    for endpoint in endpoints:
        project_name = project_names[endpoint["project_id"]]
        if project_name in output.keys():
            output[project_name].append(endpoint)
        else:
            output[project_name] = [endpoint]

    return output


def get_endpoints(write):
    # make a fetch
    projects = BrevAPI(config.api_url).get_projects()
    endpoints = BrevAPI(config.api_url).get_endpoints()
    if write:
        with open(f"{root}/.brev/endpoints.json", "w") as file:
            file.write(json.dumps(endpoints["endpoints"]))
            file.close()
        with open(f"{root}/.brev/projects.json", "w") as file:
            file.write(json.dumps(projects["projects"]))
            file.close()
    return format_endpoint_data(endpoints["endpoints"], projects["projects"])

def get_projects(write=False):
    if write:
        projects = BrevAPI(config.api_url).get_projects()
        with open(f"{root}/.brev/projects.json", "w") as file:
            file.write(json.dumps(projects["projects"]))
            file.close()
            return projects["projects"]
    else:
        with open(f"{root}/.brev/projects.json", "r") as file:
            projects = json.loads(file.read())
            file.close()
            return projects

def add_endpoint(name):
    endpoints = []
    with open(f"{root}/.brev/endpoints.json", "r") as file:
        endpoints = json.loads(file.read())

    endpoint = BrevAPI(config.api_url).add_endpoint(
        name, get_active_project()["id"]
    )["endpoint"]
    endpoints.append(endpoint)
    with open(f"{root}/.brev/endpoints.json", "w") as file:
        file.write(json.dumps(endpoints))
        file.close()
    create_endpoint_file(endpoint, get_active_project()["name"])
    return endpoint


def remove_endpoint(id):
    endpoints = []
    with open(f"{root}/.brev/endpoints.json", "r") as file:
        endpoints = json.loads(file.read())

    endpoint = BrevAPI(config.api_url).remove_endpoint(id)

    updated_endpoints = [e for e in endpoints if not e["id"] == id]
    removedEP = [e for e in endpoints if e["id"] == id]

    with open(f"{root}/.brev/endpoints.json", "w") as file:
        file.write(json.dumps(updated_endpoints))
        file.close()
    remove_endpoint_file(removedEP[0], get_active_project()["name"])
    return endpoint

def get_project_list():
    with open(f"{root}/.brev/projects.json", "r") as myfile:
        projects = json.loads(myfile.read())
        myfile.close()
        return [p["name"] for p in projects]


def get_endpoint_list():
    active_project = get_active_project()["id"]
    with open(f"{root}/.brev/endpoints.json", "r") as myfile:
        endpoints = json.loads(myfile.read())
        myfile.close()
        return [ep for ep in endpoints if ep["project_id"] == active_project]


def formatted_ep_data():
    with open(f"{root}/.brev/projects.json", "r") as project_file, open(
        f"{root}/.brev/endpoints.json", "r"
    ) as endpoint_file:
        projs = json.loads(project_file.read())
        eps = json.loads(endpoint_file.read())
        project_file.close()
        endpoint_file.close()
        return format_endpoint_data(eps, projs)


def do_init(email, password):
    try:
        certs = BrevAPI(config.api_url).authenticate(email, password)
    except requests.exceptions.HTTPError as http_error:
        if http_error.response.status_code == 401:
            click.echo(click.style("-> Incorrect email or password", fg="red"))
            click.echo(
                click.style(
                    "-> Would you like to create an account? https://app.brev.dev/signup",
                    fg="green",
                )
            )
        else:
            click.echo(
                click.style(
                    "Oops looks like there is network or server error", fg="red"
                )
            )
        return
    BrevAPI.access_key = certs["access_token"]
    store_refresh_token(certs["access_token"], certs["refresh_token"])


def validate_type(arg_type):
    if arg_type == "project" or arg_type == "endpoint":
        return arg_type
    else:
        raise click.BadParameter(
            "Invalid type. Argument must be either `project` or `endpoint`"
        )

def setup_shell():
    shell_type = click.prompt("Do you use Zsh, Bash, or Fish? ")
    shell_type = shell_type.lower()

    complete = '\n\n## brev cli shell completion\n'

    if shell_type == "zsh":
        complete += 'eval "$(_BREV_COMPLETE=source_zsh brev)"\n\n'
        with open(f"{root}/.zshrc", "a") as file:
            file.write(f"{complete}")
            file.close()
        click.secho("Please run 'source ~/.zshrc' to finish setting up shell autocomplete" ,fg="yellow")

    elif shell_type == "bash":
        complete += 'eval "$(_BREV_COMPLETE=source_bash brev)"\n\n'
        with open(f"{root}/.bash_profile", "a") as file:
            file.write(f"{complete}")
            file.close()
        with open(f"{root}/.bashrc", "a") as file:
            file.write(f"{complete}")
            file.close()
        click.secho("please run 'source ~/.bashrc' and 'source ~/.bash_profile to finish setting up shell autocomplete" ,fg="yellow")

    elif shell_type == "fish":
        complete += 'eval (env _FOO_BAR_COMPLETE=source_fish foo-bar)\n\n'
        with open(f"{root}/.config/fish/completions/brev.fish", "a") as file:
            file.write(f"{complete}")
        click.secho("You might need to source ~/.config/fish/completions/brev.fish to finish setting up shell autocomplete" ,fg="yellow")


def init_home():
    brev_home = os.path.join(Path.home(), ".brev")
    try:
        os.mkdir(brev_home)
    except FileExistsError:
        click.secho("BrevDev directory already exists", fg="yellow")


def create_root_dir():
    if not os.path.isdir(f"{root}/BrevDev"):
        click.secho("\tBrev Directory Does Not Exist...", fg="yellow")
        os.mkdir(f"{root}/BrevDev")
        click.secho(f"\tCreated ~/BrevDev! 🥞", fg="bright_green")


def create_project_dir(project):
    if not os.path.isdir(f"{root}/BrevDev/{project}"):
        click.secho(f"\t{project} does not exist...", fg="yellow")
        os.mkdir(f"{root}/BrevDev/{project}")
        click.secho(f"\tCreated ~/BrevDev/{project} ! 🥞", fg="bright_green")
    if not os.path.isdir(f"{root}/.brev"):
        os.mkdir(f"{root}/.brev")


def create_endpoint_file(endpoint, project):
    if not os.path.isfile(f"{root}/BrevDev/{project}/{endpoint['name']}.py"):
        with open(f"{root}/BrevDev/{project}/{endpoint['name']}.py", "w") as file:
            file.write(endpoint["code"])
            file.close()
        click.secho(
            f"\tCreated {root}/BrevDev/{project}/{endpoint['name']}.py ! 🥞",
            fg="bright_green",
        )
    else:
        with open(f"{root}/BrevDev/{project}/{endpoint['name']}.py", "w") as file:
            file.write(endpoint["code"])
            file.close()
        click.secho(
            f"🥞 ~/BrevDev/{project}/{endpoint['name']}.py has been updated ",
            fg="bright_green",
        )


def remove_endpoint_file(endpoint, project):
    if not os.path.isfile(f"{root}/BrevDev/{project}/{endpoint['name']}.py"):
        return
    else:
        os.remove(f"{root}/BrevDev/{project}/{endpoint['name']}.py")
        click.secho(
            f"🥞 ~/BrevDev/{project}/{endpoint['name']}.py has been removed ",
            fg="green",
        )

def get_modules(write=False):
    if write:
        modules = BrevAPI(config.api_url).get_modules()
        with open(f"{root}/.brev/modules.json", "w") as file:
            file.write(json.dumps(modules["modules"]))
            file.close()
            return modules["modules"]
    else:
        with open(f"{root}/.brev/modules.json", "r") as file:
            modules = json.loads(file.read())
            file.close()
            return modules



def create_module_file(project_name, project_id, write=False):
    modules = get_modules(write=write)
    module = [m for m in modules if m["project_id"] == project_id]
    if len(module) == 0:
        return
    module = module[0]
    file_content = ""
    if module["source"] == "":
        file_content = f"# no shared code yet. Code written here is accessible by every endpoint in this project {project_name}"
    else:
        file_content = module["source"]

    if not os.path.isfile(f"{root}/BrevDev/{project_name}/shared.py"):
        with open(f"{root}/BrevDev/{project_name}/shared.py", "w") as file:
            file.write(file_content)
            file.close()
        click.secho(
            f"\tCreated {root}/BrevDev/{project_name}/shared.py ! 🥞",
            fg="bright_green",
        )
    else:
        with open(f"{root}/BrevDev/{project_name}/shared.py", "w") as file:
            file.write(file_content)
            file.close()
        click.secho(
            f"🥞 ~/BrevDev/{project_name}/shared.py has been updated ",
            fg="bright_green",
        )


def get_logs(type, id):
    response = BrevAPI(config.api_url).get_logs(type, id)
    return response["logs"]


def create_new_project(project_name):
    response = BrevAPI(config.api_url).create_project(project_name)
    return response

def update_module(source, project_id=None):
    # fetch modules for project id
    if project_id == None:
        project_id = get_active_project()['id']
    
    response = BrevAPI(config.api_url).get_modules()
    
    # get matched module
    module = [m for m in response['modules'] if m['project_id']==project_id][0]
    
    # update the module
    response = BrevAPI(config.api_url).update_module(module['id'], source)

    return response

def create_variables_file(project_name, project_id):
    variables = BrevAPI(config.api_url).get_variables(project_id)
    variables = variables["variables"]
    file_contents = ""
    if len(variables) == 0:
        file_contents = "# no variables defined for this project. Add them here: https://app.brev.dev/variables"
    else:
        file_contents = "# use 'import variables' in the endpoint to use the following values"

        for variable in variables:
            file_contents += f'\n{variable["name"]}="*****"'

    if not os.path.isfile(f"{root}/BrevDev/{project_name}/variables.py"):
        with open(f"{root}/BrevDev/{project_name}/variables.py", "w") as file:
            file.write(file_contents)
            file.close()
        click.secho(
            f"\tCreated {root}/BrevDev/{project_name}/variables.py ! 🥞",
            fg="bright_green",
        )
    else:
        with open(f"{root}/BrevDev/{project_name}/variables.py", "w") as file:
            file.write(file_contents)
            file.close()
        click.secho(
            f"🥞 ~/BrevDev/{project_name}/variables.py has been updated ",
            fg="bright_green",
        )


def create_readme_file(readme_string):
    if not os.path.isfile(f"{root}/BrevDev/readme.md"):
        with open(f"{root}/BrevDev/readme.md", "w") as file:
            file.write(readme_string)
            file.close()
        click.secho(
            f"\tCreated readme at {root}/BrevDev/readme.md ! 🥞", fg="bright_green"
        )
    else:
        with open(f"{root}/BrevDev/readme.md", "w") as file:
            file.write(readme_string)
            file.close()
            # Todo: run a diff, add a click.secho if changes were added to the readme


def set_active_project(project):
    with open(f"{root}/.brev/active.json", "w") as file:
        file.write(json.dumps(project))
        file.close()


def get_active_project():
    with open(f"{root}/.brev/active.json", "r") as file:
        active = json.loads(file.read())
        return active
        file.close()


def pull(entire_dir=False):
    click.echo(click.style("... overriding your local with remote", fg="yellow"))
    
    create_root_dir()

    readme_contents = ""

    endpoints = get_endpoints(write=True)
    projects = get_projects()
    if entire_dir == False:
        projects = [get_active_project()]
    for project in [p["name"] for p in projects]:
        create_project_dir(project)
        readme_contents += f"Project: {project}\n"
        project_id = [p["id"] for p in projects if p["name"]==project][0]
        create_variables_file(project, project_id)
        create_module_file(project, project_id, write=True)

        numEPs = 0
        if project in endpoints.keys():
            for endpoint in endpoints[project]:
                if endpoint["archived"] != True:
                    numEPs += 1
                    readme_contents += (
                        f"\tEndpoint:\n\t\tname:{endpoint['name']}\n\t\tid:{endpoint['id']}"
                    )
                    readme_contents += (
                        f"\n\t\tExecuteURL: {config.api_url}{endpoint['uri']}\n"
                    )
                    create_endpoint_file(endpoint, project)
        if numEPs == 0:
            readme_contents += "... no active endpoints \n"
        readme_contents += "\n"

def push(entire_dir=False):
    click.echo(click.style("... overriding remote with your local", fg="yellow"))
    try:
        endpoints = formatted_ep_data()
        project_list = (endpoints.keys() if entire_dir == True else [get_active_project()["name"]])
        for project in project_list:
            for endpoint in endpoints[project]:
                # grab contents of file
                try:
                    local_file = open(
                        f"{root}/BrevDev/{project}/{endpoint['name']}.py", "r"
                    )
                    local_code = local_file.read()
                    local_file.close()
                    # push local_code to remote
                    agent.BrevAPI(config.api_url).update_endpoint(
                        code=local_code,
                        name=endpoint["name"],
                        project_id=endpoint["project_id"],
                        id=endpoint["id"],
                        methods=endpoint["methods"],
                        uri=endpoint["uri"],
                    )
                    click.secho(
                        f"🥞 ~/BrevDev/{project}/{endpoint['name']}.py has been pushed! ",
                        fg="bright_green",
                    )
                except:
                    # the file might not exist locally.
                    pass
            ## udpate shared code. 1 per project (as of this writing)
            try: 
                local_file = open(
                    f"{root}/BrevDev/{project}/shared.py", "r"
                )
                shared_code = local_file.read()
                local_file.close()
                update_module(source=shared_code)
                click.secho(
                    f"🥞 ~/BrevDev/{project}/shared.py has been pushed! ",
                    fg="bright_green",
                )
            except:
                click.secho(
                    f"Could not update ~/BrevDev/{project}/shared.py, it might contain a bug.",
                    fg="yellow",
                )                

    except requests.exceptions.HTTPError:
        click.secho(
            f"Could not fetch from remote. Please check your internet.", fg="bright_red"
        )


### Entry points from Commands.py ###
def status():
    click.echo(
        f"Your active project is "
        + click.style(f"{get_active_project()['name']}", fg="green")
    )
    click.echo(f"View API docs here: {get_active_project()['domain']}/docs")
    
    all_packages = get_packages()
    if len(all_packages) > 0:
        click.echo("Packages: ")
        for p in all_packages:
            if p["status"] == "installed":
                click.echo(f"\t{p['name']} {p['status']} v{p['version']}")
            elif p["status"] == "error":
                click.echo(
                    click.style(f"\t{p['name']} {p['status']} v{p['version']}", fg="red")
                )
            elif p["status"] == "pending":
                click.echo(
                    click.style(f"\t{p['name']} {p['status']} v{p['version']}", fg="yellow")
                )
    else:
        click.echo("no installed packages")

def set_default_project():
    project_list = get_projects()
    default = [p for p in project_list if p['name']=="default"]
    set(default[0]['name'])


def set(project_name):
    project_list = get_projects()
    selected_project = [p for p in project_list if p["name"] == project_name][0]
    set_active_project(selected_project)
    click.echo(
        f"Your active project is now "
        + click.style(f"{get_active_project()['name']}", fg="green")
    )

def run(endpoint,httptype,body,args,stale):
    endpoint_url = get_endpoint_list()
    ep = [ep for ep in endpoint_url if ep["name"] == endpoint][0]
    
    url = f"{get_active_project()['domain']}{ep['uri']}"
    args_dict = {}
    for arg in args:
        splitArg = arg.split("=")
        args_dict[splitArg[0]] = splitArg[1]
    if len(urlparse.urlencode(args_dict)) > 0:
        url = f"{url}?{urlparse.urlencode(args_dict)}"

    try:
        local_file = open(
            f"{root}/BrevDev/{get_active_project()['name']}/{ep['name']}.py", "r"
        )
        local_code = local_file.read()
        local_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")
        stale = True

    try:
        module_file = open(
            f"{root}/BrevDev/{get_active_project()['name']}/shared.py", "r"
        )
        shared_code = module_file.read()
        module_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")
        stale = True

    if not stale == True: 
        try:
            spin.start()
            click.echo("Updating endpoint/shared code before running remote ...")
            agent.BrevAPI(config.api_url).update_endpoint(
                code=local_code,
                name=ep["name"],
                project_id=ep["project_id"],
                id=ep["id"],
                methods=ep["methods"],
                uri=ep["uri"],
            )
            click.echo("endpoint updated!")
            # spin.stop()

        except:
            # spin.stop()
            click.secho("Couldn't update endpoint.", fg="bright_red")

        try:
            # spin.start()
            update_module(shared_code, get_active_project()['id'])
            click.echo("shared code updated!")
            spin.stop()
        except:
            click.secho("Couldn't update shared code.", fg="bright_red")


    
    if httptype == "GET":
        if stale==True:
            spin.start()
        response = requests.get(url)
        spin.stop()
        click.echo(response) # if this isn't here, the pancake still shows
        print_response(response)

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
        if stale==True:
            spin.start()
        response = (
            requests.post(url, json=jsonBody)
            if httptype == "POST"
            else requests.post(url, json=jsonBody)
        )
        spin.stop()
        click.echo(response)
        print_response(response)

    elif httptype == "DELETE":
        spin.start()
        response = (
            requests.delete(url, json=jsonBody)
            if httptype == "POST"
            else requests.post(url, json=jsonBody)
        )
        spin.stop()
        click.echo(response)
        print_response(response)

def print_response(response):
    msg_color = "green" if str(response.status_code )[0] == "2" else "red"
    click.echo(
        click.style("\nStatus Code: ", fg=msg_color) +
        click.style(f"{response.status_code}", fg=msg_color)
    )
    headers = response.headers
    response = response.json()
    click.echo(
        click.style("\nResponse: \n") +
        click.style(f"{response}")  
    )
    try:
        stdout = urlparse.unquote(headers['x-stdout'])
        click.echo(
            click.style("\nStandard Out: \n") +
            click.style(stdout)
        )
    except:
        pass

def list(type):
    if not type or type == "project" or type == "endpoint":
        readme_contents = ""
        endpoints = formatted_ep_data()
        projects = get_projects()
        for project in endpoints.keys():
            full_proj_obj = [p for p in projects if p['name']==project]

            readme_contents += f"Project: {project}\n"
            readme_contents += f"API docs: {full_proj_obj[0]['domain']}/docs\n"
            for endpoint in endpoints[project]:
                readme_contents += f"\tEndpoint:\n\t\tname: {endpoint['name']}\n\t\tid: {endpoint['id']}\n"
                readme_contents += f"\t\tURL: {full_proj_obj[0]['domain']}{endpoint['uri']}\n"
            readme_contents += "\n"

        click.secho(readme_contents, fg="yellow")
    elif type == "package":
        pkgs = get_packages()
        click.secho(f"Project :", fg="green")
        installed = ""
        errored = ""
        pending = ""
        for pkg in pkgs:
            if pkg["status"] == "installed":
                installed += f"{pkg['name']}=={pkg['version']} {pkg['home_page']}"
            elif pkg["status"] == "error":
                errored += f"{pkg['name']}=={pkg['version']} {pkg['home_page']}"
            elif pkg["status"] == "pending":
                pending += f"{pkg['name']}=={pkg['version']} {pkg['home_page']}"
        if len(installed) > 0:
            click.secho("Installed Packages:", fg="bright_green")
            click.secho(installed)
        if len(errored) > 0:
            click.secho("Errored Packages:", fg="bright_red")
            click.secho(errored)
        if len(pending) > 0:
            click.secho("Pending Packages:", fg="purple")
            click.secho(pending)

def diff():
    click.secho(f"Fetching remote endpoints to run diff ...", fg="yellow")
    endpoints = get_endpoints(write=False)
    unchanged = True
    for project in endpoints.keys():
        for endpoint in endpoints[project]:
            # grab contents of file
            # if file not there, they need to pull
            try:
                local_file = open(
                    f"{root}/BrevDev/{project}/{endpoint['name']}.py", "r"
                )
                local_code = local_file.read()
                local_file.close()
            except:
                click.secho(
                    f"Endpoint {project}/{endpoint['name']} doesn't exist locally and needs to be fetched.",
                    fg="yellow",
                )
                break

            diff = difflib.ndiff(
                endpoint["code"].splitlines(keepends=True),
                local_code.splitlines(keepends=True),
            )
            output = str("".join(diff))
            total_changes = 0
            changes = []
            for line in output.split("\n"):
                if len(line) == 0:
                    continue
                elif line[0] == "-":
                    # click.secho(f"\t{line}", fg="bright_red")
                    changes.append((f"\t{line}", "bright_red"))
                    total_changes += 1
                elif line[0] == "+":
                    # click.secho(f"\t{line}", fg="bright_green")
                    changes.append((f"\t{line}", "bright_green"))
                    total_changes += 1
                else:
                    continue

            if total_changes != 0:
                unchanged = False
                click.secho(f"Diff for {project}/{endpoint['name']}:", fg="yellow")
                for change in changes:
                    click.secho(change[0], fg=change[1])
    
    if unchanged:
        click.secho(f"No changes. You're synced with remote.", fg="bright_green")

def new(type,name):
    try:
        if type == "project":
            click.secho(f"Creating project {name}", fg="green")
            spin.start()
            response = create_new_project(name)
            get_projects(write=True)
            spin.stop()
            set_active_project(response['project'])
            create_project_dir(response['project']['name'])
            create_variables_file(response['project']['name'], response['project']['id'])
            create_module_file(response['project']['name'], response['project']['id'], write=True)
            click.secho(f"{type} {name} created successfully.", fg="bright_green")
    except:
        spin.stop()
        click.secho(f"An error occured creating {type} {name}.", fg="bright_red")

def add(type,name):
    try:
        if type == "package":
            click.secho(f"Adding package {name}", fg="green")
            spin.start()
            response = add_package(name)
            spin.stop()
        elif type == "variable":
            value = click.prompt(f"Value for variable {name}?")
            click.secho(f"Adding variable {name}", fg="green")
            spin.start()
            response = add_variable(name, value)
            create_variables_file(get_active_project()['name'],get_active_project()['id'])
            spin.start()
        elif type == "endpoint":
            click.secho(f"Adding endpoint {name}", fg="green")
            spin.start()
            response = add_endpoint(name)
            spin.stop()

        click.secho(f"{type} {name} adding successfully.", fg="bright_green")
    except:
        spin.stop()
        click.secho(f"An error occured adding {type} {name}.", fg="bright_red")

def remove(type,name):
    try:
        spin.start()
        if type == "package":
            packages = get_packages()
            package = [p for p in packages if p["name"] == name]
            if len(package) == 0:
                click.secho(f"{type} {name} does not exist on your project. ", fg="red")
                return
            click.secho(f"Removing package {name}", fg="green")
            response = remove_package(package[0]["id"])
        elif type == "variable":
            variables = get_variables()
            variable = [v for v in variables if v["name"] == name]
            if len(variable) == 0:
                click.secho(f"{type} {name} does not exist on your project. ", fg="red")
                return
            click.secho(f"Removing variable {name}", fg="green")
            response = remove_variable(variable[0]["id"])
            create_variables_file(get_active_project()['name'],get_active_project()['id'])
        elif type == "endpoint":
            endpoint = [e for e in get_endpoint_list() if e["name"] == name]
            if len(endpoint) == 0:
                click.secho(f"{type} {name} does not exist on your project. ", fg="red")
                return
            click.secho(f"Removing endpoint {name}", fg="green")
            response = remove_endpoint(endpoint[0]["id"])
        spin.stop()
        click.secho(f"{type} {name} removed successfully.", fg="green")
    except:
        spin.stop()
        click.secho(f"An error occured removing {type} {name}.", fg="red")
