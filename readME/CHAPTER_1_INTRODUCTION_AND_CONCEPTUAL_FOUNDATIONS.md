# Chapter 1: Introduction and Conceptual Foundations

---

## 1.1 The Industrial Context

The digital transformation of manufacturing, commonly referred to as Industry 4.0, represents a paradigm shift toward intelligent, interconnected production systems. This transformation is driven by the integration of Internet technologies into industrial processes, with the aim of unlocking new value creation through networking and digitalisation [1]. Achieving true interoperability in industrial environments nevertheless remains a central challenge: industrial assets such as machines, components, and production systems are far from the “plug and play” behaviour typical of consumer IT [1]. Interoperability is therefore not only a technical goal but the enabling condition for modern smart factories that must integrate data and systems across vendors, lifecycle phases, and domains.

Interoperability is defined as the ability of systems, devices, and applications to connect and communicate purposefully across manufacturers, encompassing both Operational Technology (OT) and Information Technology (IT) [1]. In the context of Industry 4.0, this requires deep software integration of assets and systems along multiple dimensions. The Reference Architecture Model Industry 4.0 (RAMI4.0) illustrates this scope: it provides a three-dimensional frame for interoperability across hierarchy levels (from product to connected world), the value stream (lifecycle from development to maintenance), and enterprise layers (from business to functional to asset) [3], [4]. This view underscores that seamless data exchange in industry is significantly more complex than in consumer IT, where standards such as Ethernet, USB, and common driver architectures already provide largely manufacturer-independent communication [1].

Industrial systems have evolved through a mix of proprietary and standardised solutions tailored to specific use cases. The resulting heterogeneity creates barriers to interoperability across manufacturers, lifecycle phases, and domains (mechanical, electrical, automation, IT), as well as across different standardisation initiatives [1]. Addressing these challenges is a prerequisite for the economic benefits expected from Industry 4.0, where efficiency and effectiveness in production system engineering depend on the ability to identify and use appropriate data sources and to map them into the internal data models of engineering and automation algorithms [2].

---

## 1.2 Problem Statement

A core difficulty in this setting is that relevant data must be mapped to the internal data models of engineering automation algorithms for each application [2]. As data sources increasingly adopt standardised structures—through initiatives such as the Industrial Digital Twin Association (IDTA), the OPC Foundation, and the AutomationML Association—the need for systematic mapping between these standards and proprietary tool models grows [2]. Simulation-based engineering decisions play a key role in automating engineering processes, yet simulations typically rely on tool-specific, proprietary data models that must be populated from standardised sources [2]. The central problem addressed in this thesis is therefore: *How can model parameters be automatically mapped between generalised digital twins (represented by standardised data sources such as AAS and OPC UA) and domain-specific simulation models (represented by proprietary tool data models)?*

Today, this mapping is largely manual. Manual mapping is time-consuming, requires expert knowledge, and does not scale to large numbers of parameters and models; it is also error-prone and maintenance-intensive when sources or target models change [1]. Data integration and parameter mapping between different industrial standards (e.g. Asset Administration Shell, OPC UA with Companion Specifications, AutomationML) and proprietary simulation or engineering tools therefore impose a sustained manual effort that limits scalability and consistency. Automated mapping methodologies are needed to reduce this effort, improve consistency, enable scalability, and support maintenance as models evolve [1].

---

## 1.3 The Role of Standardisation

Interoperability in Industry 4.0 is not achieved by a single global model but by the coordinated use of complementary standards, each developed and maintained within its domain of competence [1]. Three technologies are recognised as key for Industry 4.0 and are recommended by the Platform Industrie 4.0: the Asset Administration Shell (AAS), OPC UA with its Companion Specifications, and AutomationML [1]. When applied in a complementary rather than competing manner, they avoid duplicate work, reduce overlapping models, reduce development effort, and enable cross-domain interoperability through a clear division of roles [1].

The risk of duplicate standardisation is a critical concern: when several technologies (AAS Submodels, AutomationML, OPC UA Companion Specifications) all aim to provide harmonised information models, they could compete and lead to duplicate modelling, duplicate data storage, duplicate software development, and fragmented value chains [1]. The joint position of AutomationML e.V., IDTA, OPC Foundation, and VDMA is that proprietary or closed interoperability solutions are not sustainable and that standardised, complementary solutions should be prioritised [1]. In this sense, the adoption of complementary standards—each serving a defined purpose (lifecycle-spanning product information, operational data access, engineering data exchange)—constitutes a matured, sustainable approach to addressing interoperability, analogous to relying on well-defined routes and interfaces rather than ad hoc, duplicate solutions.

To achieve interoperability, assets and services must provide standardised data models (e.g. via AAS Submodel Templates, AutomationML, and OPC UA Companion Specifications) and expose them through standardised interfaces such as OPC UA [1]. The AAS, in particular, serves as a digital lifecycle file that authorised stakeholders—from sales to service, across company boundaries—can access [1]. This role of standardisation as the foundation for interoperability motivates the present work: automated mapping must operate across these standardised sources and proprietary targets while preserving semantics and avoiding duplicate modelling.

---

## 1.4 Research Objectives

This thesis aims to develop and demonstrate a generalised methodology for the automated mapping of model parameters between generalised digital twins and domain-specific simulation models. The specific research objectives are:

1. **State-of-the-art analysis:** To evaluate current simulation systems, standardised production-system-related data sources, and data mapping methodologies, and to identify gaps that an automated mapping methodology should address.

2. **Mapping approach development:** To design a tool-independent mapping methodology with meta-models for both the data-source side and the simulation side, including semantic node extraction, multi-source enrichment, and hybrid matching that respects units, types, and semantics.

3. **Prototypical application:** To implement and validate the methodology using representative industrial data (e.g. AAS, OPC UA–derived, or AutomationML sources and simulation or engineering tool targets), and to report on benefits and limitations.

4. **Contribution to interoperability:** To support the vision of avoiding duplicate standardisation and redundant digital models, and to enable more seamless data exchange and automated engineering decision support in line with Industry 4.0 objectives [1], [2].

The remainder of the thesis is structured as follows. Chapter 2 presents the technical background on AAS, OPC UA, and AutomationML. Chapter 3 reviews the state of the art in data mapping and semantic technologies. Chapter 4 describes the developed methodology. Chapter 5 presents the prototypical implementation and validation. Chapter 6 concludes and outlines future work.

---

## Constraint check and reference note

- **RAMI4.0:** The RAMI4.0 framework is standardised in IEC PAS 63088 [3] and DIN SPEC 91345 [4]. These standard documents are **not** in the current library. When you add them, verify the three-dimensional structure (Hierarchy Levels, Value Stream, Layers) and any quoted wording against the originals.

- **Platform Industrie 4.0:** The thesis documents state that AAS, OPC UA, and AutomationML are recommended by the Platform Industrie 4.0 and cite [1] for this. If [1] in turn cites a specific Platform Industrie 4.0 publication, consider adding that publication to your library and citing it directly where you use this claim.
