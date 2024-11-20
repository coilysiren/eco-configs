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

            # skip diffs that aren't useful
            if ("Network" in config) or ("Maintenance" in config):
                return new_data

            print(f"\tDiffing {config}")

            # read in the original data
            original_path = os.path.join(server_path(), "Configs", f"{config}.eco.template")
            with open(original_path, "r", encoding="utf-8") as file:
                original_data = json.loads(file.read())

            # write back the original data, as a reference
            with open(os.path.join("Configs", config + ".original.json"), "w", encoding="utf-8") as file:
                file.write(json.dumps(original_data, indent=2, sort_keys=True))

            # diff the two then dump..
            # ..load, and dump again to get a pretty print
            diff_json = jsondiff.diff(original_data, new_data, marshal=True, dump=True)
            diff_str = json.dumps(json.loads(diff_json), indent=2, sort_keys=True)

            # write the diff to a file
            with open(os.path.join("Configs", config + ".diff.json"), "w", encoding="utf-8") as file:
                file.write(diff_str)

        else:
            raise RegexException(f"Could not match {path}")
        return new_data

    process_configs("", _show_diffs, verbose=False)


@invoke.task
def reset_worldgen(_: invoke.Context):
    with open(os.path.join(server_path(), "Configs", "WorldGenerator.eco.template"), "r", encoding="utf-8") as file:
        data = file.read()

    with open(os.path.join("Configs", "WorldGenerator.eco"), "w", encoding="utf-8") as file:
        file.write(data)


@invoke.task
def expand_deposits(_: invoke.Context):
    example_data = {
        "TerrainModule": {
            "$id": "11",
            "$type": "Eco.WorldGenerator.TerrainModule, Eco.WorldGenerator",
            "Modules": [
                {
                    "$id": "12",
                    "$type": "Eco.WorldGenerator.BiomeTerrainModule, Eco.WorldGenerator",
                    "BiomeName": "Grassland",
                    "Module": {
                        "$id": "13",
                        "BlockDepthRanges": [
                            {
                                "BlockType": {"Type": "Eco.Mods.TechTree.SandstoneBlock, Eco.Mods"},
                                "SubModules": [
                                    {
                                        "$type": "Eco.WorldGenerator.DepositTerrainModule, Eco.WorldGenerator",
                                        "BlockType": {"$id": "48", "Type": "Eco.Mods.TechTree.IronOreBlock, Eco.Mods"},
                                        "DepositDepthRange": {"max": 60, "min": 15},
                                        "DepthRange": {"max": 60, "min": 53},
                                    }
                                ],
                            }
                        ],
                    },
                }
            ],
        }
    }

    def _expand_deposits(sub_module: dict) -> dict:
        if "DepthRange" in sub_module:
            if sub_module["DepthRange"]["min"] >= 20:
                sub_module["DepthRange"]["min"] -= 15
            if sub_module["DepthRange"]["max"] >= 20:
                sub_module["DepthRange"]["max"] = min(sub_module["DepthRange"]["max"] + 20, 200)

        if "DepositDepthRange" in sub_module:
            if sub_module["DepositDepthRange"]["min"] >= 5:
                sub_module["DepositDepthRange"]["min"] = max(sub_module["DepthRange"]["min"] - 5, 5)
            sub_module["DepositDepthRange"]["max"] = min(sub_module["DepthRange"]["max"] + 20, 200)

        return sub_module

    with open(os.path.join("Configs", "WorldGenerator.eco"), "r", encoding="utf-8") as file:
        world_data = json.loads(file.read())
        terrain_modules = world_data["TerrainModule"]["Modules"]

        for module in terrain_modules:
            if module["$type"] == "Eco.WorldGenerator.BiomeTerrainModule, Eco.WorldGenerator":
                for block_depth_range in module["Module"]["BlockDepthRanges"]:
                    for sub_module in block_depth_range["SubModules"]:
                        is_deposit = sub_module["$type"] == "DepositTerrainModule"
                        is_ore = "OreBlock" in sub_module["BlockType"].get("Type", "")
                        if is_deposit and is_ore:
                            sub_module = _expand_deposits(sub_module)

    with open(os.path.join("Configs", "WorldGenerator.eco"), "w", encoding="utf-8") as file:
        file.write(json.dumps(world_data, indent=2, sort_keys=True))
