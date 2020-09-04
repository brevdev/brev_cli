import click
from pyfiglet import Figlet
from . import commands


@click.group()
def cli():
    """\b
    Welcome to BrevDev 🥞

    This project is in alpha. If you run into any bugs or issues, please just text us directly:
    (415) 818-0207

    (you can try calling, no promises.)

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
