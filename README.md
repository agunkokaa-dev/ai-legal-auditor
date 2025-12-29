# ⚖️ AI Legal Auditor (GraphRAG + Agentic Workflow)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_App-000000?style=for-the-badge&logo=flask&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT_4o-412991?style=for-the-badge&logo=openai&logoColor=white)

**AI Legal Auditor** adalah sistem cerdas untuk menganalisis dokumen hukum (Kontrak/PPJB) menggunakan pendekatan **Graph Retrieval-Augmented Generation (GraphRAG)**.

Berbeda dengan RAG biasa yang hanya memotong teks (chunking), sistem ini memahami **Struktur Hierarki Hukum** (Pasal -> Ayat) dan menggunakan **Agentic Workflow** (Writer-Critic Loop) untuk memastikan jawaban akurat, minim halusinasi, dan memiliki dasar hukum yang kuat.

---

## 🌟 Fitur Unggulan (Key Features)

### 1. 🕸️ Graph-Based Retrieval (GraphRAG)
Menyimpan dokumen dalam struktur Graph (Node & Relationships) di **Neo4j**.
- **Parent-Child Indexing:** Saat satu ayat ditemukan, sistem otomatis mengambil konteks Pasal induknya.
- **Visualisasi Relasi:** User dapat melihat hubungan antar pasal secara interaktif di Frontend.

### 2. 🔍 Hybrid Search (Vector + Keyword)
Menggabungkan dua metode pencarian untuk akurasi maksimal:
- **Vector Search:** Mencari makna semantik (misal: "sanksi" $\approx$ "denda").
- **Keyword Search:** Mencari kata kunci spesifik/angka (misal: "5%", "Pasal 4").

### 3. 🤖 Agentic Workflow (Self-Correction)
Menggunakan arsitektur **Writer-Critic Loop**:
1.  **Writer Agent:** Membuat draft jawaban.
2.  **Critic Agent:** Memeriksa draft terhadap fakta database. Jika ada halusinasi, draft ditolak.
3.  **Refinement:** Jawaban diperbaiki sebelum sampai ke user.

### 4. 📊 Interactive Frontend
Web interface berbasis **Flask** dan **Vis.js** yang menampilkan chat dan visualisasi graph secara *side-by-side* atau *modal popup*.

---

## 🛠️ Arsitektur Sistem

```mermaid
graph TD
    User[User Question] -->|Input| Flask[Flask Backend]
    Flask -->|Hybrid Search| Retriever[Graph Retriever]
    Retriever -->|Query| Neo4j[(Neo4j Database)]
    Neo4j -->|Context Nodes| Agent{Agentic Loop}
    
    subgraph "Agentic Workflow"
    Agent -->|Draft| Writer[Writer Agent]
    Writer -->|Review| Critic[Critic Agent]
    Critic -->|Feedback| Writer
    end
    
    Critic -->|Approved| Flask
    Flask -->|Answer + Graph Data| Frontend[Web Interface]

    🚀 Cara Menjalankan (Installation)
Prasyarat
Python 3.10+

Neo4j Desktop (Aktif dan berjalan)

OpenAI API Key

1. Clone Repository
Bash

git clone [https://github.com/agunkokaa-dev/ai-legal-auditor.git](https://github.com/agunkokaa-dev/ai-legal-auditor.git)
cd ai-legal-auditor
2. Setup Environment
Buat file .env di folder root dan isi konfigurasi berikut:

Cuplikan kode

OPENAI_API_KEY=sk-proj-xxxx...
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password_kamu
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Jalankan Aplikasi
Pastikan Neo4j sudah START, lalu jalankan:

Bash

python app.py
Buka browser dan akses: http://localhost:5000

📂 Struktur Project
Plaintext

ai-legal-auditor/
├── app.py                 # Entry point (Flask Server)
├── src/
│   ├── modules/
│   │   ├── rag/
│   │   │   ├── generator.py   # Agentic Logic (Writer & Critic)
│   │   │   ├── retriever.py   # Hybrid Search Logic
│   │   │   ├── graph_store.py # Neo4j Ingestion
│   │   │   └── embeddings.py  # OpenAI Embedding
│   │   └── pdf_parser/        # Ekstraksi PDF ke JSON
├── templates/
│   └── index.html         # Frontend (Chat + Vis.js)
├── data/                  # Tempat menyimpan file PDF (Diabaikan git)
└── requirements.txt       # Daftar Library