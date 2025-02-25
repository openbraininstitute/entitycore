# Schema

## Concepts


- **Entity**:

Represents a thing in the system, which can be physical (e.g., a car, a computer) or informational (e.g., a database, a plan).
Objects exist independently and have states that can change over time.

    Ex:

     - AnalysisSoftwareSourceCode
     - EModel
     - Mesh
     - MEModel
     - ReconstructionMorphology
     - SingleCellExperimentalTrace
     - SingleNeuronSynaptome
     - SingleNeuronSimulation
     - ExperimentalNeuronDensity
     - ExperimentalBoutonDensity
     - ExperimentalSynapsesPerConnection
     
- **Agent**:
  
A special type of entity that actively controls or influences a process.
Agents are usually humans, organizations, or intelligent systems (e.g., a driver operating a car, an AI controlling a thermostat).

- **Activity**:
  
Represents an activity that transforms objects by creating, destroying, or modifying them.
Can be controlled by an agent or occur automatically.

- **Relationship**:
  
    1.  Entity-Activity Relationships:
       
	    •	wasGeneratedBy (Entity → Activity): An entity (e.g., a document) was created or derived from an activity.

	    •	used (Activity → Entity): An activity used a pre-existing entity as an input.

	2.	Entity-Agent Relationships:

	    •	wasAttributedTo (Entity → Agent): An entity is attributed to an agent, meaning the agent had a role in creating, modifying, or influencing the entity.

    3.	Activity-Agent Relationships:
       
	    •	wasAssociatedWith (Activity → Agent): An activity was performed by or under the responsibility of an agent.

	    •	actedOnBehalfOf (Agent → Agent): One agent acted on behalf of another, indicating delegation of responsibility. 

    4.  Entity-Entity Relationships:
       
	    •	wasDerivedFrom (Entity → Entity): One entity was derived from another, meaning the second entity influenced the first (e.g., a translated document derived from an original document).

	    •	wasRevisionOf (Entity → Entity): A special case of derivation where an entity is a revised version of another entity.

	    •	wasQuotedFrom (Entity → Entity): A specific form of derivation where an entity includes content from another entity. (not used)

	    •	hadMember (Entity → Entity): Represents a collection-membership relationship where an entity is part of a larger collection. (not used, we use hasPart for some reason)

	5.	Activity-Activity Relationships:

	    •	wasInformedBy (Activity → Activity): One activity was informed or influenced by another activity (e.g., a report-writing activity was informed by a research activity).(used for workflow)

	    •	hadStep (Activity → Activity): Represents a hierarchical breakdown where an activity consists of sub-activities.

	6.	Agent-Agent Relationships:

    	•	actedOnBehalfOf (Agent → Agent): One agent (e.g., an employee) acted on behalf of another agent (e.g., a company or supervisor), representing delegation or responsibility. (not used)

	8.	Activity-Entity Relationships (Additional Concepts):

	    •	generated (Activity → Entity): Similar to “wasGeneratedBy,” but expressed from the activity’s perspective, meaning the activity produced a certain entity.

	    •	invalidated (Activity → Entity): An entity was invalidated or ceased to exist due to an activity (e.g., a document was deleted). (not used)


- **Annotation**:
    An opinion about an entity. Annotations are a relationship between an entity and a element of a controlled vocabulary, set by an Agent at a given time.

    A "controlled vocabulary" is a predefined set of terms (no free string) for concepts such as m-types / e-types /...
    The terms are possibly in a hierarchical structure.
    Each element of the vocabulary has a property prefLabel which is the preferred label for a concept element, A property AltLabel for synonyms and a description.

    A "controlled vocabulary + the hierarchical structure is called a classification scheme. There can be multiple "classification schemes" for the same concept.

    We agreed to use 1 annotation of a classification scheme for 1 entity. Discussions are on going for coexistence of multiple classification. We can proceed assuming 1 classification scheme is used for the time being per concept.



     - Brain Location
     - Brain Region
     - License
     - Species
