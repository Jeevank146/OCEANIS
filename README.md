@'
# OCEANIS — Ocean Intelligence & Decision System

> **Turning Ocean Data into Intelligent Decisions.**

OCEANIS is an AI-powered marine intelligence and decision-support platform designed to integrate marine observations, satellite Earth Observation, weather, ocean conditions, geospatial intelligence, safety information, and Potential Fishing Zone (PFZ) intelligence into a single decision-support workflow.

## SIH 2026

- **Problem Statement:** SIH26176 — ORCA: Marine Ecosystem Reasoning with Collaborative Agents
- **Theme:** Disaster Management
- **Category:** Software
- **Project:** OCEANIS — Ocean Intelligence & Decision System

## What OCEANIS Does

OCEANIS follows an intelligence workflow:

**UNDERSTAND → PLAN → RETRIEVE → REASON → SIMULATE → EXPLAIN → RECOMMEND → ALERT**

The platform combines real marine data with six specialized domain agents and a decision/safety layer to provide evidence-backed marine intelligence.

## Six Domain Agents

1. **Fishing Intelligence Agent**
   - PFZ intelligence and fishing suitability
   - SST and chlorophyll-based indicators
   - Fishing-ground comparison
   - Safety-aware fishing recommendations

2. **Marine Conditions Agent**
   - Wind and atmospheric conditions
   - Waves and swell
   - Ocean currents
   - SST and marine conditions

3. **Earth Observation Agent**
   - Satellite-derived marine intelligence
   - SST and chlorophyll-a
   - Spatial and temporal analysis
   - Ocean-condition indicators

4. **Geo-Spatial & Navigation Agent**
   - Coordinates and spatial queries
   - Maritime boundaries
   - Restricted/protected areas
   - Routes, distance and spatial intersections

5. **Disaster & Safety Agent**
   - Marine warnings and hazards
   - Cyclone and severe-weather intelligence
   - Hazard-zone assessment
   - Safety-first decision support

6. **Marine Operations Agent**
   - Route planning
   - Travel distance and estimated time
   - Departure-time analysis
   - Operational what-if scenarios

The **Agent Orchestrator** coordinates these domain agents and is not counted as a seventh domain agent.

## Intelligence Architecture

```text
User Query / Location
        ↓
Intent & Query Understanding
        ↓
Agent Orchestrator
        ↓
Six Domain Agents
        ↓
Real Marine Data Retrieval
        ↓
Evidence Fusion
        ↓
Freshness & Confidence Assessment
        ↓
Safety Guardrails
        ↓
Risk / Decision Engine
        ↓
What-If Simulation
        ↓
Explainable Recommendation