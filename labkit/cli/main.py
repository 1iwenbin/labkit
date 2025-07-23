#!/usr/bin/env python3
import typer
from labkit.cli.commands.edit.main import edit
from labkit.cli.commands.validate.main import validate
from labkit.cli.commands.run.main import app as run_app
from labkit.cli.commands.init.main import init

app = typer.Typer(help="Labbook: Workflow-oriented CLI for experiment projects")

app.command()(init)
app.command()(edit)
app.command()(validate)
app.add_typer(run_app, name="run", help="运行实验")

if __name__ == "__main__":
    app() 