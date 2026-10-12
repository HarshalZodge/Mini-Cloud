# MiniCloud — 5-Minute Live Demonstration Script

Use this exact chronological script when presenting and defending MiniCloud before professors and external examiners.

---

## Equipment Setup Before Examiners Arrive:
1. **Host Computer**:
   - Terminal 1: Waitress running via `powershell -ExecutionPolicy Bypass -File .\scripts\run-lan-server.ps1`.
   - Browser tab open to: `http://localhost:5000` (or `http://<HOST_IP>:5000`).
2. **Second Computer or Phone**:
   - Connected to the same lab Wi-Fi/LAN, with browser ready to navigate to `http://<HOST_IP>:5000`.
3. **Hadoop Cluster (if in real HDFS mode)**:
   - Ubuntu VM running Hadoop with `jps` displaying `NameNode` and `DataNode`.

---

## Minute 0:00 – 1:00: Problem & Architecture Introduction
- **What to say:**
  > *"Respected examiners, our project is MiniCloud: an on-premise Software as a Service private cloud storage solution built over our laboratory LAN.
  > Instead of using third-party public clouds, we built our own Cloud Controller in Python/Flask that communicates directly with an Apache Hadoop HDFS cluster using the WebHDFS REST API.
  > The frontend is an offline-ready React 18 Single Page Application featuring a glassmorphism interface with dark mode. Everything is served over a single port—port 5000—so any computer in this laboratory can use it without installing anything."*
- **What to show:**
  - Point to the active storage badge in the top bar: **"HDFS ACTIVE"** (or **"MOCK MODE"** for local dev).
  - Toggle light and dark mode in the top right to demonstrate theme responsiveness.

---

## Minute 1:00 – 2:00: Multi-User Isolation & File Operations
- **What to say:**
  > *"Let's log in as the administrator and look at the dashboard. All these metrics—storage quota progress bar, recent files, and the Recharts file-type breakdown—come dynamically from the Cloud Controller API."*
- **What to show:**
  1. Open **My Files**. Click **New Folder**, name it `Lab_Assignments`.
  2. Drag and drop two files (e.g. a PDF and an image) into the upload drop zone.
  3. Show the animated progress bar completing per file.
  4. Double click `Lab_Assignments` to demonstrate virtual folder navigation and breadcrumbs.
  5. Star one file, download the other (highlighting that the SHA-256 hash matches byte-for-byte).
  6. Switch between **List View** and **Grid View**.

---

## Minute 2:00 – 3:00: The 6-Step Consistency Protocol & Trash Lifecycle
- **What to say:**
  > *"A critical requirement of our Cloud Controller is storage consistency. We don't store folders on HDFS; folders are virtual in SQLite. Files in HDFS are stored flat using UUIDs.
  > When we upload a file, the controller validates the user quota, writes a 'pending' row, streams bytes to WebHDFS, verifies length, and only then marks it 'ready'.
  > If anything fails mid-stream, the controller automatically deletes the partial HDFS block and rolls back the database row."*
- **What to show:**
  1. Delete a file: show it move to **Trash**.
  2. Navigate to the **Trash** page: explain that trashed files still count against quota until permanently deleted.
  3. Click **Restore**: the file reappears in My Files.
  4. Delete it again and click **Empty Trash** with the confirmation modal.

---

## Minute 3:00 – 3:45: LAN Demonstration from Second Device
- **What to say:**
  > *"Now let's demonstrate the multi-computer LAN capability. Notice that my phone / second laptop is on the same lab network."*
- **What to show:**
  1. On the second device, open the browser and navigate to `http://<HOST_IP>:5000`.
  2. Register a new student account (`student1`).
  3. Point out that `student1` automatically gets the `user` role, whereas the first registered user was `admin`.
  4. Show that `student1` sees an empty directory, proving complete **multi-tenant isolation** (User B cannot see or touch User A's files).

---

## Minute 3:45 – 4:30: Admin Telemetry & NameNode JMX
- **What to say:**
  > *"Because our account on the primary machine has the admin role, we have access to the Cluster page."*
- **What to show:**
  1. Navigate to **Cluster Status (Admin)**.
  2. Show the live cards: **Live DataNodes**, **Total HDFS Blocks**, **Replication Factor**, and **Total Storage Pool**.
  3. Explain: *"These metrics are polled live by the Cloud Controller from the NameNode JMX endpoint at `/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState`."*

---

## Minute 4:30 – 5:00: Intentional Failure & Error Handling (Viva Climax)
- **What to say:**
  > *"Finally, examiners often ask: what happens if HDFS crashes? Does the controller silently write to local disk? The answer is no."*
- **What to show:**
  1. In the terminal, show the result of querying an offline HDFS cluster:
     The controller strictly returns `HTTP 503 Storage Unavailable` with a clear message: `Unable to reach HDFS NameNode at <IP>:9870`.
  2. Conclude:
     > *"MiniCloud strictly enforces error boundaries, protects student data, and delivers an authentic cloud storage experience over an institutional LAN. We are now ready for your questions."*
