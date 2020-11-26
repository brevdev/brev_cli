import click
from pyfiglet import Figlet
import os
from . import commands
from . import helpers
# def do_upgrade():
#     print "Performing upgrade"

# def bypass_upgrade_check(func):
#     setattr(func, "do_upgrade_check", False)
#     return func

# @click.group()
# @click.pass_context
# def common(ctx):
#     sub_cmd = ctx.command.commands[ctx.invoked_subcommand]
#     if getattr(sub_cmd, "do_upgrade_check", True):
#         do_upgrade()



@click.group()
# @click.pass_context # not sure if this is needed
def cli():
    """\b
    Welcome to BrevDev 🥞

    This project is in alpha. If you run into any bugs or issues, please just text us directly:
    (415) 818-0207

    (you can try calling, no promises.)

    """
    pass
    # if helpers.get_active_project_dir() == None:
    #     helpers.not_in_brev_error_message()
    #     raise click.Abort()


cli.add_command(commands.init)
cli.add_command(commands.add)
cli.add_command(commands.list)
cli.add_command(commands.diff)
cli.add_command(commands.run)
cli.add_command(commands.status)
cli.add_command(commands.login)
cli.add_command(commands.override)
cli.add_command(commands.remove)
cli.add_command(commands.logs)
cli.add_command(commands.log)
