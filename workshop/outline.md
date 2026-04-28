# WIS2Box Workshop Outline

## 1. Introduction
### 1.1 Introduction to WMO WIS2 system
1. What is WMO WIS2 system
2. Why WMO WIS2 system
3. How WMO WIS2 system works

### 1.2 Datasets published in WIS2

1. What datasets we published 
2. What is BUFR format
3. How to generate BUFR files from source data

## 2. Architecture of WIS2 SYSTEM
### 2.1 High Level Architecture
```mermaid
graph LR
    Producer[Data Producer] -->|Data| Node[WIS 2.0 Node]
    Node -->|Metadata & Notifications| Broker[Global Broker]
    Broker -->|Discovery| Cache[Global Cache]
    Cache -->|Discovery| Consumers[Data Consumers]
```

### 2.2 Publication of WIS2 Stations with WIGOS ID

```mermaid
flowchart LR
    A[Facility Team] -->|WIGOS ID| B[OceanOPS]
    B -->|Activate WIGOS ID| C[Oscar]
    A -->|WIGOS ID| D[IMOS Data Engineer]
    D -->|Validate IDs| B
    D -->|Validate IDs| C
    D -->|Create/modify the station table| E[WIS2box-AODN Repo]
    E -->|Push to WIS2box Management Service| F[Publish to IMOS WIS2 Node]
```
