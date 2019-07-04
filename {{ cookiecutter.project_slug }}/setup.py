# Copyright (c) {% now 'local', '%Y' %} {{ cookiecutter.author }} <{{ cookiecutter.email }}>
# MIT License <https://choosealicense.com/licenses/mit>

import pathlib

import setuptools

setuptools.setup(
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    package_data={"": ["LICENSE*", "README*"]},
    entry_points={
        "airflow.plugins": [
            "{{ cookiecutter.plugin_type.lower().replace(' ', '') }}_plugin = {{ cookiecutter.package_name }}.plugin:{{ cookiecutter.plugin_type.title().replace(' ', '') }}Plugin"
        ]
    },
)
