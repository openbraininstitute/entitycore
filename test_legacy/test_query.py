from sqlalchemy import func
from app.db.model import Person, Contribution, CellMorphology
from sqlalchemy.orm import aliased


def test_query(client, db):
    print("test_query")
    from typing import List

    # MTypeAnnotationBodyAlias = aliased(annotation.MTypeAnnotationBody)
    # AnnotationAlias = aliased(annotation.Annotation)
    # CellMorphologyAlias = aliased(morphology.CellMorphology)

    # res: List[morphology.CellMorphology] = (
    #     db.query(MTypeAnnotationBodyAlias.pref_label, func.count().label("count"))
    #     .join(AnnotationAlias, MTypeAnnotationBodyAlias.id == AnnotationAlias.annotation_body_id)
    #     .join(CellMorphologyAlias, AnnotationAlias.entity_id == CellMorphologyAlias.id)
    #     .filter(CellMorphologyAlias.name.like("C060%"))
    #     .group_by(MTypeAnnotationBodyAlias.pref_label)
    # ).all()
    # print(res)
    # MTypeAnnotationBodyAlias = aliased(annotation.MTypeAnnotationBody)
    # SpeciesAlias = aliased(base.Species)
    # CellMorphologyAlias = aliased(morphology.CellMorphology)

    # res: List[morphology.CellMorphology] = (
    #     db.query(SpeciesAlias.name, func.count().label("count"))
    #     .join(CellMorphologyAlias, SpeciesAlias.id == CellMorphologyAlias.species_id)
    #     .filter(CellMorphologyAlias.name.like("C060%"))
    #     .group_by(SpeciesAlias.name)
    # ).all()
    # print(res)
    # print("end test_query")

    # PersonAlias = aliased(agent.Person)
    # ContributionAlias = aliased(contribution.Contribution)
    # CellMorphologyAlias = aliased(morphology.CellMorphology)

    # res: List[morphology.CellMorphology] = (
    #     db.query(PersonAlias.familyName, func.count().label("count"))
    #     .join(ContributionAlias, PersonAlias.id == ContributionAlias.agent_id)
    #     .join(CellMorphologyAlias, ContributionAlias.entity_id == CellMorphologyAlias.id)
    #     .filter(CellMorphologyAlias.name.like("C060%"))
    #     .group_by(PersonAlias.familyName)
    # ).all()
    # print(res)
    # print("end test_query")

    PersonAlias = aliased(Person)
    ContributionAlias = aliased(Contribution)
    CellMorphologyAlias = aliased(CellMorphology)

    res: List[CellMorphology] = (
        db.query(PersonAlias.familyName, func.count().label("count"))
        .join(ContributionAlias, PersonAlias.id == ContributionAlias.agent_id)
        # .join(CellMorphologyAlias, ContributionAlias.entity_id == CellMorphologyAlias.id)
        .join(ContributionAlias.entity)
        .filter(CellMorphologyAlias.name.like("C060%"))
        .group_by(PersonAlias.familyName)
    ).all()
    print(res)
    print("end test_query")
