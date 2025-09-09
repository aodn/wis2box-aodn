import inspect
import re
import glob
import importlib
import tempfile
from pathlib import Path
from os import path, getcwd, environ
from pprint import pformat
from types import SimpleNamespace
import sys
import yaml
import prefect.context
from prefect.settings import PREFECT_API_URL


class FlowConfig(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.Config = None

    def set_config(self, config):
        self.Config = config
        if "overrides" in config:
            for flow, values in config["overrides"].items():
                self.Config.update(values)
        if "global" in config and config["global"] is not None:
            self.Config.update(config["global"])

    def get(self, key, default=None):
        return self.Config.get(key, default)

    def __str__(self):
        return pformat(self.Config, indent=2, sort_dicts=False)

    def __setitem__(self, key, value):
        self.Config[key] = value

    def __getitem__(self, item):
        return self.Config[item]


def create_temp_config_dir():
    # creates a temp directory to store the lazy loaded config in
    # call this in the main/root flow eg td = create_temp_config_dir()
    if prefect.runtime.flow_run.parent_flow_run_id is None:
        td = tempfile.TemporaryDirectory(prefix=f"{prefect.runtime.flow_run.id}.")
        environ["PREFECT_CONFIG_TEMP_DIR"] = td.name
        # Return the TemporaryDirectory object so the directory is not deleted in garbage collection
        return td
    else:
        return None


def store_flow_run_config(config):
    # creates the temp file for the flow run
    # we need this to persist across sub-flow runs so no context manager is used

    td = create_temp_config_dir()

    flow_run_config = tempfile.NamedTemporaryFile(dir=environ.get("PREFECT_CONFIG_TEMP_DIR"),
                                                  prefix=f"{prefect.runtime.flow_run.id}.", delete=False)
    outfile = open(flow_run_config.name, 'w')
    yaml.dump(config, outfile, default_flow_style=False)

    config = FlowConfig()
    config.td = td
    config.flow_run_config_name = flow_run_config.name

    return config


def get_module_spec(module: str):

    cwd = getcwd()
    if path.exists(module):
        # os.path.dirname(__file__) is relative to cwd with debugger, but absolute without
        relative_dirname = path.dirname(module).replace(f"{cwd}/", "")
        module = f"{relative_dirname.replace('/', '.')}.{Path(module).stem}"

    # Prefect will change the cwd (and not the sys.path) depending on deployment
    if cwd not in sys.path:
        sys.path.append(cwd)
    module_spec = importlib.util.find_spec(module)

    return module_spec


def get_flow_config_key(module_spec) -> str:
    module_base_name = module_spec.name.replace(f"{module_spec.parent}.", "")
    flow_config_key = f"{module_base_name}.{prefect.runtime.flow_run.flow_name}"
    return flow_config_key


def get_flow_config_key_from_module(module: str) -> str:
    module_spec = get_module_spec(module)
    flow_config_key = get_flow_config_key(module_spec)
    return flow_config_key


def load_flow_config(module: str, config_file: str) -> dict:
    if path.exists(config_file):
        module_spec = get_module_spec(module)
        config_key = get_flow_config_key(module_spec)
        flow_config = load_config_at_key(config_key, config_file)
        if flow_config is None:  # There is no config for the module
            flow_config = {}
    else:
        flow_config = {}

    return flow_config


def load_parent_config() -> dict:
    if prefect.runtime.flow_run.parent_flow_run_id and "PREFECT_CONFIG_TEMP_DIR" in environ:
        # Load the parent flow config from temp file if it exists
        parent_id = prefect.runtime.flow_run.parent_flow_run_id
        parent_config_file = glob.glob(f"{path.join(environ.get('PREFECT_CONFIG_TEMP_DIR'), str(parent_id))}.*")[0]
        parent_config = load_config_from_file(parent_config_file)
    else:
        parent_config = {}
    return parent_config

def lazy_load_config(config_file: str = None):
    # Load part of config needed when the flow is run.
    # A config.yaml file is required in the directory that contains the module.

    # Keys are of the form:
    #   module.flow

    # How it works.
    #   Load config for the module if it exists
    #   Check for parent flow run id  (prefect.runtime.flow_run.parent_flow_run_id)
    #      If None:
    #           Load the root config for the profile that is in use
    #      If there is a parent:
    #           Load the parent flow config
    #      Merge module config with the root/parent config
    #           Apply global config
    #           Apply overrides for current flow
    #           Apply all other overrides
    #      Save the merged config in temp file using the prefect.runtime.flow_run.id in the file name

    #   Merging rules:
    #     "global" values do not belong to any particular flow or task.
    #     "global" values should be accessible in every flow and task run. ie they should only be in the root config
    #     "global" values cannot be overridden
    #     values can override values in descendent configs if their keys match

    #   Values should be passed to library functions as parameters (ie they have no config.yaml)

    module = inspect.stack()[1].filename
    module_spec = get_module_spec(module)
    flow_path = path.dirname(path.realpath(module_spec.origin))

    if config_file is None:
        config_file = "config"

    config_file_path = path.join(flow_path, f"{config_file}.yaml")

    flow_config = load_flow_config(module, config_file_path)
    parent_config = load_parent_config()

    if "global" in parent_config:
        flow_config.update({"global": parent_config["global"]})

    if "overrides" in parent_config:
        flow_config.update({"overrides": parent_config["overrides"]})
        flow_config_key = get_flow_config_key_from_module(module)
        if flow_config_key in parent_config["overrides"]:
            flow_config.update(parent_config["overrides"][flow_config_key])

    config = store_flow_run_config(flow_config)
    config.flow_config = flow_config
    config.set_config(flow_config)

    return config


def load_config_from_file(config_file: str = "config.yaml"):
    with open(config_file, "r") as yamlfile:
        config = yaml.safe_load(yamlfile)
    return config


def load_root_config(config_file: str = "config.yaml"):
    profile = prefect.context.root_settings_context().profile.name
    if re.search("^development-.*$", profile):
        profile = "development"
    else:
        workspaces = load_config_at_key("workspaces", config_file)
        workspace_id = re.match("^.*workspaces/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
                                PREFECT_API_URL.value()).group(1)
        profile = workspaces[workspace_id]
    current_config = load_config_at_key(profile, config_file)
    return current_config


def load_config_at_key(key, config_file: str = "config.yaml"):
    all_configs = load_config_from_file(config_file)
    if key in all_configs:
        current_config = all_configs[key]
        if current_config is None:  # The key exists but it is an empty dict
            current_config = {}
    else:
        current_config = all_configs
    return current_config
