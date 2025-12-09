import json
import parser
import os

def find_json_files(directory):
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


def parse_json_file(json_file):
    with open(json_file, "r",encoding="utf-8" ) as file:
        data = json.load(file)
    return data


    