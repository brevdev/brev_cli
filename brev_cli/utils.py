def make_header(token):
    header = {"authorization": f"Bearer {token}"}
    return header


def get_method_args_as_dict(locals, should_remove_none=False):
    """
    Use inside a class method to get all method arguments as a dictionary.\n
    Must pass locals() in at top of method\n
    """
    locals.pop("self")
    if should_remove_none:
        for k, v in locals.items():
            if v is None:
                locals.pop(k)
    return locals

