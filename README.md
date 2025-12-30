# tiny-kv 🗄️⚡

A lightweight, fault-tolerant **distributed key–value store** built in Python.

`tiny-kv` demonstrates core distributed systems concepts including:
- Versioned writes
- Quorum-based replication
- Tombstone deletes
- Node failure tolerance
- Replica snapshot recovery

This project is intentionally minimal and educational, focusing on correctness and clarity over scale.

---

## 🚀 Features

- **Versioned KV Store**
  - Each key maintains a monotonically increasing version
- **Quorum Writes**
  - Writes succeed when a majority of replicas acknowledge
- **Replication**
  - Primary node replicates writes to replicas via HTTP
- **Fault Tolerance**
  - System continues operating when a replica goes down
- **Snapshot Sync / Recovery**
  - Restarted replicas automatically sync missing data
- **Tombstone Deletes**
  - Deletes are replicated and versioned to prevent resurrection

---

## 🧠 Architecture Overview

       ┌─────────────┐
       │   Client    │
       └──────┬──────┘
              │
              ▼
    ┌──────────────────┐
    │ Primary (node1)  │
    │   Port: 5001     │
    └──────┬──────┬───┘
           │      │
  replicate│      │replicate
           ▼      ▼
 ┌────────────┐ ┌────────────┐
 │ Replica    │ │ Replica    │
 │ node2:5002 │ │ node3:5003 │
 └────────────┘ └────────────┘

 - Writes go to the **primary**
- Primary replicates to replicas
- Quorum = ⌈N/2⌉ acknowledgements

---

## 🛠️ Setup & Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/harshitmaann/tiny-kv.git
cd tiny-kv