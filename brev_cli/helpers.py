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
                    "Please login with 'brev login' or create an account at app.brev.dev",
                    fg="green",
                ),
            )
            # res = yes_no_prompt()
            # if res:
            #     init_home()
            #     pull(entire_dir=True)

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

def init_necessary_files():
    with open(f"{root}/.brev/active_projects.json", "w") as file:
        file.write(json.dumps([]))
        file.close()

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


def get_endpoints(write=False, init=False, custom_dir=None):
    
    dir = get_active_project_dir() if custom_dir==None else custom_dir
    
    # if initializing: just create the file with an empty list
    if init:
        with open(f"{dir}/.brev/endpoints.json", "w") as file:
            file.write(json.dumps([]))
            file.close()
    
    # make a fetch
    projects = BrevAPI(config.api_url).get_projects()
    endpoints = BrevAPI(config.api_url).get_endpoints()
    
    # organize data to list of endpoints
    activeProject = get_active_project(custom_dir=dir)
    eps = [e for e in endpoints['endpoints'] if e['project_id']==activeProject['id']]
    if write:
        with open(f"{dir}/.brev/endpoints.json", "w") as file:
            file.write(json.dumps(eps))
            file.close()
    
    return eps

def create_projects_file(name=None, custom_dir=None):
    dir = get_active_project_dir() if custom_dir==None else custom_dir
    projects = BrevAPI(config.api_url).get_projects()
    matchedProject = [p for p in projects["projects"] if p['name']==name]
    with open(f"{dir}/.brev/projects.json", "w") as file:
        file.write(json.dumps(matchedProject[0]))
        file.close()
        return matchedProject[0]


def add_endpoint(name):
    endpoints = []
    dir = get_active_project_dir()
    with open(f"{dir}/.brev/endpoints.json", "r") as file:
        endpoints = json.loads(file.read())

    endpoint = BrevAPI(config.api_url).add_endpoint(
        name, get_active_project()["id"]
    )["endpoint"]
    endpoints.append(endpoint)
    with open(f"{dir}/.brev/endpoints.json", "w") as file:
        file.write(json.dumps(endpoints))
        file.close()
    create_endpoint_file(endpoint, get_active_project()["name"] ,dir)
    return endpoint


def remove_endpoint(id):

    dir = get_active_project_dir()
    endpoints = []
    with open(f"{dir}/.brev/endpoints.json", "r") as file:
        endpoints = json.loads(file.read())

    endpoint = BrevAPI(config.api_url).remove_endpoint(id)

    updated_endpoints = [e for e in endpoints if not e["id"] == id]
    removedEP = [e for e in endpoints if e["id"] == id]

    with open(f"{dir}/.brev/endpoints.json", "w") as file:
        file.write(json.dumps(updated_endpoints))
        file.close()
    remove_endpoint_file(removedEP[0], get_active_project()["name"])
    return endpoint

def get_endpoint_list():
    curr_dir = get_active_project_dir()
    if curr_dir==None:
        return []
    # active_project = get_active_project()["id"]
    with open(f"{curr_dir}/.brev/endpoints.json", "r") as myfile:
        endpoints = json.loads(myfile.read())
        myfile.close()
        return [ep for ep in endpoints]


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


def create_endpoint_file(endpoint, project, dir):
    if not os.path.isfile(f"{dir}/{endpoint['name']}.py"):
        with open(f"{dir}/{endpoint['name']}.py", "w") as file:
            file.write(endpoint["code"])
            file.close()
        # click.secho(
        #     f"\tCreated ~🥞/{endpoint['name']}.py!",
        #     fg="bright_green",
        # )
    else:
        with open(f"{dir}/{endpoint['name']}.py", "w") as file:
            file.write(endpoint["code"])
            file.close()
        # click.secho(
        #     f"\t ~🥞/{endpoint['name']}.py has been updated ",
        #     fg="bright_green",
        # )


def remove_endpoint_file(endpoint, project):
    dir = get_active_project_dir()

    if not os.path.isfile(f"{dir}/{endpoint['name']}.py"):
        raise BrevError(f"Endpoint {endpoint['name']} does not exist or isn't on this machine.")
    else:
        os.remove(f"{dir}/{endpoint['name']}.py")
        # click.echo(f"\t ~🥞/{endpoint['name']}.py has been removed")


def create_module_file(project_name, project_id, write=False, custom_dir=None):
    curr_dir = get_active_project_dir() if custom_dir==None else custom_dir
    modules = BrevAPI(config.api_url).get_modules()
    module = [m for m in modules["modules"] if m["project_id"] == project_id]
    if len(module) == 0:
        return
    module = module[0]
    file_content = ""
    if module["source"] == "":
        file_content = f"# no shared code yet. Code written here is accessible by every endpoint in this project {project_name}"
    else:
        file_content = module["source"]
    
    path = os.path.join(curr_dir, "shared.py")
    if not os.path.isfile(path):
        with open(path, "w") as file:
            file.write(file_content)
            file.close()
        click.secho(
            f"\tCreated ~🥞/shared.py",
            fg="bright_green",
        )
    else:
        with open(path, "w") as file:
            file.write(file_content)
            file.close()
        click.secho(
            f"\t~🥞/shared.py has been updated ",
            fg="bright_green",
        )


def get_logs(type, id):
    response = BrevAPI(config.api_url).get_logs(type, id)
    return response["logs"]


def create_new_project(project_name):
    response = BrevAPI(config.api_url).create_project(project_name)
    return response

def update_module(source, project_id=None):
    if project_id == None:
        curr_dir = get_active_project_dir()
        project_id = get_active_project()['id']
    
    # get matched module
    modules = BrevAPI(config.api_url).get_modules()
    module = [m for m in modules["modules"] if m['project_id']==project_id][0]
    
    # update the module
    response = BrevAPI(config.api_url).update_module(module['id'], source)

    return response

def create_variables_file(project_name, project_id, custom_dir=None):
    curr_dir = get_active_project_dir() if custom_dir==None else custom_dir
    variables = BrevAPI(config.api_url).get_variables(project_id)
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


def get_active_project(custom_dir=None):
    curr_dir = get_active_project_dir() if custom_dir==None else custom_dir
    with open(f"{curr_dir}/.brev/projects.json", "r") as file:
        active = json.loads(file.read())
        file.close()
        return active


def get_all_project_dirs():
    with open(f"{root}/.brev/active_projects.json", "r") as file:
        all_dirs = json.loads(file.read())
        return all_dirs


def print_response(response):
    msg_color = "green" if str(response.status_code )[0] == "2" else "red"
    click.echo(
        click.style("\nStatus Code: ", fg=msg_color) +
        f"{response.status_code}"
    )
    notFound = f"{response.status_code}" == "404"
    headers = response.headers
    response = response.json()
    click.echo(
        click.style("\nResponse: \n", fg=msg_color) +
        f"{response}"
    )
    try:
        stdout = urlparse.unquote(headers['x-stdout'])
        click.echo(
            click.style("\nStandard Out: \n", fg=msg_color) +
            f"{stdout}"
        )
    except:
        pass


    if notFound:
        click.secho("The endpoint URL doesn't exist. Maybe you changed the URL?", fg="bright_red")
        click.secho("Run 'brev refresh' to refresh your endpoints locally.", fg="bright_red")

class BrevError(Exception):
    pass

def add_project_to_list(path):
    # file to copy the paths of active projects
    # try:
    contents = []
    # get contents if file exists
    if os.path.isfile(f"{root}/.brev/active_projects.json"):
        with open(f"{root}/.brev/active_projects.json", "r") as file:
            contents = json.loads(file.read())
            file.close()

    # add new project
    if path in contents:
        raise BrevError("Brev is already initialized in this directory.")
    else:
        contents.append(path)
    # if path not in contents:
    #     contents.append(path)
        

    with open(f"{root}/.brev/active_projects.json", "w") as file:
        file.write(json.dumps(contents))
        file.close()
    # except:
    #     click.echo("An error occured. It's likely our fault.")
    #     click.echo("We couldn't add the project to the global list, but this won't affect your functionality.")

def new(type,name,dir,create=True):
    # try:
    if type == "project":
        verb = "Creating" if create==True else "Cloning"
        click.secho(f"{verb} project {name}", fg="green")
        spin.start()
        response ={}
        if create:
            response = create_new_project(name)
            response = response['project']
        else: # fetch it from the server
            response = BrevAPI(config.api_url).get_projects()
            response = [p for p in response['projects'] if p['name']==name][0]
        create_projects_file(name, custom_dir=dir)
        spin.stop()
        create_variables_file(response['name'], response['id'], dir)
        create_module_file(response['name'], response['id'], write=True, custom_dir=dir)
        click.secho(f"{type} {name} created successfully.", fg="bright_green")
        # Add to a root brev
        add_project_to_list(dir)

    # except:
    #     spin.stop()
    #     click.secho(f"An error occured creating {type} {name}.", fg="bright_red")


def not_in_brev_error_message():
    click.echo("Not in active Brev directory. Please go to an active Brev directory or run 'brev init'")
    all_dirs = get_all_project_dirs()
    if len(all_dirs) == 0:
        click.echo("\nHave you created a brev project yet? Run 'brev init' in a project to make it live with Brev!")
    else:
        click.echo("\nThese are active Brev directories: ")
        for dir in all_dirs:
            click.echo(f"\t{dir}")

def get_active_project_dir():
    for projdir in get_all_project_dirs():
        if projdir in os.getcwd():
            return projdir
    return None
    # should we do the below lines here??
    # not_in_brev_error_message()
    # click.Abort()
    
def get_remote_only_projects():
    remote_projects = BrevAPI(config.api_url).get_projects()
    local_projects = [path.split("/")[-1] for path in get_all_project_dirs()]
    
    remote_only_projects = [p for p in remote_projects['projects'] if p['name'] not in local_projects]

    return remote_only_projects


####################################################
##          CLI COMMANDS (not helpers)            ##
####################################################
# brev override local
def pull(entire_dir=False):
    click.echo(click.style("... overriding your local with remote", fg="yellow"))
    curr_dir = get_active_project_dir()
    
    endpoints = get_endpoints(write=True)
    project = get_active_project()
    
    # update non-endpoints
    create_variables_file(project['name'], project['id'])
    create_module_file(project['name'], project['id'], write=True)
    
    # update endpoints
    for endpoint in endpoints:
        if endpoint["archived"] != True:
            create_endpoint_file(endpoint, project, curr_dir)

# brev override remote
def push(entire_dir=False):
    click.echo(click.style("... overriding remote with your local", fg="yellow"))
    curr_dir = get_active_project_dir()
    
    try:
        endpoints = get_endpoints(write=True)
        project = get_active_project()
        
        for endpoint in endpoints:
            try:
                local_file = open(
                    f"{curr_dir }/{endpoint['name']}.py", "r"
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
                    f" ~🥞/{endpoint['name']}.py has been pushed! ",
                    fg="bright_green",
                )
            except:
                # the file might not exist locally.
                pass        

        ## udpate shared code. 1 per project (as of this writing)
        try: 
            local_file = open(
                f"{curr_dir}/shared.py", "r"
            )
            shared_code = local_file.read()
            local_file.close()

            update_module(source=shared_code)
            click.secho(
                f" ~🥞/shared.py has been pushed! ",
                fg="bright_green",
            )
        except:
            click.secho(
                f"Could not update ~🥞/shared.py, it might contain a bug.",
                fg="yellow",
            )                

    except requests.exceptions.HTTPError:
        click.secho(
            f"Could not fetch from remote. Please check your internet.", fg="bright_red"
        )

# brev status
def status():
    curr_dir = get_active_project_dir()
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

# brev run
def run(endpoint,httptype,body,args,stale):
    curr_dir = get_active_project_dir()
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
            f"{curr_dir}/{ep['name']}.py", "r"
        )
        local_code = local_file.read()
        local_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")
        stale = True

    try:
        module_file = open(
            f"{curr_dir}/shared.py", "r"
        )
        shared_code = module_file.read()
        module_file.close()
    except:
        click.secho("The file doesn't exist locally. Proceeding to run from remote", fg="yellow")
        stale = True

    if not stale == True: 
        try:
            spin.start()
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

# brev list
def list(type):
    click.echo("\nYour Brev projects: ")
    for dir in get_all_project_dirs():
        click.echo(f"\t{dir}")
    click.echo("\n")

    curr_dir = get_active_project_dir()
    if not type or type == "project" or type == "endpoint":
        endpoints = get_endpoints(False)
        project = get_active_project()

        click.echo(
            f"Current Project: " + click.style(f"{project['name']}", fg="green")
        )
        click.echo(
            f"API docs: {project['domain']}/docs\n"
        )
        for endpoint in endpoints:
            click.echo(
                f"\tEndpoint:\n\t\tname: {endpoint['name']}\n\t\tid: {endpoint['id']}" 
            )
            click.echo(
                f"\t\tURL: "
                + click.style(f"{project['domain']}{endpoint['uri']}", fg="green")
                + f"\n"
            )


    elif type == "package":
        pkgs = get_packages()
        click.secho(f"Project :")
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
            click.secho("Installed Packages:")
            click.secho(installed)
        if len(errored) > 0:
            click.secho("Errored Packages:")
            click.secho(errored)
        if len(pending) > 0:
            click.secho("Pending Packages:")
            click.secho(pending)

# brev diff
def diff():
    curr_dir = get_active_project_dir()
    click.secho(f"Fetching remote endpoints to run diff ...")
    endpoints = get_endpoints(write=False)    
    unchanged = True
    for endpoint in endpoints:
        # grab contents of file
        # if file not there, they need to pull
        try:
            local_file = open(
                f"{curr_dir}/{endpoint['name']}.py", "r"
            )
            local_code = local_file.read()
            local_file.close()
        except:
            unchanged=False
            click.secho(
                f"Endpoint {endpoint['name']} doesn't exist locally and needs to be fetched.",
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
                changes.append((f"\t{line}", "bright_red"))
                total_changes += 1
            elif line[0] == "+":
                changes.append((f"\t{line}", "bright_green"))
                total_changes += 1
            else:
                continue

        if total_changes != 0:
            unchanged = False
            click.secho(f"Diff for {endpoint['name']}:", fg="yellow")
            for change in changes:
                click.secho(change[0], fg=change[1])

    ## check shared code. 1 per project (as of this writing)
    try: 
        # get current shared code
        local_file = open(
            f"{curr_dir}/shared.py", "r"
        )
        local_shared = local_file.read()
        local_file.close()

        # get remote shared code
        project = get_active_project()
        modules = BrevAPI(config.api_url).get_modules()
        remote_shared = [m for m in modules['modules'] if m["project_id"]==project["id"]]
        if not len(remote_shared) == 0:
            diff = difflib.ndiff(
                remote_shared[0]['source'].splitlines(keepends=True),
                local_shared.splitlines(keepends=True)
            )
            output = str("".join(diff))
            total_changes = 0
            changes = []
            for line in output.split("\n"):
                if len(line) == 0:
                    continue
                elif line[0] == "-":
                    changes.append((f"\t{line}", "bright_red"))
                    total_changes += 1
                elif line[0] == "+":
                    changes.append((f"\t{line}", "bright_green"))
                    total_changes += 1
                else:
                    continue

            if total_changes != 0:
                unchanged = False
                click.secho(f"Diff for shared code:", fg="yellow")
                for change in changes:
                    click.secho(change[0], fg=change[1])
    except:
        click.secho(
            f"Could not check ~🥞/shared.py",
            fg="yellow",
        )       
        
    if unchanged:
        click.secho(f"No changes. You're synced with remote.", fg="bright_green")

# brev add
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
            spin.stop()
        click.secho(f"{type} {name} added successfully.", fg="bright_green")
    except:
        # print(sys.exc_info())
        spin.stop()
        click.secho(f"An error occured adding {type} {name}.", fg="bright_red")

def remove(type,name):
    try:
        spin.start()
        if type == "variable":
            variables = get_variables()
            variable = [v for v in variables if v["name"] == name]
            if len(variable) == 0:
                click.secho(f"{type} {name} does not exist on your project. ", fg="red")
                return
            click.secho(f"Removing variable {name}", fg="green")
            response = remove_variable(variable[0]["id"])
            create_variables_file(get_active_project()['name'],get_active_project()['id'])
        spin.stop()
        click.secho(f"{type} {name} removed successfully.", fg="green")
    except:
        spin.stop()
        click.secho(f"An error occured removing {type} {name}.", fg="red")


def parse_log(log):
    date = log['timestamp'].split("T")[0]
    time = log['timestamp'].split("T")[1]
    datetime = f"{date}/{time}"
    exec_time = f"{log['meta']['wall_time']}ms"

    uri = ""
    if "uri" in log['meta']:
        uri = log['meta']['uri']
    
    status_code = ""
    if "status_code" in log['meta']:
        status_code = log['meta']['status_code']
    
    request_id = ""
    if "request_id" in log['meta']:
        request_id = log['meta']['request_id']

    stdout= ""
    for line in log['stdout'].split("\n"):
        if (len(line) > 0):
            if line[:6] == "[INFO]":
                continue
            else:
                stdout += line + "\n"


    return f"{log['type']} {datetime} {exec_time} {status_code} {request_id} {uri} \n{stdout}"

def logs():

    # gets first output
    prevResponse = ""

    while True:
        response = BrevAPI(config.api_url).get_logs(type="project", id=get_active_project()['id'])
        if not response == prevResponse:
            for log in response['logs'][::-1]:
                click.echo(parse_log(log))
        prevResponse = response

        time.sleep(0.5)


def refresh():
    
    try:
        click.echo("Refreshing local endpoints")
        spin.start()
        get_endpoints(write=True)
        spin.stop();
        click.secho("Refreshing complete!", fg="bright_green");        
    except:
        click.echo("An error occured refreshing your endpoints. Please try again or text (415) 818-0207 for help.")
