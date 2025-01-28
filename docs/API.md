
# Normal/simple REST APIs:
```
    /bouton-density
    /contribution
    /experimental-bouton-density
    /experimental-neuron-density
    /experimental-synapses-per-connection
    /organization
    /person
    /reconstructed-neuron-morphology/
    /role
```

These have CRUD-able patterns:
    GET /contribution/{id} to get
    POST /contribution/ to create


Note: the organizations will need to be filled in; they include ones that are not yet part of the OBI, so there isn't a one-to-one relationship with what is included virtual lab service.
Future work may include auto-additing organizations when one joins the OBI; alternatively the first time data is created, they could be added.

TODO:
    What are the ACLs on these operations?
        contribution
        organization
        person
        role

# List views
The endpoint for returning the listing per type; including faceting; if no query parameter is passed, the traditional list view will be returned (ie: no filtering)
```
    /bouton-density/
    /reconstructed-neuron-morphology/
```

Ex:
```
GET /reconstructed-neuron-morphology/
```

Would return:
```
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```
`data` would include the columns that are required for the current FE list view, for now would be hardcoded, but in the future could be part of the query param.

Note:
will need to decide how to handle expansion of brain_region_ids, something like how the sonata-position-service works

## Search and filtering

If there is a query param `search`, it searches across text fields within the results of the query, for instance the description.
Furthermore, fields of the particular entity being searched for can be specified with their exact matching value.

Ex:
```
GET /reconstructed-neuron-morphology/search=foo&brain_region_id=997
```

The return payload is the same as above, except the `data` only includes matches with `foo` and the region being 997.
Its pagination data reflects the result of the filters.

## Faceting

Additional facet statistics can be included by using the `facets` keyword: `[...]&facets=mtype,etype`

```
"facets": {
<aggregation of "columns" in data>
}
```

"facets" for MEModel: `[...]&facets=mtype,etype`
```
"facets": {
    "mType": {"L5_TPC": 10, "L6_BAC": 1},
    "eType": {"cSTUT": 10, "bAC": 1},
    ...
}
```
    
# Special Cases:

## brain-regions/ return the "simplified" hierarchy.json:

* This can also have a query param: with "alternative view" to get a json file with that
* We may want to version this if we expect to have updated atlases

EX:
    {
         "id": 997,
         "acronym": "root",
         "name": "root",
         "color_hex_triplet": "FFFFFF",
         "parent_structure_id": null,            # shouldn't be necessary, might be removed
         "children": [
              { "id": 997, "acronym": "root", "name": "root", ..., "children": []},
              ...
         ]
    }

GET /brain-regions/{id}: could do this, but not sure it's useful: the full
    json size is ~200k uncompressed, and 20k compressed; having logic on the
    frontend to work w/ this file would be much faster than having to hit the
    API each time to get 

Future work would include using ltree from postgresql to make doing lookups and such easier: https://www.postgresql.org/docs/current/ltree.html 


# Authorization:
Current model is to have things be either public, or private to a lab/project.
As such, results returned will be gated by this, based on the logged in user.
The frontend will have to supply the current user's Bearer token, as well as the current lab and project.
These will have to be passed as headers in the request.
The service will check that the user does indeed belong to this lab and project, and then filter the results to include only public ones, along with those in the lab and project.


# Files:

For files, there are two main use cases:
1) Downloading them via a web API
2) Mounting them in some fashion on the cluster

The former is likely to be smaller files (such as morphologies, ephys traces, images and reports \[ie: pdf\], etc).
The later is things like circuit data, which can be large, and may not include only individual files, rather a directory.

## Semantics

* An entity (eg: morphology), can be associated with multiple files
* A file is associated with only one Entity, this also means that a `Folder` owns all the contents, and no other Entity points to anything within the folder
* A file has a type associated with it; at first approximation these are MIME types, however there are many vendor specific ones that will have to be handled
* Once registered, a file is immutable; it cannot be changed or replaced
* A file inherits its Authorization from the entity to which it is associated

## API
* When getting an entity, the `?expand-files=True` query parameter can be used.
  This will include add the following payload to the request:
  ```
  {"filename.ext": {
    "url": 
    "type": "aMimetype/like.string",
    "size": 314159, # in bytes
    "sha1": "c7102fb8700511782990db9ac149b28cb76c79f0",
   },
   "filename.swc": {
    "url": 
    "type": "application/swc",  # or should it be application/octet-stream or `application/vnd.swc`
    "size": 271828, # in bytes
    "sha1": "571a7182818284590450db9ac718281828459045",
   }
   "foldername": {
    "url": "/some/path/on/cluster",
    "type": "application/x-directory",
    "size": 0,   # Not applicable
    "sha1": "0", # Not applicable
   }
  }
  ```

* The `url` supplied with the result can be used to download the file
* For folder types there no way to list or download the contents

## Staging
* On the cluster, a folder is automatically staged, as it's path should be accessible.
* For files; either the file is pulled down through the API, via the `url` property, or there will need to be a way to map

## Configurations

The frontend currently stores `configuration` data (ex: `cell-composition`, `connectome-model`) in NEXUS.


# To be looked at more:
```
    experimental-data/_count
    model-data/_count
```
