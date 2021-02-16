from . import helpers
import json
import os

def validate_directory():
    if helpers.get_active_project_dir() == None:
        helpers.not_in_brev_error_message()
        return False
    return True
        # raise click.Abort()


def get_active_project_dir():
    for projdir in helpers.get_all_project_dirs():
        if projdir in os.getcwd():
            return projdir
    return None


def get_active_project(custom_dir=None):
    curr_dir = get_active_project_dir() if custom_dir==None else custom_dir
    with open(f"{curr_dir}/.brev/projects.json", "r") as file:
        active = json.loads(file.read())
        file.close()
        return active
