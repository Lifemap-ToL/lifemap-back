#!/usr/bin/python3

import logging
import json

from config import BUILD_DIRECTORY

logger = logging.getLogger("LifemapBuilder")


def MergeJsons(f1, f2, output):
    with open(BUILD_DIRECTORY / f1, "r") as f:
        data1 = f.read()
    # Here we add a control for the unexpected problem of a "}," being present sometimes
    # at the end of the TreeFeatures2.json file.
    lines = data1.split("\n")
    if lines[-4].find("},") != -1:
        lines.pop(-4)
        data1 = "\n".join(lines)

    with open(BUILD_DIRECTORY / f2, "r") as f:
        data2 = f.read()

    dict1 = json.loads(data1)
    dict2 = json.loads(data2)

    keys_to_keep1 = ["taxid", "sci_name", "zoom", "lat", "lon"]
    dict1_2 = [
        {key: item[key] for key in keys_to_keep1 if key in item} for item in dict1
    ]
    keys_to_keep2 = ["taxid", "ascend"]
    dict2_2 = [
        {key: item[key] for key in keys_to_keep2 if key in item} for item in dict2
    ]

    dict2_map = {d["taxid"]: d for d in dict2_2}

    result = []

    # Iterate over each dictionary in dict1 and merge with the corresponding dictionary from dict2_map
    for d1 in dict1_2:
        taxid = d1.get("taxid")
        if taxid in dict2_map:
            merged_dict = {**d1, **dict2_map[taxid]}
            result.append(merged_dict)

    with open(BUILD_DIRECTORY / output, "w") as f:
        json.dump(result, f, indent=4)


def merge_all():
    MergeJsons("TreeFeatures1.json", "ADDITIONAL.1.json", "TreeFeaturesComplete1.json")
    MergeJsons("TreeFeatures2.json", "ADDITIONAL.2.json", "TreeFeaturesComplete2.json")
    MergeJsons("TreeFeatures3.json", "ADDITIONAL.3.json", "TreeFeaturesComplete3.json")
