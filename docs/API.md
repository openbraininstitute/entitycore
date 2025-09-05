
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
    GET /experimental-bouton-density/{id} to get
    POST /experimental-bouton-density/ to create
    PATCH /experimental-bouton-density/ to update

API reserved for the service admin group (see [Authorization](#Authorization)) will be prefixed by /admin/ .

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
GET /reconstruction-morphology?search=foo&species__name=Mus%20musculus
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

# Assets:

Assets can be attached to entities.
Assets can either be a single file, or a directory of files.

The following API exists for both single files and directories:

## Get Entity Assets

```
GET    /{entity_type}/{entity_id}/assets
```

## Get Entity Asset Metadata

```
GET    /{entity_type}/{entity_id}/assets/{asset_id}
```

## Delete Entity Asset

```
DELETE /{entity_type}/{entity_id}/assets/{asset_id}
```

The following API exists for single file asset:

## Upload Entity Asset
```
POST   /{entity_type}/{entity_id}/assets
```

## Download Entity Asset

```
GET    /{entity_type}/{entity_id}/assets/{asset_id}/download
```

The following API exists for directory asset:

## Upload Directory

First, `POST` a json payload with the following keys:
```
{
    "name": "name-of-directory",
    "files": [
        "foo.txt",
        "a/b/c.txt",
        "bar/foo.txt"
    ],
    "label": null,
    "meta": null
}

```

to:
```
POST   /{entity_route}/{entity_id}/assets/directory/upload
```

This will return JSON with a `files` key: this includes a mapping of the desired files to be uploaded, and time-limited URLs to `PUT` the files.

## List Contents of Directory

```
GET    /{entity_route}/{entity_id}/assets/{asset_id}/list
```

# Special Cases:

## brain-regions/

The concept of `Brain Regions`, often referred to as "the hierarchy" is a description of how the areas of the brain are related.
For instance, the brain can be broken up in to parts like the `Hippocampus`, the `Visual Cortex`, etc.
These larger regions can further be broken down, for instance into the `CA1so`,  and `CA1sp` for the hippocampus.
Thus, a tree, or hierarchy is formed.

Following the `Allen Institute`'s original hierarchy, each of the nodes within the tree have the following attributes:

* annotation\_value: A unique number identifying the region; this is the `id` in the original 1.json file: ex: 72856
* acronym: A unique short name for the region; without a space, and as short as possible: ex VISrll2
* name: A longer, more human readable name: ex:"Rostrolateral lateral visual area, layer 2"
* color\_hex\_triplet: A colour associated with the region: ex: "188064"
* parent\_structure\_id: The parent `id` of the current node: ex: 480149202
* children: a list of nodes

Normally, the full set of nodes is encoded in a `hierarchy.json`, which contains all the nodes:

```
{
     "annotation_value": 997,   # this is the ID in the original hierarchy
     "acronym": "root",
     "name": "root",
     "color_hex_triplet": "FFFFFF",
     "children": [
          { "annotation_value": 997, "acronym": "root", "name": "root", ..., "children": []},
          ...
     ]
}
```

### Views

This is a feature to come.
In addition to the "top down" view described above, there is also a `horizontal` or `alternate` view.
In some regions, there is a second natural view that is structured by layer.
For instance, the `Cortex` has multiple layers (1, 2, 3, ...); if one wants to get all the regions that are in this cortical layer, one would have to enumerate them.
Instead, an alternate view is used, that has the `Cortical Layer 3` grouped.
The shape of the hierarchy is the same, so all the properties exist `ids`, `acronym`, etc, but the `parent_structure_id`, `children` are different.


### API

Currently the brain-region API is read only.

`GET brain-region`

Returns all the brain regions, across all the hierarchies, in a flat list.
One can use the normal query parameters to filter this list.
EG, to get a region by acronym:

`GET brain-region?acronym=VISal6a`

And:

`GET brain-region/$UUID`

Returns the particular node.

### Multiple Hierarchies

In the world of biology, there are multiple types of animals.
They may have different hierarchies.
This means there is also a `brain-region-hierarchy` endpoint:

`GET brain-region-hierarchy`

Gets the hierarchies.

`GET brain-region-hierarchy/$UUID`

Gets a particular hierarchy.

`GET brain-region-hierarchy/$UUID/hierarchy`

This returns the 1.json style hierarchy; w/ the tree layout.

### Note

The hierarchy only defines the names of the regions, and their relationship to each other.
This does *not* say where a particular region exists in an atlas.
Most nodes within the hierarchy are not in the atlas, as only nodes in the periphery exist.
For example, the `Isocortex` region won't exist, but its children like `VISrll4` and `VISrll5` will.


### Filtering brain-region aware endpoints

Entities that are aware of their brain-region can be filtered by the hierarchy.
For instance, one may want to get all the morphologies that are within the `Isocortex`.
One way to do this would be to enumerate all the regions within the `Isocortex`, and use that to filter the morphologies.
This is inefficient.
Instead, one can use the following query parameters:

```
    within_brain_region_hierarchy_id: uuid.UUID | None = None
    within_brain_region_brain_region_id: uuid.UUID | None = None
    within_brain_region_ascendants: bool = False
```

```
GET /reconstruction-morphology?within_brain_region_hierarchy_id=3f41b5b5-4b62-40da-a645-eef27c6d07e3&within_brain_region_brain_region_id=ff004978-e3a2-4249-adab-f3d253e4bdd3
```

In other words, the name of the hierarchy, and the id which will be recursively included.
This can happen in either by the `descendants` (the default) or by `ascendants`.

# Brain Atlas:

A BrainAtlas is an volumetric concept describing the locatations of brain regions in space.
It is composed of an `annotation` (also known as `parcellation`) of voxels, storred in an NRRD file.
Each of the voxels is assigned an ID, which corresponds to `annotation_value` in the hierarchy.
In addition, there is metadata assocated with an atlas:

    # the volume of each region
    # meshes of regions

The following endpoints exist:

`GET brain-atlas`

Returns all the atlases that exist

`GET brain-atlas/$UUID`

Returns metadata about the atlas:

```
{
        "creation_date": ...,
        "hierarchy_id": $UUID,
        "id": brain_atlas.id,
        "name": "test brain atlas",
        "species": {
            "creation_date": ...,
            "id": species_id,
            "name": "Test Species",
            "taxonomy_id": "12345",
            "update_date": ...,
        },
        "update_date": ...,
    }
```


`GET brain-atlas/$UUID/regions`
    [
        {
            "brain_atlas_id": $UUID,
            "brain_region_id": $UUID,
            "creation_date": ...,
            "id": $UUID,
            "is_leaf_region": False,
            "update_date": ...,
            "volume": null, # this is null, since it's a leaf region;
        },
        {
            "brain_atlas_id": $UUID,
            "brain_region_id": $UUID,
            "creation_date": ...,
            "id": $UUID,
            "is_leaf_region": False,
            "update_date": ...,
            "volume": 123456789.0,
        },
        ....
    ]

The volume is in um^3.
By only storing the volume for leaf nodes, it composes with the different views by climbing the tree, and summing all the children along the way.

# Authorization:
Current model is to have `Entity`s (ex: `EModel`, `CellMorphology`, etc) be either public, or private to a project.
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

Users in the [service admin group](#service-admin-group) can read data from any project, and edit (read/update/delete) data in any project.

A resource without an authorized_project_id is called a global resource.

Global resources and public entities can be updated only by service admins.



### To be looked at more:
```
    files/
    experimental-data/_count
    model-data/_count
```

