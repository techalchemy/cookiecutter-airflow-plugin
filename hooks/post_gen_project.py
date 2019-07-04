# Copyright (c) 2019 Dan Ryan <dan@danryan.co>
# ISC License <https://opensource.org/licenses/isc>

import os
import shutil

if "{{ cookiecutter.initialize_git_repository }}".strip().lower() == "y":
    os.system("git init")

if "{{ cookiecutter.build_virtual_environment }}".strip().lower() == "y":
    python_path = shutil.which("python3.7")
    pipenv_command = "pipenv install --dev"
    if python_path:
        pipenv_command = pipenv_command + f" --python {python_path}"
    os.system(pipenv_command)

if "{{ cookiecutter.initialize_pre_commit }}".strip().lower():
    os.system("pipenv run pre-commit install")
