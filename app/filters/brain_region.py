import sqlalchemy as sa

from app.db.model import BrainRegion, BrainRegionHierarchyName

def _get_family_query(hierarchy_id: int, hierarchy_name: str, with_ascendants=False):
    """Create query for BrainRegions that returns ids.

    Can either traverse down (the default) or up (with_ascendants=True)
    """

    cte = (sa.select(BrainRegion.id, BrainRegion.parent_structure_id)
           .join(BrainRegionHierarchyName,
                 BrainRegion.hierarchy_name_id == BrainRegionHierarchyName.id)
           .where(BrainRegion.hierarchy_id == hierarchy_id,
                  BrainRegionHierarchyName.name == hierarchy_name)
           .cte(recursive=True)
    )

    br_alias = sa.orm.aliased(BrainRegion)

    direction_join = br_alias.parent_structure_id == cte.c.id
    if with_ascendants:
        direction_join = br_alias.id == cte.c.parent_structure_id

    recurse = (sa.select(br_alias.id, br_alias.parent_structure_id)
               .join(cte, direction_join)
               .join(BrainRegionHierarchyName,
                     br_alias.hierarchy_name_id == BrainRegionHierarchyName.id)
               .where(BrainRegionHierarchyName.name == hierarchy_name)
    )

    query = cte.union_all(recurse)

    return query


def filter_by_hierarchy_name_and_id(query, model, hierarchy_id: int, hierarchy_name: str, with_ascendants=False):
    brain_region_query = _get_family_query(hierarchy_id, hierarchy_name, with_ascendants=with_ascendants)
    query = query.filter(model.brain_region_id.in_(sa.select(brain_region_query.c.id)))
    return query
