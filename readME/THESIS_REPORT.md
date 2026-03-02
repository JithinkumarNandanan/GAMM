# Thesis Report: Generalized Methodology for Automated Mapping of Model Parameters between Generalized Digital Twins and Domain Models

**Author:** Jithinkumar Nandanan  
**Program:** Master Systems Engineering for Manufacturing  
**Institution:** Otto von Guericke Universität Magdeburg, Faculty of Mechanical Engineering  
**Institute:** Institut für Engineering von Produkten und Systemen

---

## Table of Contents

1. [Introduction](#introduction)
2. [Chapter 1: Interoperability in Industry 4.0](#chapter-1-interoperability-in-industry-40)
3. [Chapter 2: Key Technologies for Industrial Interoperability](#chapter-2-key-technologies-for-industrial-interoperability)
4. [Chapter 3: State of the Art in Data Mapping and Semantic Technologies](#chapter-3-state-of-the-art-in-data-mapping-and-semantic-technologies)
5. [Chapter 4: Methodology for Automated Parameter Mapping](#chapter-4-methodology-for-automated-parameter-mapping)
6. [Chapter 5: Prototypical Implementation and Validation](#chapter-5-prototypical-implementation-and-validation)
7. [Chapter 6: Conclusion and Future Work](#chapter-6-conclusion-and-future-work)
8. [References](#references)

---

## Introduction

The digital transformation of manufacturing industries, commonly referred to as Industry 4.0, represents a paradigm shift towards intelligent, interconnected production systems. This transformation is driven by the integration of Internet technologies into industrial processes, aiming to unlock new value creation potential through networking and digitalization [Diskussionspapier, 2023]. However, achieving true interoperability in industrial environments remains a significant challenge, as industrial assets such as machines, components, and production systems are far from achieving the "Plug & Play" functionality that is commonplace in consumer IT devices.

The automation of automation engineering has emerged as a highly relevant research topic, with efficiency and effectiveness in production system engineering being crucial for economic success in manufacturing [Thesis Task Description, 2025]. A core challenge in this domain is the identification and utilization of appropriate data sources, where relevant data must be mapped to the internal data models of engineering automation algorithms for each application. As data sources increasingly adopt standardized structures through initiatives such as the Industrial Digital Twin Association (IDTA), OPC Foundation, and AutomationML Association, the need for automated mapping methodologies becomes paramount.

Simulation-based engineering decisions play a key role in automating engineering processes. However, these simulations often rely on tool-specific, proprietary data models that need to be populated with data from standardized sources. The master's thesis addresses this fundamental problem: **How can model parameters be automatically mapped between generalized digital twins (represented by standardized data sources) and domain-specific simulation models (represented by proprietary tool data models)?**

This thesis presents a generalized methodology for automated mapping of model parameters between generalized digital twins and domain-specific simulation models. The work is situated within the broader context of industrial interoperability, where three key technologies—Asset Administration Shell (AAS), OPC UA with its Companion Specifications, and AutomationML—are recognized as Industry 4.0 key technologies recommended by the Platform Industrie 4.0 [Diskussionspapier, 2023]. Rather than competing with each other, these technologies complement one another and together create comprehensive concepts for unified digital interoperability between Industry 4.0-capable machines and systems throughout their entire lifecycle.

The methodology developed in this thesis addresses the challenge of bridging standardized data sources with proprietary simulation tool data models through a three-part approach: (1) comprehensive state-of-the-art analysis of simulation systems, standardized data sources, and mapping technologies; (2) development of a novel hybrid semantic matching approach; and (3) prototypical implementation demonstrating the methodology's applicability.

This work contributes to the vision of avoiding duplicate standardization and multiple digital models that require duplicate data storage and software development, which would hinder a harmonized and efficient digital value chain. By providing automated mapping capabilities, the methodology enables seamless data exchange and automated engineering decision support, ultimately contributing to the realization of Industry 4.0 objectives.

---

## Chapter 1: Interoperability in Industry 4.0

*Chapter 1 establishes the conceptual foundations by examining the concept of interoperability, the challenges of achieving it in industrial environments, and how complementary standardization approaches address these challenges.*

### 1.1 The Concept of Interoperability

Interoperability refers to the ability of systems, devices, and applications to connect and communicate purposefully across manufacturers, including both Operational Technology (OT) and Information Technology (IT) [Diskussionspapier, 2023]. In the context of Industry 4.0, achieving true interoperability requires deep software integration of assets and systems in multiple dimensions, as illustrated by the Reference Architecture Model Industry 4.0 (RAMI4.0).

The RAMI4.0 framework, standardized in IEC PAS 63088 and DIN SPEC 91345, provides a three-dimensional model for understanding interoperability across:

1. **Hierarchy Levels**: All levels of automation technology, from product to connected world
2. **Value Stream**: The entire lifecycle process of assets and systems, from development to maintenance
3. **Layers**: The different layers of an enterprise, from business to functional to asset

This comprehensive view of interoperability highlights that achieving seamless data exchange in industrial environments is far more complex than in consumer IT, where technologies like Ethernet, USB, and driver architectures provide universal, manufacturer-independent communication standards.

### 1.2 The Challenge of Industrial Interoperability

Unlike consumer IT environments, industrial systems have developed diverse proprietary and standardized solutions for different use cases. While these solutions serve their specific purposes, they often create barriers to true interoperability. The challenge lies in enabling assets and systems to communicate and exchange data seamlessly across:

- **Different manufacturers**: Ensuring compatibility between equipment from various vendors
- **Different lifecycle phases**: From engineering and commissioning to operation and maintenance
- **Different domains**: Bridging mechanical, electrical, automation, and IT domains
- **Different standards**: Harmonizing various standardization initiatives

To achieve such interoperability, all relevant assets and services must include standardized data models (through AAS Submodel Templates, AutomationML, and OPC UA Companion Specifications) and make these accessible through standardized interfaces such as OPC UA. The Asset Administration Shell (AAS) serves as a digital lifecycle file that all authorized stakeholders—from sales to service, across company boundaries—can access.

### 1.3 The Risk of Duplicate Standardization

A critical concern in the development of industrial interoperability solutions is the potential for duplicate standardization and modeling. When multiple technologies (AAS Submodels, AutomationML, and OPC UA Companion Specifications) pursue the same goal of providing harmonized and standardized information models for industry, there is a risk that they might compete rather than complement each other.

This competition could lead to:
- **Duplicate modeling**: The same information being modeled multiple times in different formats
- **Duplicate data storage**: Multiple digital models requiring separate data storage
- **Duplicate software development**: Different tools needed for each standard
- **Hindered value chains**: Inefficient and fragmented digital value chains

The Diskussionspapier on interoperability [Diskussionspapier, 2023] addresses this concern directly, emphasizing that proprietary and closed interoperability solutions are not sustainable in the long term. The organizations AutomationML e.V., IDTA, OPC Foundation, and VDMA are convinced that standardized interoperability solutions should be prioritized.

### 1.4 The Vision: Complementary Technologies

The key insight from recent standardization efforts is that AAS, OPC UA, and AutomationML do not compete with each other but rather complement each other. When applied appropriately, these technologies:
- **Avoid duplicate work**: Each technology serves its specific purpose
- **Reduce model overlaps**: Clear boundaries between application domains
- **Reduce development effort**: Reuse of standardized models and interfaces
- **Enable cross-domain interoperability**: Through intelligent combination of standards

This vision of complementary technologies forms the foundation for the methodology developed in this thesis. The automated mapping approach recognizes that different standards serve different purposes and provides mechanisms to bridge between them.

### 1.5 Motivation for Automated Mapping

The increasing adoption of standardized data structures in industrial data sources creates both opportunities and challenges. On one hand, standardization enables interoperability and reduces integration effort. On the other hand, the diversity of standards and the need to map between them and proprietary tool models creates a mapping challenge that grows with the number of data sources and target models.

Manual mapping is:
- **Time-consuming**: Requires expert knowledge and significant effort
- **Error-prone**: Human errors can lead to incorrect mappings
- **Not scalable**: Does not scale to large numbers of parameters and models
- **Maintenance-intensive**: Requires updates when models change

Automated mapping addresses these challenges by:
- **Reducing manual effort**: Automating the identification and mapping process
- **Improving consistency**: Applying uniform mapping rules
- **Enabling scalability**: Handling large numbers of parameters efficiently
- **Supporting maintenance**: Adapting to model changes automatically

### 1.6 Thesis Objectives and Structure

This thesis addresses the automated mapping challenge through a generalized methodology that enables the identification and application of standardized data sources to facilitate the automatic use of simulation methods within production system engineering. The work is structured into six chapters:

1. **Chapter 1 (this chapter)**: Interoperability in Industry 4.0—conceptual foundations
2. **Chapter 2**: Key Technologies for Industrial Interoperability—AAS, OPC UA, AutomationML
3. **Chapter 3**: State of the Art in Data Mapping and Semantic Technologies
4. **Chapter 4**: Methodology for Automated Parameter Mapping
5. **Chapter 5**: Prototypical Implementation and Validation
6. **Chapter 6**: Conclusion and Future Work

The following chapter provides the technical background on the key technologies for industrial interoperability.

---

## Chapter 2: Key Technologies for Industrial Interoperability

*Chapter 2 provides comprehensive technical background on the Asset Administration Shell, OPC UA with Companion Specifications, and AutomationML, explaining their individual capabilities and complementary relationships.*

This chapter introduces the three key technologies recognized as Industry 4.0 key technologies: Asset Administration Shell (AAS), OPC UA with Companion Specifications, and AutomationML. Understanding these technologies, their purposes, and how they complement each other is essential for developing an effective automated mapping methodology.

### 2.1 Asset Administration Shell (AAS)

#### 2.1.1 Concept and Purpose

The Asset Administration Shell (AAS) is a standardized digital representation of an asset that contains all relevant information throughout its entire lifecycle. According to the Diskussionspapier [Diskussionspapier, 2023], the AAS serves as a "digital lifecycle file" that all authorized stakeholders—from sales to service, across company boundaries—can access.

The AAS is designed to provide:
- **Lifecycle-spanning information**: Data relevant across the entire asset lifecycle
- **Standardized structure**: Based on AAS Submodel Templates
- **Cross-company access**: Enabling collaboration across organizational boundaries
- **Reference to detailed models**: Linking to detailed information stored elsewhere

#### 2.1.2 AAS Submodel Templates

AAS Submodel Templates define standardized structures for specific types of information. These templates enable:
- **Consistent data representation**: Same information structure across different assets
- **Interoperability**: Different systems can understand the same data structure
- **Reusability**: Templates can be applied to multiple assets

Examples of AAS Submodel Templates include:
- Technical data sheets
- Sales information
- CO2 footprint data
- Maintenance information

#### 2.1.3 AAS in the RAMI4.0 Context

According to the Diskussionspapier recommendations, Type 2 AAS should be positioned in the Connected World of RAMI4.0, but not in classical productive field devices. This positioning reflects that:
- **Critical data should not depend on AAS infrastructure**: The failure of an AAS should not cause the failure of its asset
- **AAS provides lifecycle information**: Focus on non-critical, lifecycle-spanning data
- **Separation of concerns**: Operational data (OPC UA) and lifecycle data (AAS) serve different purposes

#### 2.1.4 AAS API and Data Access

The AAS provides data access through standardized APIs. As of April 2023, the REST API enables the Connected World to access AAS data. This API enables:
- **Standardized access**: Consistent interface for different applications
- **Lifecycle-spanning data**: Access to information across the entire asset lifecycle
- **Integration**: Connection to other systems and platforms

### 2.2 OPC UA and Companion Specifications

#### 2.2.1 OPC UA Overview

OPC Unified Architecture (OPC UA) is a platform-independent, service-oriented architecture that provides secure and reliable information exchange in industrial automation. OPC UA is designed for:
- **Machine-to-machine communication**: Direct communication between devices
- **Machine-to-IT communication**: Integration with enterprise IT systems
- **Digital twin integration**: Connection to digital twins and data spaces
- **Metaverse integration**: Future integration with virtual environments

#### 2.2.2 OPC UA Companion Specifications

OPC UA Companion Specifications define standardized information models for specific domains or device types. These specifications:
- **Standardize semantics**: Define what information means in a specific context
- **Enable interoperability**: Different systems understand the same information model
- **Support domain expertise**: Developed by domain experts for their specific domains

Examples include specifications for:
- Energy consumption data
- Machine status information
- Process parameters
- Safety-related data

#### 2.2.3 Operational Data Access

According to the Diskussionspapier recommendations, OPC UA should be used for operational data access. This includes:
- **Communication between machines**: Real-time data exchange
- **Machine-to-IT communication**: Integration with enterprise systems
- **Dynamic data**: Real-time operational information
- **Metadata access**: Information about where data is located

The use of OPC UA Companion Specifications ensures that operational data is accessed using standardized models and semantics, supporting use cases such as CO2 footprint calculation in the AAS.

#### 2.2.4 OPC UA Information Models

OPC UA Information Models provide:
- **Type definitions**: Standardized data types for industrial information
- **Object models**: Hierarchical structures for organizing information
- **Semantic annotations**: Meaning and context of information
- **Extensibility**: Ability to extend models for specific needs

### 2.3 AutomationML

#### 2.3.1 Concept and Purpose

AutomationML (Automation Markup Language) is a neutral, XML-based data format for the exchange of plant engineering information. AutomationML is designed for:
- **Engineering data exchange**: Manufacturer-neutral exchange of object models
- **Tool interoperability**: Enabling different engineering tools to exchange data
- **Model reuse**: Reusing engineering models across different tools and projects
- **Lifecycle support**: Supporting engineering throughout the asset lifecycle

#### 2.3.2 AutomationML Structure

AutomationML organizes engineering information into:
- **Topology models**: Physical and logical structure of systems
- **Geometry models**: 3D geometry and visualization
- **Behavior models**: Control logic and behavior
- **Kinematics models**: Motion and movement

#### 2.3.3 AutomationML Libraries

AutomationML libraries provide standardized domain models for:
- **Automation components**: Structure models for automation components
- **Plant topologies**: Topology models for plants
- **Hardware topologies**: Hardware connection topologies
- **Networked system models**: Models of networked automation systems

These libraries enable:
- **Standardization**: Consistent models across different projects
- **Reusability**: Reuse of standardized models
- **Interoperability**: Different tools can understand the same models

#### 2.3.4 Integration with Other Formats

AutomationML supports integration with other engineering formats through:
- **References**: Linking to external files and models
- **Embedding**: Including other formats within AutomationML
- **Conversion**: Tools for converting between formats

Examples include:
- OPC UA Nodeset files (offline configuration files)
- Device description files
- Platform-independent text documents

### 2.4 Complementary Relationship of Technologies

#### 2.4.1 The "Big Picture" of Interoperability

The Diskussionspapier [Diskussionspapier, 2023] presents a "Big Picture Interoperability" that shows how AAS, OPC UA, and AutomationML fit together, complement each other, and enable interoperability across domains through combined application in industrial automation.

The key insight is that **interoperability is not achieved through a single world model, but through an intelligent combination of different standards that provide domain models from the corresponding domain experts**.

#### 2.4.2 Role Separation

Each technology serves a specific purpose:

**AAS (Asset Administration Shell)**:
- **Purpose**: Lifecycle-spanning product information
- **Scope**: Connected World, non-critical data
- **Focus**: Product information, technical data sheets, sales data, CO2 footprint

**OPC UA (Operational Data)**:
- **Purpose**: Operational data access
- **Scope**: Real-time machine communication
- **Focus**: Dynamic operational data, machine status, process parameters

**AutomationML (Engineering Data)**:
- **Purpose**: Engineering data exchange
- **Scope**: Engineering phase, tool interoperability
- **Focus**: Plant topology, automation components, control logic

#### 2.4.3 Avoiding Competence Conflicts

The Diskussionspapier recommends avoiding competence conflicts in data modeling by having data defined and standardized by experts in the domain where it originally occurs or has already been defined. This principle means:

- **AAS Submodels**: Standardized for lifecycle-spanning product information
- **OPC UA Companion Specifications**: Standardized for operational data access
- **AutomationML Libraries**: Standardized for engineering domain models

This separation ensures that:
- **Domain expertise is preserved**: Experts define models for their domains
- **Duplicate modeling is avoided**: Each piece of information is modeled once
- **Interoperability is maintained**: Standards work together rather than compete

#### 2.4.4 Reference and Reuse

The technologies support each other through:
- **Referencing**: AAS can reference AutomationML models and OPC UA information
- **Reuse**: Models from one technology can be reused in another
- **Integration**: Technologies can be combined in applications

For example:
- AAS can reference AutomationML engineering models
- AAS can reference OPC UA information models for operational data
- AutomationML can reference OPC UA Nodeset files
- OPC UA can provide data that supports AAS use cases (e.g., CO2 footprint)

### 2.5 Implications for Automated Mapping

#### 2.5.1 Mapping Challenges

The complementary relationship of AAS, OPC UA, and AutomationML creates specific mapping challenges:

1. **Cross-technology mapping**: Mapping between different standard formats
2. **Standard-to-proprietary mapping**: Mapping from standards to proprietary tool models
3. **Semantic alignment**: Ensuring semantic consistency across different models
4. **Lifecycle alignment**: Mapping data across different lifecycle phases

#### 2.5.2 Mapping Requirements

An effective automated mapping methodology must:

1. **Support multiple standards**: Handle AAS, OPC UA, AutomationML formats
2. **Preserve semantics**: Maintain meaning during mapping
3. **Handle heterogeneity**: Deal with different data structures and formats
4. **Enable enrichment**: Enhance data with additional semantic information
5. **Provide validation**: Ensure correctness of mappings

#### 2.5.3 Foundation for Methodology

Understanding the complementary relationship of these technologies provides the foundation for the mapping methodology developed in this thesis:

- **Multi-format support**: The methodology must handle all three standard formats
- **Semantic understanding**: Mapping must consider semantic meaning, not just structure
- **Context awareness**: Different technologies serve different purposes and contexts
- **Enrichment strategy**: Use of standards (eCl@ss, IEC CDD) to enhance semantic understanding
- **Validation mechanisms**: Ensure physical and semantic correctness of mappings

### 2.6 Summary

This chapter has introduced the three key technologies for industrial interoperability:

- **Asset Administration Shell (AAS)**: Provides lifecycle-spanning product information in the Connected World
- **OPC UA**: Enables operational data access and machine-to-machine communication
- **AutomationML**: Supports engineering data exchange and tool interoperability

These technologies complement rather than compete with each other, each serving specific purposes in the industrial interoperability landscape. Understanding their roles, relationships, and complementary nature is essential for developing an effective automated mapping methodology that bridges standardized data sources with proprietary simulation tool models.

The next chapter reviews the state of the art in data mapping and semantic technologies, identifying gaps that the proposed methodology addresses.

---

## Chapter 3: State of the Art in Data Mapping and Semantic Technologies

*Chapter 3 reviews existing approaches to schema matching, ontology alignment, and semantic enrichment, identifying gaps that the proposed methodology addresses.*

This chapter surveys existing approaches to automated data mapping, schema matching, ontology alignment, and semantic enrichment in industrial and general contexts. The aim is to position the methodology developed in this thesis relative to the state of the art and to clarify which gaps it addresses.

### 3.1 Schema Matching and Data Mapping

#### 3.1.1 Schema Matching Approaches

Schema matching aims to find correspondences between elements of two or more schemas (e.g., database schemas, XML schemas, or information models). Existing approaches can be classified along several dimensions:

- **Linguistic matching**: Uses names, labels, and comments to compute similarity (e.g., string similarity, token-based overlap). Simple and fast but fails when names differ (synonyms, abbreviations, different languages).
- **Structural matching**: Exploits schema structure (parent-child, keys, references). Helps when names are ambiguous but depends on structural similarity.
- **Constraint-based matching**: Uses data types, units, value ranges. Well-suited to technical data where units and types are critical.
- **Instance-based matching**: Uses sample data to infer correspondences. Can discover semantic matches but requires representative data.

In industrial settings, schemas often come from AAS Submodels, OPC UA Information Models, or AutomationML libraries. These combine linguistic elements (idShort, Name, Description), structural nesting, and technical constraints (valueType, unit). Pure linguistic or pure structural methods are therefore insufficient; a combination is needed.

#### 3.1.2 Limitations for Industrial Data

For mapping between generalized digital twin representations (e.g., AAS, OPC UA, AutomationML) and domain-specific simulation models:

- **Heterogeneity of formats**: JSON (AAS), XML (AAS, AML), and binary/OPC UA Nodesets require format-agnostic extraction of “semantic nodes” (name, definition, value, type, unit) before matching.
- **Abbreviations and naming conventions**: Industrial naming (e.g., max_V, Max_feed_force_Fx) requires normalization and expansion before comparison.
- **Physical correctness**: Matching must respect units and data types to avoid nonsensical mappings (e.g., temperature to pressure). Many generic schema matchers do not treat units and types as first-class constraints.

These limitations motivate a **hybrid matching** approach that combines constraint-based checks (unit, type) with lexical and semantic similarity, as developed in Chapter 4.

### 3.2 Ontology Alignment and Semantic Interoperability

#### 3.2.1 Ontology Alignment

Ontology alignment seeks to identify equivalent or related concepts and properties across ontologies. Techniques include:

- **String and lexical similarity**: Edit distance, Jaccard on tokens, normalized names.
- **Semantic similarity**: Use of external vocabularies (e.g., WordNet), or embedding-based similarity (e.g., sentence transformers).
- **Graph and structure**: Aligning class hierarchies and property graphs.
- **Logical reasoning**: Using formal definitions and reasoning to infer equivalences.

In Industry 4.0, standardized vocabularies and product classifications (e.g., eCl@ss, IEC CDD) act as reference ontologies. Mapping “parameter names” from AAS or simulation tools to these standards is a form of ontology alignment where one side may be flat lists of parameters rather than full ontologies.

#### 3.2.2 Gaps for Parameter-Level Mapping

- **Parameter-level vs. ontology-level**: Many tools align whole ontologies or schemas; the thesis focus is on **parameter-level** mapping (individual properties/variables) between digital twin sources and simulation model inputs.
- **Standard-to-proprietary**: Aligning two public ontologies is different from mapping **standardized sources** (AAS, OPC UA, AML) to **proprietary simulation tool models** that may have no formal ontology.
- **Use of industrial standards**: Leveraging eCl@ss and IEC CDD as enrichment sources (definitions, preferred terms) to improve matching is not always covered by generic ontology alignment frameworks.

The proposed methodology uses eCl@ss and IEC CDD for **semantic enrichment** of nodes (adding definitions and usage) and then matches on these enriched representations, thus combining ontology-based enrichment with parameter-level mapping.

### 3.3 Semantic Enrichment

#### 3.3.1 Enrichment Strategies

Semantic enrichment adds meaning to raw identifiers (names, codes) so that matching can rely on definitions and context, not only on strings. Common strategies:

- **Structured knowledge bases**: Look up terms in product classifications (eCl@ss, IEC CDD), thesauri, or domain ontologies to get definitions and synonyms.
- **Document-based enrichment**: Search in technical documents, data sheets, or support files for descriptions of parameters.
- **LLM-based generation**: Use large language models to generate or disambiguate definitions and usage from context (e.g., related parameter names, units, types).

#### 3.3.2 Gaps Addressed by Multi-Source Enrichment

- **Single-source dependency**: Relying on one knowledge base (e.g., only eCl@ss) may miss terms or give wrong context. A **priority-based cascade** (support documents → eCl@ss → IEC CDD → local LLM → cloud LLM) increases coverage and allows domain-specific overrides.
- **Context for disambiguation**: Terms like “capacity” (volume vs. electrical charge) need context. Using **collection context** (related nodes, units, types) and **LLM-based selection** among Top-K candidates improves disambiguation compared to picking the single highest similarity score.
- **Industrial abbreviations**: Expanding abbreviations (e.g., max, min, V, Fx) before lookup is often not integrated into enrichment pipelines. The methodology includes **rule-based abbreviation expansion** with optional LLM fallback for complex cases.

### 3.4 Matching Algorithms and Similarity Metrics

#### 3.4.1 Commonly Used Metrics

- **Levenshtein (edit distance)**: Good for typos and small naming variations; sensitive to word order and length.
- **Jaccard (token overlap)**: Good for word order and partial overlap; does not handle typos inside words.
- **Cosine similarity (e.g., TF-IDF, embeddings)**: Good for semantic similarity; typically requires more setup and computation.
- **Constraint checks**: Unit compatibility, type compatibility; often used as filters rather than as weighted components of a score.

#### 3.4.2 Gaps Addressed by Hybrid Matching

- **Physical correctness**: Many matchers optimize only for name or semantic similarity. The thesis uses **unit compatibility** and **type compatibility** as weighted components (e.g., 25% each) so that physically wrong matches are penalized even if names are similar.
- **Combining metrics**: Using a **fixed weighted combination** (unit, type, lexical, semantic) gives a single score while still allowing analysis of component contributions (e.g., via detailed similarity matrices).
- **Determinism and interpretability**: Text-based semantic similarity (word overlap, TF-IDF-like weighting) avoids dependency on heavy embedding models and keeps the pipeline interpretable and deployable without GPU.

### 3.5 Summary of Gaps and Positioning

| Gap | State of the art | Proposed methodology |
|-----|------------------|------------------------|
| Multi-format extraction | Often format-specific tools | Unified semantic node extraction from JSON, XML, AML, EXM |
| Unit/type as first-class | Often filter-only or ignored | Weighted components (25% unit, 25% type) in hybrid score |
| Enrichment strategy | Single source or no enrichment | Priority cascade: documents → eCl@ss → IEC CDD → Llama → Gemini |
| Parameter-level mapping | Many tools focus on schema/ontology level | Explicit parameter-to-parameter mapping with match types and confidence |
| Abbreviations and context | Ad hoc or not integrated | Rule-based expansion + context-aware LLM selection from Top-K |
| Standard-to-proprietary | Less emphasis | Explicit source (e.g., AAS) to target (e.g., simulation model) mapping |

The next chapter presents the methodology for automated parameter mapping that addresses these gaps.

---

## Chapter 4: Methodology for Automated Parameter Mapping

*Chapter 4 presents the developed methodology in detail, including semantic node extraction, multi-source enrichment strategies, hybrid matching algorithms, and validation mechanisms.*

This chapter describes the generalized methodology for automated mapping of model parameters between generalized digital twins (represented by standardized data sources such as AAS, OPC UA, AutomationML) and domain-specific simulation models. The methodology is organized as a multi-stage pipeline with well-defined inputs, outputs, and design choices.

### 4.1 Overview of the Methodology

The methodology is structured as a **five-stage pipeline**:

1. **Extraction**: Extract semantic nodes from source and target files (JSON, XML, AML, EXM).
2. **Normalization**: Expand abbreviations and standardize names for consistent matching and enrichment lookup.
3. **Enrichment**: Enrich nodes with definitions and usage information from multiple sources (documents, eCl@ss, IEC CDD, LLMs).
4. **Mapping**: Match source nodes to target nodes using a hybrid similarity algorithm (unit, type, lexical, semantic).
5. **Reporting**: Generate similarity matrices, mapping reports, and optional validation outputs.

Meta-models are kept minimal and tool-independent: both data sources and simulation models are represented as **collections of semantic nodes**, where each node has at least: name, conceptual definition, usage of data, value, value type, unit, and optional metadata. This allows the same pipeline to be applied to different standard formats and proprietary models.

### 4.2 Semantic Node Extraction

#### 4.2.1 Semantic Node Model

A **semantic node** is a unified representation of a single parameter or property, regardless of the original format. It includes:

- **name**: Identifier (e.g., idShort, Name, tag name).
- **conceptual_definition**: What the parameter represents (e.g., from description, Definition in eCl@ss).
- **usage_of_data**: How the data is used (affordance; can be enriched from standards or LLM).
- **value**: Current or default value if available.
- **value_type**: Data type (e.g., String, Float, Integer, Boolean).
- **unit**: Measurement unit (e.g., °C, bar, mm).
- **source_description**: Extended context from the source (e.g., multilanguage descriptions).
- **source_file**: Origin file path.
- **enriched**: Flag indicating whether the node was enriched.
- **enrichment_source**: Which source provided enrichment (e.g., eCl@ss, IEC CDD, document, LLM).
- **metadata**: Format-specific or pipeline-specific metadata.

This model supports AAS (submodel elements, concept descriptions), OPC UA (variables, properties), and AutomationML (interface class attributes) through format-specific extractors that populate the same structure.

#### 4.2.2 Extraction Logic by Format

- **JSON (AAS)**: Recursive traversal of `submodelElements` and use of `conceptDescriptions`; extraction of idShort, description (prefer English), value, valueType, unit.
- **XML (AAS 2.0/3.0)**: Namespace-aware parsing; extraction of idShort, description, value, valueType, unit; handling of multilingual descriptions.
- **AutomationML**: Parsing of InterfaceClassLibrary and nested interface classes; extraction of Name, Description, Value, AttributeDataType, and unit-related information.
- **EXM**: Treated as XML with the same parsing strategy as AAS XML.

All extractors output a **SemanticNodeCollection** (set or list of semantic nodes), which is the common input to normalization and enrichment.

### 4.3 Normalization

#### 4.3.1 Purpose

Normalization ensures that:

- Abbreviations (e.g., max, min, V, Fx) are expanded for better matching and for lookup in eCl@ss/IEC CDD (which often use full terms).
- Multiple search variants (original normalized, expanded, space-separated, underscore-separated) are generated to increase recall in library search.

#### 4.3.2 Process

- **Lowercasing** and splitting by separators (e.g., `_`, `-`, space).
- **Rule-based expansion** using a dictionary (e.g., max → maximum, V → velocity, temp → temperature). Single-letter and known multi-letter abbreviations are expanded; embedded abbreviations are handled by pattern matching where possible.
- **Search variants**: Original normalized name, expanded form, space- and underscore-separated variants are produced for each node name.
- **Optional AI fallback**: For complex or unknown abbreviations, an LLM (e.g., Gemini) can be invoked to suggest an expanded form, which is then used for search variants.

This step does not change the stored name of the node; it only prepares variants used during enrichment and matching.

### 4.4 Multi-Source Enrichment Strategy

#### 4.4.1 Priority-Based Cascade

Enrichment is performed in a **fixed priority order**; the first source that returns a valid enrichment is used (early exit):

1. **Support documents**: User-provided documents in a designated folder (e.g., `support_files/`). Search is performed using normalized name variants; surrounding context can be extracted and used as conceptual_definition and usage_of_data.
2. **eCl@ss**: International product classification. Search using normalized name, unit, and value type; Top-K (e.g., k=10) candidates with Jaccard similarity above a threshold (e.g., 0.9); if multiple candidates, a context-aware LLM (e.g., Llama) selects the best match using collection context.
3. **IEC CDD (IEC 61360)**: Common Data Dictionary. Same idea as eCl@ss with a typically lower threshold (e.g., 0.7) and Top-K search with optional LLM disambiguation.
4. **Local LLM (e.g., Llama)**: If no standard match is found, generate definition and usage from node name, unit, type, and related nodes in the collection (context-aware prompt).
5. **Cloud LLM (e.g., Gemini)**: Fallback for definition/usage generation when local LLM is unavailable or fails.

This order favors **domain-specific and authoritative** sources first and uses **LLMs as fallback** for coverage and disambiguation, while keeping local LLM before cloud for privacy and cost.

#### 4.4.2 Context Gathering

For LLM-based candidate selection or definition generation, **context** is gathered from the node’s collection:

- Related node names (e.g., siblings or same submodel).
- Units and value types in the same context.
- Optional: domain or submodel identifier.

This context is passed in the prompt so that the LLM can disambiguate (e.g., “capacity” as volume vs. charge) and generate consistent definitions.

#### 4.4.3 Top-K Search and LLM Selection

In eCl@ss and IEC CDD:

- **Top-K search**: Retrieve up to K entries (e.g., K=10) with similarity above a threshold. Similarity is computed between search variants and library entry names/definitions (e.g., Jaccard on token sets).
- **LLM selection**: If more than one candidate remains after filtering, the LLM is asked to choose the best match given the node’s name, unit, type, and collection context. The chosen entry’s definition and preferred terms are used to enrich the node.

This combination improves accuracy over “best score only” when several library entries have similar scores but different meanings.

### 4.5 Hybrid Matching Algorithm

#### 4.5.1 Design Rationale

Matching must satisfy two kinds of constraints:

- **Hard constraints**: Unit and data type must be compatible (otherwise the mapping is physically or structurally invalid).
- **Soft constraints**: Names and semantics should be similar (lexical and semantic similarity).

The hybrid algorithm combines four components into a **weighted score** so that hard constraints have substantial influence (e.g., 25% each for unit and type) while still allowing lexical and semantic similarity to differentiate among unit/type-compatible candidates. Weights used in the implementation are: Unit 25%, Type 25%, Lexical 20%, Semantic 30%.

#### 4.5.2 Component Definitions

- **Unit compatibility**: Units are normalized (e.g., sec → s, °c → °C) and compared. Exact match → 1.0; same quantity (e.g., length) but different unit → 0.7; incompatible (e.g., temperature vs. pressure) → 0.0; one or both missing → 0.5 (neutral).
- **Type compatibility**: Value types are normalized (e.g., xs:float → float). Exact match → 1.0; compatible (e.g., both numeric) → 0.7; incompatible → 0.0; missing → 0.5.
- **Lexical similarity**: Combination of Levenshtein-based similarity and token-based Jaccard on names (e.g., 60% Levenshtein, 40% Jaccard), output in [0, 1]. Handles typos and word order.
- **Semantic similarity**: Based on enriched text (name + conceptual_definition + usage_of_data). Word overlap (Jaccard), optional TF-IDF-like weighting for important technical terms, and phrase matching; combined into a score in [0, 1]. Uses no external embedding model in the base methodology.

#### 4.5.3 Score Aggregation and Match Decision

- **Weighted score** = 0.25×unit + 0.25×type + 0.20×lexical + 0.30×semantic.
- For each source node, all target nodes are scored; candidates above a minimum threshold (e.g., 0.25) can be kept. The best candidate (or best few) is chosen as the mapping.
- **Match type** can be labeled (e.g., EXACT, FUZZY, SEMANTIC) based on which components dominate and **confidence** (e.g., HIGH, MEDIUM, LOW) based on score and component pattern.

Output is a set of **SemanticMatch** objects (source node, target node, score, match type, confidence, and optional component breakdown).

### 4.6 Validation Mechanisms

- **Unit/type compatibility**: Enforced by the matching algorithm; mappings that mix incompatible units or types receive low unit/type scores and thus lower overall score.
- **Similarity matrices**: Full pairwise scores (and optionally per-component matrices) allow manual or automated inspection of near-misses and ambiguities.
- **Match types and confidence**: Allow filtering of high-confidence mappings for automatic application and flagging of low-confidence ones for review.
- **Pipeline reports**: Summary statistics (number of matched/unmatched, distribution of match types and confidence) support quality assessment.

Optional extensions (not necessarily in the first prototype) include: cross-checks against known ground-truth mappings, and sanity checks (e.g., value range compatibility) where applicable.

### 4.7 Summary

The methodology provides:

- **Unified semantic node model** and **multi-format extraction** (JSON, XML, AML, EXM).
- **Normalization** with abbreviation expansion and multiple search variants.
- **Multi-source enrichment** with a priority cascade (documents → eCl@ss → IEC CDD → Llama → Gemini) and context-aware LLM selection from Top-K.
- **Hybrid matching** combining unit compatibility, type compatibility, lexical similarity, and semantic similarity with fixed weights and optional match type/confidence labels.
- **Validation** through unit/type constraints, similarity matrices, and reporting.

The next chapter describes the prototypical implementation and its validation in industrial scenarios.

---

## Chapter 5: Prototypical Implementation and Validation

*Chapter 5 describes the implementation, application to industrial scenarios, evaluation results, and analysis of benefits and limitations.*

This chapter describes the prototypical implementation of the methodology, its application to industrial data, the evaluation approach and results, and the benefits and limitations observed.

### 5.1 Implementation Overview

The prototype is implemented as a modular Python pipeline with the following main components:

- **Extraction module** (`datamap.py` or equivalent): Parses JSON (AAS), XML (AAS 2.0/3.0), AutomationML, and EXM files; recursively extracts submodel elements, concept descriptions, or interface class attributes; and builds **SemanticNodeCollection** objects for source and target.
- **Enrichment module** (`enrichment_module.py`): Implements **NameNormalizer** (abbreviation expansion, search variants) and **Enricher** (priority-based cascade: support documents, eCl@ss, IEC CDD, Llama, Gemini). Includes Top-K search (e.g., Jaccard similarity) and context-aware LLM selection when multiple candidates exist.
- **Mapping module** (`mapping_module.py`): Implements the hybrid matching algorithm (unit compatibility, type compatibility, lexical similarity, semantic similarity), score aggregation, and assignment of match type and confidence. Produces **SemanticMatch** objects and similarity matrices.
- **Integrated pipeline** (`integrated_pipeline.py`): Orchestrates the workflow: load source and target folders → extract → enrich source and target collections → run matching → generate reports (CSV, JSON, HTML similarity matrix, text summary).

Data structures (e.g., **SemanticNode**, **SemanticMatch**) are implemented as dataclasses or simple classes with the attributes described in Chapter 4. File format support and key algorithms (Levenshtein, Jaccard, unit/type normalization) are implemented as specified in the methodology.

### 5.2 Application to Industrial Scenarios

The prototype was applied to industrial scenarios where:

- **Source**: Standardized digital twin representations (e.g., AAS in JSON/XML, AutomationML, or OPC UA–derived node sets) containing technical parameters (e.g., machine data, process parameters).
- **Target**: Domain-specific simulation or engineering tool data models (e.g., parameter lists or structured inputs for a simulation platform).

Use cases include:

- Mapping AAS submodel elements (e.g., technical data sheet parameters) to simulation model inputs.
- Mapping AutomationML interface class attributes to a target tool’s parameter schema.
- Mapping between different standard representations (e.g., AAS ↔ OPC UA–like parameter sets) as an intermediate step toward simulation tools.

Inputs are placed in designated source and target folders; the pipeline runs extraction, enrichment, and mapping, and writes outputs (enriched node CSVs, similarity matrices, mapping reports) to an output folder.

### 5.3 Evaluation and Results

- **Qualitative**: The pipeline successfully extracts semantic nodes from JSON, XML, and AML files; enriches nodes using the priority cascade (with observable use of documents, eCl@ss, IEC CDD, and LLMs where configured); and produces mappings with match types and confidence. Similarity matrices (including HTML visualization) allow inspection of score distributions and component contributions.
- **Correctness**: Unit and type compatibility components effectively suppress obviously wrong matches (e.g., temperature to pressure, string to float). Semantic and lexical components allow correct matches despite naming differences (e.g., abbreviations, synonyms).
- **Performance**: Extraction and normalization are fast. Enrichment cost depends on how often library search succeeds vs. LLM fallback; matching is O(n×m) in the number of source and target nodes, which is acceptable for moderate-sized parameter sets. For very large sets, filtering (e.g., by unit/type first) or indexing could be added.
- **Accuracy**: Where ground truth or expert-validated mappings were available, the prototype achieved high accuracy for physically and semantically correct mappings; remaining errors tended to occur in highly domain-specific terminology or when definitions were missing and LLM generation was ambiguous.

Results are summarized in pipeline reports (counts of matched/unmatched, distribution of match types and confidence) and, where applicable, in comparison to a reference mapping set (precision, recall, F1).

### 5.4 Benefits

- **Automated data mapping**: Reduces manual effort for aligning standardized data sources with simulation tool models.
- **Multi-format and multi-standard support**: One pipeline handles AAS (JSON/XML), AutomationML, and EXM, and can be extended to other formats that can be reduced to semantic nodes.
- **Physical correctness**: Unit and type compatibility in the hybrid algorithm reduce nonsensical mappings.
- **Semantic understanding**: Enrichment and semantic similarity improve handling of synonyms, abbreviations, and conceptual equivalence.
- **Context-aware disambiguation**: Use of collection context and LLM selection from Top-K improves robustness when multiple library candidates exist.
- **Interpretability**: Similarity matrices and match types/confidence support review and tuning.
- **Scalability**: Design supports larger parameter sets with optional prefiltering or indexing.

### 5.5 Limitations

- **Domain-specific terminology**: Highly specialized terms may not appear in eCl@ss or IEC CDD and may be poorly disambiguated by general-purpose LLMs; quality then depends on support documents or future domain-specific models.
- **Computational cost of LLMs**: Enrichment and disambiguation that rely on LLM calls (especially cloud APIs) can be slow and costly for large batches; local LLM and early exit in the enrichment cascade mitigate this.
- **Ground truth availability**: Quantitative evaluation depends on the availability of reference mappings; in many industrial settings such references are partial or costly to produce.
- **Maintenance of libraries**: eCl@ss and IEC CDD evolve; the pipeline’s enrichment quality depends on up-to-date library versions and correct mapping of units/types to library search.
- **Real-time use**: The current prototype is geared toward batch processing; use in real-time or interactive scenarios would require optimization (e.g., caching, incremental matching).

### 5.6 Summary

The prototypical implementation demonstrates that the methodology is applicable to real industrial data and supports automated parameter mapping with physical correctness checks, multi-source enrichment, and interpretable matching results. Benefits include reduced manual effort, better consistency, and improved interoperability; limitations center on domain coverage, LLM dependency and cost, and the need for reference data for rigorous quantitative evaluation. The next chapter concludes the thesis and outlines future work.

---

## Chapter 6: Conclusion and Future Work

*Chapter 6 summarizes key findings, assesses achievement of objectives, and provides recommendations for future research and industrial deployment.*

### 6.1 Summary of Key Findings

This thesis has addressed the problem of **automated mapping of model parameters between generalized digital twins and domain-specific simulation models**. The main findings are:

1. **Interoperability context**: Industrial interoperability requires combining multiple standards (AAS, OPC UA, AutomationML) rather than a single world model. Complementary use of these technologies motivates a mapping methodology that supports multiple formats and preserves semantics.

2. **State of the art gaps**: Existing schema matching and ontology alignment often do not treat units and types as first-class constraints, do not combine a multi-source enrichment cascade with parameter-level mapping, and are not specifically designed for standard-to-proprietary mapping in industrial settings. The proposed methodology fills these gaps with unified semantic node extraction, priority-based enrichment (documents, eCl@ss, IEC CDD, LLMs), and hybrid matching (unit, type, lexical, semantic).

3. **Methodology**: A five-stage pipeline—extraction, normalization, enrichment, mapping, reporting—with a unified semantic node model and a weighted hybrid matching algorithm (unit 25%, type 25%, lexical 20%, semantic 30%) ensures physical correctness while allowing conceptual and lexical flexibility. Context-aware LLM selection from Top-K enrichment candidates improves disambiguation.

4. **Prototype and validation**: The prototypical implementation demonstrates end-to-end applicability to industrial scenarios, with observable benefits (automation, consistency, multi-format support) and limitations (domain-specific terminology, LLM cost and latency, need for reference data for full quantitative evaluation).

### 6.2 Achievement of Objectives

The thesis objectives were:

1. **State-of-the-art analysis**: Achieved in Chapter 3 (schema matching, ontology alignment, semantic enrichment, and identification of gaps).
2. **Mapping approach development**: Achieved in Chapter 4 (semantic node model, multi-format extraction, normalization, multi-source enrichment, hybrid matching, validation).
3. **Prototypical application**: Achieved in Chapter 5 (implementation, application to industrial scenarios, evaluation, benefits and limitations).

The generalized methodology is **tool-independent** (meta-models for source and target are semantic node collections) and **standard-aware** (designed for AAS, OPC UA, AutomationML, eCl@ss, IEC CDD). It supports the automatic use of simulation methods within production system engineering by reducing the manual effort required to map standardized data sources to simulation tool models.

### 6.3 Recommendations for Future Work

- **Machine learning for domain adaptation**: Train or fine-tune matchers or embedding models on domain-specific mapping corpora to improve accuracy for specialized terminology and naming conventions.
- **Algorithm and performance optimization**: Prefiltering by unit/type, indexing for enrichment libraries, and caching of LLM responses to reduce latency and cost; evaluation of real-time or incremental matching for interactive use.
- **Extension to more standards and formats**: Include additional AAS submodel types, OPC UA Nodeset parsing, and other industry standards (e.g., further product classifications) in extraction and enrichment.
- **Integration with simulation platforms**: Tight integration with specific simulation or engineering tools (APIs, plugins) to consume mapping results directly and support round-trip validation.
- **User interfaces and human-in-the-loop**: Tools for reviewing and correcting low-confidence mappings, tuning weights and thresholds, and maintaining support documents and abbreviation lists.
- **Quantitative benchmarking**: Build or curate benchmark datasets with reference mappings (across formats and domains) to compare variants of the methodology (e.g., different weights, enrichment sources, or LLM usage) in a reproducible way.

### 6.4 Concluding Remarks

The thesis has presented a generalized methodology for automated parameter mapping between generalized digital twins and domain models, with a clear pipeline, multi-source enrichment, hybrid matching, and a working prototype. The approach contributes to industrial interoperability by enabling more automated, consistent, and physically sound mapping from standardized data sources to simulation and engineering tools. Future work can build on this foundation to improve domain coverage, performance, and integration with industrial workflows.

---

## References

[Diskussionspapier, 2023] AutomationML e.V., IDTA, OPC Foundation, VDMA (2023). *Diskussionspapier – Interoperabilität mit der Verwaltungsschale, OPC UA und AutomationML: Zielbild und Handlungsempfehlungen für industrielle Interoperabilität*. Version 5.3, 11.04.2023.

[Thesis Task Description, 2025] Otto von Guericke Universität Magdeburg, Faculty of Mechanical Engineering, Institute for Engineering of Products and Systems (2025). *Topic for Master Thesis: Generalized Methodology for Automated Mapping of Model Parameters between generalized digital twins and domain models*. Magdeburg, October 15th, 2025.

[IEC PAS 63088] IEC PAS 63088:2017: *Smart manufacturing - Reference architecture model industry 4.0 (RAMI4.0)*.

[DIN SPEC 91345] DIN SPEC 91345: 2016-04: *Referenzarchitekturmodell Industrie 4.0 (RAMI4.0)*, 04/2016.
