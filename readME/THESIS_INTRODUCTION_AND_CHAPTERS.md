# Introduction and Chapters 1-2

## Introduction

The digital transformation of manufacturing industries, commonly referred to as Industry 4.0, represents a paradigm shift towards intelligent, interconnected production systems. This transformation is driven by the integration of Internet technologies into industrial processes, aiming to unlock new value creation potential through networking and digitalization [Diskussionspapier, 2023]. However, achieving true interoperability in industrial environments remains a significant challenge, as industrial assets such as machines, components, and production systems are far from achieving the "Plug & Play" functionality that is commonplace in consumer IT devices.

The automation of automation engineering has emerged as a highly relevant research topic, with efficiency and effectiveness in production system engineering being crucial for economic success in manufacturing [Thesis Task Description, 2025]. A core challenge in this domain is the identification and utilization of appropriate data sources, where relevant data must be mapped to the internal data models of engineering automation algorithms for each application. As data sources increasingly adopt standardized structures through initiatives such as the Industrial Digital Twin Association (IDTA), OPC Foundation, and AutomationML Association, the need for automated mapping methodologies becomes paramount.

Simulation-based engineering decisions play a key role in automating engineering processes. However, these simulations often rely on tool-specific, proprietary data models that need to be populated with data from standardized sources. The master's thesis addresses this fundamental problem: **How can model parameters be automatically mapped between generalized digital twins (represented by standardized data sources) and domain-specific simulation models (represented by proprietary tool data models)?**

This thesis presents a generalized methodology for automated mapping of model parameters between generalized digital twins and domain-specific simulation models. The work is situated within the broader context of industrial interoperability, where three key technologies—Asset Administration Shell (AAS), OPC UA with its Companion Specifications, and AutomationML—are recognized as Industry 4.0 key technologies recommended by the Platform Industrie 4.0 [Diskussionspapier, 2023]. Rather than competing with each other, these technologies complement one another and together create comprehensive concepts for unified digital interoperability between Industry 4.0-capable machines and systems throughout their entire lifecycle.

The methodology developed in this thesis addresses the challenge of bridging standardized data sources with proprietary simulation tool data models through a three-part approach: (1) comprehensive state-of-the-art analysis of simulation systems, standardized data sources, and mapping technologies; (2) development of a novel hybrid semantic matching approach; and (3) prototypical implementation demonstrating the methodology's applicability.

This work contributes to the vision of avoiding duplicate standardization and multiple digital models that require duplicate data storage and software development, which would hinder a harmonized and efficient digital value chain. By providing automated mapping capabilities, the methodology enables seamless data exchange and automated engineering decision support, ultimately contributing to the realization of Industry 4.0 objectives.

---

## Chapter 1: Interoperability in Industry 4.0

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

This thesis addresses the automated mapping challenge through a generalized methodology that enables the identification and application of standardized data sources to facilitate the automatic use of simulation methods within production system engineering. The work is structured into three main parts:

1. **State-of-the-Art Analysis**: Evaluation of current simulation systems, standardized production system-related data sources, and data mapping methodologies
2. **Mapping Approach Development**: Conceptual development of a tool-independent mapping methodology with meta-models for both data source and simulation sides
3. **Prototypical Application**: Demonstration of the methodology through an example simulation system and production system with selected data sources

The following chapters provide the theoretical foundation and context for this work, beginning with an overview of the key technologies for industrial interoperability.

---

## Chapter 2: Key Technologies for Industrial Interoperability

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

The next chapter will present the state-of-the-art analysis of simulation systems, standardized data sources, and existing mapping technologies, building upon the foundation established in this chapter.

---

## References

[Diskussionspapier, 2023] AutomationML e.V., IDTA, OPC Foundation, VDMA (2023). *Diskussionspapier – Interoperabilität mit der Verwaltungsschale, OPC UA und AutomationML: Zielbild und Handlungsempfehlungen für industrielle Interoperabilität*. Version 5.3, 11.04.2023.

[Thesis Task Description, 2025] Otto von Guericke Universität Magdeburg, Faculty of Mechanical Engineering, Institute for Engineering of Products and Systems (2025). *Topic for Master Thesis: Generalized Methodology for Automated Mapping of Model Parameters between generalized digital twins and domain models*. Magdeburg, October 15th, 2025.

[IEC PAS 63088] IEC PAS 63088:2017: *Smart manufacturing - Reference architecture model industry 4.0 (RAMI4.0)*.

[DIN SPEC 91345] DIN SPEC 91345: 2016-04: *Referenzarchitekturmodell Industrie 4.0 (RAMI4.0)*, 04/2016.
