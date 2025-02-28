
# Normal/simple REST APIs:
```
    # for `Entity`
    /experimental-bouton-density
    /experimental-neuron-density
    /experimental-synapses-per-connection
    /reconstructed-neuron-morphology/

    /contribution
    /role
    /organization
    /person
```

These have CRUD-able patterns:
    GET /contribution/{id} to get
    POST /contribution/ to create


Note: the organizations will need to be filled in; they include ones that are not yet part of the OBI, so there isn't a one-to-one relationship with what is included virtual lab service.
Future work may include auto-additing organizations when one joins the OBI; alternatively the first time data is created, they could be added.
Currently, `Entity`s are immutable, with the exception of the `authorized_public` property (see Authorization).

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
    "page_size": 10,
    "total_items": 100
  }
}
```
`data` would include the columns that are required for the current FE list view, for now would be hardcoded, but in the future could be part of the query param.
Note that `page` starts at 1.

Note:
will need to decide how to handle expansion of brain\_region\_ids, something like how the sonata-position-service works

## Search and filtering

If there is a query param `search`, it searches across text fields within the results of the query, for instance the description.
Furthermore, fields of the particular entity being searched for can be specified with their exact matching value.

Ex:
```
GET /reconstruction_morphology/?search=foo&species__name=Mus%20musculus
```

The return payload is the same as above, except the `data` only includes matches with `foo` and the species name matching `Mus musculus`.
Its pagination data reflects the result of the filters.
The facets cover the results of the full query, not just the pagination.

## Faceting

Additional facet statistics are included on entity endpoints:

EX: "facets" for reconstructed-neuron-morphology:
```
    "species": [
        {
            id: 1,
            label: "Mus musculus",
            count: 3508
        },
        [...]
    ],
    "strain": [
        {
            id: 5,
            label: "C57BL/6J",
            count: 31
        },
    [...]
    ]
    "mtype": [
        {
         id: 3
         label: "L5TPC",
         count: 339
        },
    ]
    .....
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
         "parent_structure_id": null,          # <- if this is used?
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


To be looked at more:
```
    files/
    experimental-data/_count
    model-data/_count
```

# Authorization:
Current model is to have `Entity`s (ex: `EModel`, `ReconstructionMorphology`, etc) be either public, or private to a project.
As such, results returned will be gated by this, based on the logged in user.
The frontend will have to supply the current user's Bearer token, as well as the current lab and project:

```
    Authorization: Bearer <token>
    virtual-lab-id: <virtual lab UUID>
    project-id: <project UUID>
```

The service will check that the user does indeed belong to the supplied project, and then filter the results to include only public ones, along with those in the project.
By default, an `Entity` is private, and marked as being owned by the `project-id` supplied in the header.
Members of the owning project can set the `authorized_public` on creation, to mark the `Entity` as public.
In addition, this value can be changed by using the `PATCH` operation.
Once an `Entity` is made public, it can not be made private, since it could be already shared/used by others.
