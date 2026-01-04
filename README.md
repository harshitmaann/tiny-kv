# tiny-kv 🗄️⚡

A lightweight, fault-tolerant **distributed key–value store** built in Python.

`tiny-kv` demonstrates core distributed systems concepts through a minimal but correct implementation, focusing on **replication, consistency, and failure handling** rather than scale.

---

## 🚀 Features

- **Versioned Key–Value Store**
  - Each key maintains a monotonically increasing version number
- **Quorum-Based Writes**
  - Writes succeed only after a majority of replicas acknowledge
- **Replication**
  - Primary node replicates writes to replica nodes via HTTP
- **Fault Tolerance**
  - System continues operating when one or more replicas fail
- **Snapshot Sync & Recovery**
  - Restarted replicas automatically synchronize missing state
- **Tombstone Deletes**
  - Deletes are versioned and replicated to prevent data resurrection

---

## 🧠 Architecture Overview

```text
Client
  |
  v
+--------------------+
| Primary (node1)    |
| Port: 5001         |
+---------+----------+
          |
     replicate writes
          |
   +------+------+
   |             |
   v             v
+---------+   +---------+
| Replica |   | Replica |
| node2   |   | node3   |
| :5002   |   | :5003   |
+---------+   +---------+

Notes:
- Writes are routed to the primary node.
- The primary replicates writes to replicas.
- A write succeeds once quorum = ceil(N / 2) acknowledgements is reached.

```
---

## 🛠️ Setup & Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/harshitmaann/tiny-kv.git
cd tiny-kv