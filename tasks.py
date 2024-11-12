#!/usr/bin/env python3

import json
import os
import re
import typing

import invoke
import jsondiff


JsonCallableType = typing.Callable[[str, dict], dict]


WINDOWS_SERVER_PATH = os.path.join(
    "C:\\",
    "Program Files (x86)",
    "Steam",
    "steamapps",
    "common",
    "Eco",
    "Eco_Data",
    "Server",
)
LINUX_SERVER_PATH = os.path.join(
    "/home",
    "kai",
    ".local",
    "share",
    "Steam",
    "steamapps",
    "common",
    "Eco",
    "Eco_Data",
    "Server",
).replace("\\", "/")


def server_path():
    if "windows" in os.getenv("OS", "").lower():
        return WINDOWS_SERVER_PATH
    else:
        return LINUX_SERVER_PATH


def process_configs(base_path: str, func: JsonCallableType, verbose=True) -> None:
    configs = os.listdir(os.path.join(base_path, "Configs"))
    if verbose:
        print(f"Running {func.__name__}")
    for config in configs:
        path = os.path.join(base_path, "Configs", config)

        # Skip stuff that's not likely to be JSON
        likely_json = path.endswith("eco") or path.endswith("template")
        definitely_not_json = "Holiday" in path or "Profanity" in path
        if not likely_json or definitely_not_json:
            continue

        if verbose:
            print(f"\t{path}")
        with open(path, "r", encoding="utf-8") as file:
            data_str = file.read()
            data_json = json.loads(data_str)
            data_json = func(path, data_json)
            data_str = json.dumps(data_json, indent=2, sort_keys=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(data_str)


class RegexException(Exception):
    pass


@invoke.task
def format_json(_: invoke.Context, verbose=True):
    # no-op function to simply format the JSON
    def _format_json(_, json_data: dict) -> dict:
        return json_data

    process_configs("", _format_json, verbose=verbose)
    process_configs(server_path(), _format_json, verbose=verbose)


@invoke.task
def show_diffs(_: invoke.Context):
    format_json(_, verbose=False)

    pattern = re.compile(r".*Configs[\\/](\w+)\.eco")
    print("Showing diffs")

    def _show_diffs(path, new_data: dict) -> dict:
        if match := re.match(pattern, path):
            config = match.group(1)

            # skip the WorldGenerator diff, it's not useful
            if "WorldGenerator" in config:
                return new_data

            print(f"\tDiffing {config}")

            # read in the original data
            original_path = os.path.join(server_path(), "Configs", f"{config}.eco.template")
            with open(original_path, "r", encoding="utf-8") as file:
                original_data = json.loads(file.read())

            # write back the original data, as a reference
            with open(os.path.join("Configs", config + ".original.json"), "w", encoding="utf-8") as file:
                file.write(json.dumps(original_data, indent=2, sort_keys=True))

            # diff the two, write the diff to a file
            diff_json = jsondiff.diff(original_data, new_data, marshal=True, dump=True)

            # json dump, load, and dump again to get a pretty print
            diff_str = json.dumps(json.loads(diff_json), indent=2, sort_keys=True)

            # write the diff to a file
            with open(os.path.join("Configs", config + ".diff.json"), "w", encoding="utf-8") as file:
                file.write(diff_str)

        else:
            raise RegexException(f"Could not match {path}")
        return new_data

    process_configs("", _show_diffs, verbose=False)
