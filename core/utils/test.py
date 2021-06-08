import json


def dump_obj(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


def pp_json(msg):
    """Pretty-printing json formatted strings.

    :param msg: Json-string to pretty print
    :return: None
    """
    json_str = json.loads(msg)
    print(json.dumps(json_str, indent=3))
