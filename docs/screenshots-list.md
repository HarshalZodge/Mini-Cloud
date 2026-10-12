# MiniCloud — Required Project Report Screenshots Inventory

Capture and include these exact screenshots in your project report and presentation slide deck.

---

## 1. Authentication & Onboarding
- [ ] **Figure 1: User Login Screen**: Frosted glass card over ambient glow background.
- [ ] **Figure 2: User Registration Screen**: Demonstrating account creation for first user (admin) and subsequent users.
- [ ] **Figure 3: Form Validation Alert**: Displaying error when password is under 8 characters or email is malformed.

---

## 2. Main Dashboard & Analytics
- [ ] **Figure 4: Dashboard Overview**: Displaying welcome message, 4 quick stat cards, and active storage badge.
- [ ] **Figure 5: Personal Storage Quota Bar**: Progress bar indicating percentage of quota consumed.
- [ ] **Figure 6: File-Type Distribution Donut Chart**: Interactive Recharts donut visualization showing bytes per category.
- [ ] **Figure 7: Recent Files Table**: Listing recently accessed and uploaded documents.

---

## 3. My Files Explorer
- [ ] **Figure 8: My Files List View**: Showing table columns (Name, Type Icon, Size, Upload Date, and Row Actions).
- [ ] **Figure 9: My Files Grid View**: Showing responsive cards with large type icons and hover lift effects.
- [ ] **Figure 10: Breadcrumb Navigation**: Showing current virtual path (e.g. `My Files > Lab_Assignments > Week_1`).
- [ ] **Figure 11: Create New Folder Dialog**: Modal for entering folder name.
- [ ] **Figure 12: Move File Dialog**: Folder selection dialog moving a file into a subfolder.

---

## 4. Upload & Download Protocols
- [ ] **Figure 13: Drag-and-Drop Drop Zone**: Dashed glass upload zone showing drag-over highlight.
- [ ] **Figure 14: Multi-File Upload in Progress**: Modal showing live animated progress bars for concurrent file uploads.
- [ ] **Figure 15: Successful Upload Notification**: Toast notification confirming file written to HDFS.
- [ ] **Figure 16: File Auto-Renaming on Collision**: Showing `document (1).pdf` created automatically on duplicate name upload.

---

## 5. Starred, Recent & Trash Management
- [ ] **Figure 17: Starred Files View**: Bookmarked favorite files.
- [ ] **Figure 18: Recent Files View**: Chronologically sorted recent access view.
- [ ] **Figure 19: Trash Page**: Showing soft-deleted items with restore and permanent delete actions.
- [ ] **Figure 20: Empty Trash Confirmation Modal**: Warning modal explaining irreversible removal from HDFS.

---

## 6. Storage & Capacity Analysis
- [ ] **Figure 21: Storage Analysis Screen**: Detailed breakdown comparing user configured quota to total HDFS cluster capacity.
- [ ] **Figure 22: Category Usage Bars**: Category-by-category proportional progress bars.

---

## 7. Administrative Telemetry & Cluster Monitoring
- [ ] **Figure 23: Admin Cluster Status Page**: Real-time cards showing live DataNodes, dead DataNodes, total HDFS blocks, and replication factor.
- [ ] **Figure 24: NameNode JMX Telemetry**: Showing raw cluster capacity metrics retrieved from Hadoop NameNode.

---

## 8. Terminal Verification & Architecture Proof
- [ ] **Figure 25: Automated Pytest Suite Output**: Terminal screenshot showing 100% pass on all 12 unit tests.
- [ ] **Figure 26: Storage Smoke Test Output**: Terminal execution of `hdfs_smoke_test.py` proving hash verification.
- [ ] **Figure 27: HDFS FSCK Block Locations**: Terminal output of `hdfs fsck /minicloud -files -blocks -locations` proving multi-node replication.
- [ ] **Figure 28: Mobile Browser Access over LAN**: Photo or screenshot of smartphone accessing `http://<HOST_IP>:5000` via Wi-Fi.
