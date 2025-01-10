import json
import deepdiff
from pprint import pprint

def compare_with_reference(request_path, response_json):
    reference_path = request_path.replace("_query_path", ".json")
    with open(reference_path, "r") as file:
        print(reference_path)
        reference_json = json.load(file)

    diff = deepdiff.DeepDiff(reference_json, response_json)
    # pprint(diff)
    return diff

    
