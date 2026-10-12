# MiniCloud — Project Report Outline & Chapter Blueprint

Use this formal outline when preparing the project documentation report for submission to the computer engineering department.

---

## Preliminary Pages
1. **Title Page** (MiniCloud: Cloud for Software as a Service over Laboratory LAN using HDFS)
2. **Certificate of Approval** (Signed by Guide and Head of Department)
3. **Declaration by Student**
4. **Acknowledgement**
5. **Abstract**
6. **Table of Contents**
7. **List of Figures** (Mermaid architecture diagrams, schema, sequence diagrams)
8. **List of Tables** (Technology versions, API endpoints, troubleshooting guide)

---

## Chapter 1: Introduction
- 1.1 Background of Cloud Computing (SaaS vs IaaS vs PaaS)
- 1.2 Problem Statement & Motivation
- 1.3 Objectives of the Mini-Project
- 1.4 Scope and Target Audience (Academic Laboratory LAN)
- 1.5 Organization of the Report

---

## Chapter 2: Literature Survey & Theoretical Concepts
- 2.1 Overview of Apache Hadoop and Distributed File Systems
- 2.2 HDFS Architecture: NameNode, DataNodes, Block Management, and Replication
- 2.3 The WebHDFS REST Specification & Two-Step Upload Protocol
- 2.4 Cloud Controller Concept in Private Clouds (Comparison with OpenStack/Eucalyptus)
- 2.5 Modern Frontend Frameworks: React 18, Vite, and Component-Driven Glassmorphism

---

## Chapter 3: System Requirements & Architecture Design
- 3.1 Hardware and Software Requirements
- 3.2 High-Level System Architecture (Three-Tier Client-Controller-Storage)
- 3.3 Storage Layer Abstraction: `StorageBackend` Class Diagram
- 3.4 Data Flow Diagrams (Upload Protocol, Streaming Download Protocol)
- 3.5 Database Design & Entity Relationship (ER) Diagram
  - Virtual Folder Abstraction
  - Flat UUID Storage Strategy
  - SQLite WAL (Write-Ahead Logging) & Foreign Key Constraints

---

## Chapter 4: Implementation Details
- 4.1 Cloud Controller Implementation (Python, Flask, Waitress)
- 4.2 WebHDFS Integration (`HdfsStorage.py` and `MockStorage.py`)
- 4.3 Consistency Protocol & Rollback Mechanism
- 4.4 Authentication, Token Revocation, and Role-Based Access Control (RBAC)
- 4.5 User Storage Quota Accounting
- 4.6 Frontend Implementation (React, Tailwind CSS, Recharts, Lucide Icons)
- 4.7 Single-Port Deployment and Static Asset Serving

---

## Chapter 5: LAN Networking & Multi-Node Cluster Configuration
- 5.1 Single-Port LAN Deployment (`http://<HOST_IP>:5000`)
- 5.2 Windows Firewall Rules and Subnet Binding
- 5.3 WebHDFS 307 Redirection & DataNode Hostname Resolution
- 5.4 Multi-Node Cluster Configuration (Replication Factor = 2)
- 5.5 FSCK Verification & Block Distribution Analysis

---

## Chapter 6: Testing & Experimental Results
- 6.1 Testing Methodology (Separation of Mock vs Real HDFS)
- 6.2 Automated Unit Testing with Pytest (Auth, Quota, Isolation, File CRUD)
- 6.3 HDFS Standalone Smoke Testing (`hdfs_smoke_test.py`)
- 6.4 Metadata Reconciliation & Orphan Recovery (`reconcile.py`)
- 6.5 Failure Injection Results (Handling NameNode and DataNode Offline Scenarios)
- 6.6 Performance and Responsiveness over 100 Mbps / Wi-Fi LAN

---

## Chapter 7: Conclusion & Future Enhancements
- 7.1 Summary of Work Done
- 7.2 Achievement of Project Objectives
- 7.3 Limitations of the Current Prototype
- 7.4 Scope for Future Development (File Versioning, Kerberos, Public Link Sharing)

---

## References / Bibliography
- Apache Hadoop HDFS Architecture Documentation
- WebHDFS REST API Specification (RFC 2616 / Hadoop Documentation)
- Flask and Werkzeug Security Documentation
- React 18 and Tailwind CSS Design Patterns
