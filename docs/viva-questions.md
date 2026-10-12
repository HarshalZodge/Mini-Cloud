# MiniCloud Viva Voce Examination Questions & Answers

This guide contains 28 viva questions covering every architectural layer of MiniCloud, specifically tailored for computer engineering viva defenses.

---

### Q1: What makes MiniCloud a "Software as a Service" (SaaS) and not IaaS or PaaS?
**Answer:** In Infrastructure as a Service (IaaS), users manage raw VMs and virtual disks (e.g. AWS EC2). In Platform as a Service (PaaS), users deploy code runtimes (e.g. Heroku). In MiniCloud, users do not interact with VMs, operating systems, or raw HDFS blocks; they simply interact with an end-user cloud application (uploading, organizing, and downloading files via a browser) hosted on the lab network. Hence, it is pure SaaS.

---

### Q2: What is the specific role of the "Cloud Controller" in your project?
**Answer:** The Cloud Controller is the central orchestrator (built in Python/Flask). It performs authentication, enforces storage quotas, translates user-friendly virtual folder structures into flat HDFS block paths, queries NameNode JMX telemetry, and coordinates multi-step WebHDFS transactions while shielding clients from direct HDFS interaction.

---

### Q3: How does this Cloud Controller compare to controllers in OpenStack or Eucalyptus?
**Answer:** In OpenStack, the controller (Nova/Swift API) translates tenant REST calls into backend virtualization hypervisor or storage actions while maintaining tenancy in MySQL. MiniCloud works on the identical principle: our Flask controller acts as the control plane between browser SaaS clients and raw HDFS DataNodes while maintaining multi-tenant metadata in SQLite.

---

### Q4: Why use HDFS for file storage instead of just storing files on the local filesystem?
**Answer:** The local filesystem is limited to a single physical disk on one computer. HDFS is a distributed filesystem designed for high fault tolerance, automatic block replication across commodity nodes, horizontal scalability, and massive storage aggregation across multiple machines in a network.

---

### Q5: What are NameNodes and DataNodes in HDFS?
**Answer:** 
- **NameNode**: The master node that manages the filesystem namespace, directory tree, and block locations in RAM (persisted in FSImage and EditLogs). It does not store actual file data.
- **DataNode**: The worker nodes that store and retrieve raw blocks on local disks as instructed by the NameNode or client.

---

### Q6: Why is the default block size in HDFS 128 MB (compared to 4 KB in ext4/NTFS)?
**Answer:** Traditional filesystems use 4 KB to minimize internal fragmentation for small files. HDFS is designed for massive datasets (gigabytes to terabytes). A large block size (128 MB) minimizes disk seek time so that data transfer time dominates seek overhead, and significantly reduces the memory footprint of metadata on the NameNode (each block metadata entry takes ~150 bytes in NameNode RAM).

---

### Q7: What is WebHDFS and why did you use it?
**Answer:** WebHDFS is an HTTP REST API defined for HDFS that allows external non-Java applications to perform complete filesystem operations (create, open, delete, mkdir) using standard HTTP verbs (`GET`, `PUT`, `DELETE`). It allows our Python Flask controller to read and write blocks to Hadoop without requiring heavy Java native libraries or RPC wrappers.

---

### Q8: Explain the two-step WebHDFS upload protocol. Why is there a 307 redirect?
**Answer:** 
1. Step 1: The controller issues `PUT ...?op=CREATE` to the NameNode. The NameNode checks permissions and namespace, selects the target DataNodes for block placement, and replies with an HTTP `307 Temporary Redirect` containing the selected DataNode's URL in the `Location` header.
2. Step 2: The controller streams the actual file bytes directly to the DataNode URL.
This architecture prevents the NameNode from becoming a network bottleneck because actual file data never travels through the NameNode.

---

### Q9: What is the "DataNode hostname problem" and how did you resolve it?
**Answer:** In WebHDFS, the NameNode's 307 redirect header typically contains the DataNode's internal hostname (e.g. `http://datanode1:9864/...`). External clients or the Windows controller host often cannot resolve internal VM hostnames. We resolved this by setting `dfs.client.use.datanode.hostname=true` and adding VM IP mappings into the Windows `hosts` file (`C:\Windows\System32\drivers\etc\hosts`).

---

### Q10: Why are folders in MiniCloud "virtual" and not created on HDFS?
**Answer:** Folders are stored purely in the SQLite `folders` table. Files on HDFS are stored in a flat path: `/minicloud/users/{user_id}/files/{uuid4}{extension}`. This ensures:
1. Renaming or moving a folder is an $O(1)$ database update that takes milliseconds, avoiding expensive recursive renames in HDFS.
2. User-controlled folder names never reach HDFS, eliminating directory traversal attacks.
3. Trash operations are instantaneous soft-deletes.

---

### Q11: Explain MiniCloud's 6-step Upload Consistency Protocol.
**Answer:**
1. Pre-validation: checks user quota, folder ownership, and blocked extensions (`.exe`, `.bat`).
2. Insert a database record with `status='pending'`.
3. Stream bytes to storage and compute SHA-256 hash simultaneously.
4. Verify uploaded byte length via `stat()`.
5. Update database record to `status='ready'` with SHA-256 and final size.
6. Atomic rollback: on any connection loss or failure, the partial storage file is deleted and the pending DB row is removed, guaranteeing zero orphaned data.

---

### Q12: How does MiniCloud enforce multi-tenant isolation?
**Answer:** Every database query and storage path is partitioned by `user_id` extracted from the cryptographically verified JWT token. If User B attempts to access `/api/files/{id}` owned by User A, the controller returns `404 Not Found` (not 403) so User B cannot even deduce the existence of User A's files.

---

### Q13: How is user storage quota calculated and enforced?
**Answer:** A user's used space equals the sum of `file_size` for all of their files with `status='ready'`, including those in Trash, until permanently purged. Quota is checked *before* upload starts using `Content-Length` and re-verified after upload finishes.

---

### Q14: Why do downloads use signed download tokens instead of standard Bearer headers?
**Answer:** Standard browser file download triggers (such as `window.open` or plain `<a href="...">` links) cannot attach custom `Authorization: Bearer <token>` headers. We implement a two-step mechanism: the client requests a short-lived (60s), single-use signed token via `POST /api/files/{id}/download-token`, and then triggers the download via `GET /api/files/{id}/download?token=...`.

---

### Q15: Why use JWT (JSON Web Tokens) instead of server-side sessions?
**Answer:** JWT is stateless. The client holds the signed token, and the backend validates it using `JWT_SECRET_KEY` without querying the database for every single request. For logout, we implement a `token_blocklist` table that stores the unique token `jti` until token expiration, providing immediate invalidation.

---

### Q16: Why did you choose SQLite over MySQL or PostgreSQL?
**Answer:** SQLite is serverless, zero-configuration, and stores the entire database in a single file (`minicloud.db`), making it ideal for a reproducible academic demonstration. By enabling WAL mode (`PRAGMA journal_mode=WAL;`) and foreign keys (`PRAGMA foreign_keys=ON;`), SQLite supports concurrent readers alongside a writer with high performance.

---

### Q17: What does SQLite WAL (Write-Ahead Logging) mode do?
**Answer:** In default rollback journal mode, writing locks the entire database, blocking readers. In WAL mode, changes are appended to a separate `-wal` file. Readers read from the main database while writers append to the WAL log concurrently, significantly improving responsiveness in web applications.

---

### Q18: What is the purpose of the `reconcile.py` script?
**Answer:** It is a disaster recovery and audit utility. It scans both the SQLite database and the physical storage directory, detecting:
- **Ghost records**: DB rows that point to files missing from storage.
- **Orphan files**: Physical storage objects that have no corresponding database record.
Running with `--fix` cleanly purges both inconsistencies.

---

### Q19: Why does the system never silently fall back from HDFS to local disk?
**Answer:** Silent fallback hides infrastructure failures and misleads administrators into thinking distributed storage is working when it is actually filling up the local disk. When `STORAGE_BACKEND=hdfs` is set and HDFS is unreachable, MiniCloud strictly returns HTTP `503 Storage Unavailable`.

---

### Q20: What is the difference between pseudo-distributed and fully distributed HDFS?
**Answer:** 
- **Pseudo-distributed**: All Hadoop daemons (NameNode, DataNode, SecondaryNameNode) run on a single machine or VM.
- **Fully distributed**: The NameNode runs on a master host, and multiple DataNodes run on separate physical or virtual machines across the network.

---

### Q21: How do you demonstrate replication on a single machine?
**Answer:** Using our provided `hadoop-config/docker-compose.yml`, which boots one NameNode and two DataNodes on separate ports (`9864` and `9865`). By setting `dfs.replication=2`, blocks are physically written to both DataNode containers.

---

### Q22: What command proves that blocks are replicated across multiple DataNodes?
**Answer:**
```bash
hdfs fsck /minicloud -files -blocks -locations
```
The output displays each block ID along with the IP addresses of the DataNodes holding live replicas (e.g. `Live_repl=2 [192.168.1.105:9864, 192.168.1.106:9864]`).

---

### Q23: Why do we use Waitress instead of Gunicorn on Windows?
**Answer:** Gunicorn relies on the Unix `fork()` system call, which is not supported on Windows. Waitress is a pure-Python, production-grade WSGI server designed to run efficiently on Windows with multi-threaded request processing.

---

### Q24: What is glassmorphism and how is it implemented?
**Answer:** Glassmorphism is a UI visual design style characterized by frosted-glass semi-transparent panels floating over ambient colored backgrounds. It is implemented using pure CSS: `background: rgba(...)`, CSS `backdrop-filter: blur(16px-24px)`, a 1px subtle white top border highlight (`inset 0 1px 0 rgba(255,255,255,0.4)`), and rounded corners.

---

### Q25: How does the system handle filename collisions in the same folder?
**Answer:** Rather than failing the upload with an error, the file service automatically auto-increments the display name (e.g. `assignment.pdf` becomes `assignment (1).pdf`), matching the user experience of consumer cloud storage services like Google Drive.

---

### Q26: What happens when a DataNode crashes during an upload?
**Answer:** The HTTP PUT stream to the DataNode fails with a connection error or timeout. Step 6 of the consistency protocol catches the exception, issues a best-effort `DELETE` for the partial file, removes the `pending` database record, and returns a friendly 503/500 error to the client, preventing orphaned partial blocks.

---

### Q27: How does the Admin Cluster page gather metrics without running Hadoop CLI commands?
**Answer:** It queries the NameNode's built-in Java Management Extensions (JMX) HTTP endpoint at `/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState`. The NameNode returns structured JSON containing live DataNode counts, dead DataNodes, total raw capacity, and block counts.

---

### Q28: What are the primary architectural limitations of this project?
**Answer:**
1. The Cloud Controller is a single point of failure (no multi-controller load balancer).
2. SQLite has write-concurrency limits compared to distributed databases.
3. Network traffic runs over HTTP rather than TLS/HTTPS by default.
4. No file deduplication or public file-sharing links are implemented.
