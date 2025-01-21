
# Normal/simple REST APIs:
```
    /bouton-density
    /contribution
    /experimental_bouton_density
    /experimental_neuron_density
    /experimental_synapses_per_connection
    /organization
    /person
    /reconstructed-neuron-morphology/
    /reconstruction_morphology
    /role
```

These have CRUD-able patterns:
    GET /contribution/{id} to get
    POST /contribution/ to create

TODO:
    What are the ACLs on these operations?
        contribution
        organization
        person
        role

# List views
The endpoint for returning the listing per type; including faceting
```
    /bouton-density/list
    /reconstructed-neuron-morphology/list
```

Ex:
    GET /reconstructed-neuron-morphology/list?q=foo&brain_region_id=997

Where q string searches across name/description?

Note:
will need to decide how to handle expansion of brain_region_ids, something like how the sonata-position-service works

List View:
    {
      "status": "success"
      "data": [...],
      "pagination": {
        "page": 1,
        "limit": 10,
        "total": 100
      },
      "facets": {
        <aggregation of "columns" in data>
      }
    }

`data` would include the columns that are required for the current FE list view, for now would be hardcoded, but in the future could be part of the query param.

Ex: "data" for MEModel:
      "data": [
        {"name": "...", "description": "...", "mType": "L5TPC", "eType": "STUT"},
        ...
      ],


`facets` would include the columns that are in data, for the cases that make sense (ie: not `name`, `description`, but "types", "regions", "contributors"

Ex: "facets" for MEModel:
      "facets": {
        "mType": {"L5_TPC": 10, "L6_BAC": 1},
        "eType": {"cSTUT": 10, "bAC": 1},
        ...
      }
    
# Special Cases:

## brain-regions/ return the "simplified" hierarchy.json:

* This can also have a query param: with "alternative view" to get a json file with that
* We may want to version this if we expect to have updated atlases

EX:
    {
         "id": 997,
         "acronym": "root",
         "name": "root",
         "color_hex_triplet": "FFFFFF",          # <- if this is used?
         "parent_structure_id": null,            #
         "children": [
              { "id": 997, "acronym": "root", "name": "root", ..., "children": []},
              ...
         ]
    }

GET /brain-regions/{id}: could do this, but not sure it's useful: the full
    json size is ~200k uncompressed, and 20k compressed; having logic on the
    frontend to work w/ this file would be much faster than having to hit the
    API each time to get 

To be looked at more:
```
    files/
    experimental-data/_count
    model-data/_count
```

# Authorization:
Current model is to have things be either public, or private to a lab/project.
As such, results returned will be gated by this, based on the logged in user.
