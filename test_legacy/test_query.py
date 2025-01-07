import app.models.morphology as morphology
from app.models.base import func
from app.models import agent, contribution
from sqlalchemy.orm import aliased


def test_query(client, db):
    print("test_query")
    from typing import List

    # MTypeAnnotationBodyAlias = aliased(annotation.MTypeAnnotationBody)
    # AnnotationAlias = aliased(annotation.Annotation)
    # ReconstructionMorphologyAlias = aliased(morphology.ReconstructionMorphology)

    # res: List[morphology.ReconstructionMorphology] = (
    #     db.query(MTypeAnnotationBodyAlias.pref_label, func.count().label("count"))
    #     .join(AnnotationAlias, MTypeAnnotationBodyAlias.id == AnnotationAlias.annotation_body_id)
    #     .join(ReconstructionMorphologyAlias, AnnotationAlias.entity_id == ReconstructionMorphologyAlias.id)
    #     .filter(ReconstructionMorphologyAlias.name.like("C060%"))
    #     .group_by(MTypeAnnotationBodyAlias.pref_label)
    # ).all()
    # print(res)
    # MTypeAnnotationBodyAlias = aliased(annotation.MTypeAnnotationBody)
    # SpeciesAlias = aliased(base.Species)
    # ReconstructionMorphologyAlias = aliased(morphology.ReconstructionMorphology)

    # res: List[morphology.ReconstructionMorphology] = (
    #     db.query(SpeciesAlias.name, func.count().label("count"))
    #     .join(ReconstructionMorphologyAlias, SpeciesAlias.id == ReconstructionMorphologyAlias.species_id)
    #     .filter(ReconstructionMorphologyAlias.name.like("C060%"))
    #     .group_by(SpeciesAlias.name)
    # ).all()
    # print(res)
    # print("end test_query")

    # PersonAlias = aliased(agent.Person)
    # ContributionAlias = aliased(contribution.Contribution)
    # ReconstructionMorphologyAlias = aliased(morphology.ReconstructionMorphology)

    # res: List[morphology.ReconstructionMorphology] = (
    #     db.query(PersonAlias.familyName, func.count().label("count"))
    #     .join(ContributionAlias, PersonAlias.id == ContributionAlias.agent_id)
    #     .join(ReconstructionMorphologyAlias, ContributionAlias.entity_id == ReconstructionMorphologyAlias.id)
    #     .filter(ReconstructionMorphologyAlias.name.like("C060%"))
    #     .group_by(PersonAlias.familyName)
    # ).all()
    # print(res)
    # print("end test_query")

    PersonAlias = aliased(agent.Person)
    ContributionAlias = aliased(contribution.Contribution)
    ReconstructionMorphologyAlias = aliased(morphology.ReconstructionMorphology)

    res: List[morphology.ReconstructionMorphology] = (
        db.query(PersonAlias.familyName, func.count().label("count"))
        .join(ContributionAlias, PersonAlias.id == ContributionAlias.agent_id)
        # .join(ReconstructionMorphologyAlias, ContributionAlias.entity_id == ReconstructionMorphologyAlias.id)
        .join(ContributionAlias.entity)
        .filter(ReconstructionMorphologyAlias.name.like("C060%"))
        .group_by(PersonAlias.familyName)
    ).all()
    print(res)
    print("end test_query")
