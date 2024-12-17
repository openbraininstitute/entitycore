import os
import json
TEST_SEARCH_END_POINT = '/nexus/v1/views/bbp/atlas/https://bbp.epfl.ch/data/bbp/atlas/es_aggregate_view_tags_v1.1.0_v2.2.4'
TEST_SBO_END_POINT = '/nexus/v1/search/query/suite/sbo'
def get_body(name):
    with open(os.path.join(os.path.dirname(__file__), f"data/{name}.json"), "r") as f:
        return json.load(f)
    