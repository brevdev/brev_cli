import click
from pyfiglet import Figlet
from . import commands


@click.group()
def cli():
    """\b
    Welcome to BrevDev 🥞

    """
    pass


cli.add_command(commands.login)
cli.add_command(commands.init)
cli.add_command(commands.override)
cli.add_command(commands.new)
cli.add_command(commands.add)
cli.add_command(commands.remove)
cli.add_command(commands.diff)
cli.add_command(commands.list)
cli.add_command(commands.run)
cli.add_command(commands.set)
cli.add_command(commands.status)
