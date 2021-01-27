from . import helpers


def validate_directory():
    if helpers.get_active_project_dir() == None:
        helpers.not_in_brev_error_message()
        return False
    return True
        # raise click.Abort()