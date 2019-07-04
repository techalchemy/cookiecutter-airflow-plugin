# -*- coding=utf-8 -*-
# Copyright (c) {% now 'local', '%Y' %} {{ cookiecutter.author }}

from airflow.plugins_manager import AirflowPlugin


class {{ cookiecutter.plugin_type.title().replace(' ', '') }}Plugin(AirflowPlugin):
    """Apache Airflow {{ cookiecutter.plugin_type.title() }} Plugin."""

    name = "{{ cookiecutter.plugin_type.lower().replace(' ', '') }}_plugin"
    hooks = []
    operators = []
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []
