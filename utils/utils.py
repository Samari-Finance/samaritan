import json
import os


def read_api(api_key_file):
    if not os.path.exists(api_key_file):
        api_key_file = os.path.dirname(os.getcwd()) + '/' + api_key_file
    key_file = open(api_key_file)
    return key_file.read()


def pp_json(msg):
    json_str = json.loads(msg)
    print(json.dumps(json_str, indent=3))
