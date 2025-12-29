import os
from typing import List, Dict, Any 
from neo4j import GraphDatabase
from dotenv import load_dotenv
from src.modules.rag.embeddings import EmbeddingService

# --- FIX PATH .ENV ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)
# ---------------------

class GraphStore:
    def __init__(self):
        # Ambil kredensial
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not password:
            print(f"⚠️ Debug: Mencari .env di: {env_path}")
            raise ValueError("NEO4J_PASSWORD is not set in .env")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.embedder = EmbeddingService()

    def close(self):
        self.driver.close()

    def setup_database(self):
        """Menyiapkan Index dan Constraints."""
        print("⚙️ Membuat/Memastikan Vector Index 'ayat_vector'...")
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT doc_name IF NOT EXISTS FOR (d:Document) REQUIRE d.filename IS UNIQUE")
            session.run("""
                CREATE VECTOR INDEX ayat_vector IF NOT EXISTS
                FOR (a:Ayat) ON (a.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
        print("✅ Database Setup Selesai.")

    def ingest_document(self, filename: str, structured_data: List[Dict]):
        """Fungsi Utama: Simpan JSON parser ke Graph + Vector."""
        print(f"📥 Memproses {filename} untuk disimpan ke Neo4j...")
        
        with self.driver.session() as session:
            # A. Buat Node Dokumen Induk
            session.run("""
                MERGE (d:Document {filename: $filename})
                ON CREATE SET d.created_at = datetime()
            """, filename=filename)

            # B. Loop setiap Pasal
            for pasal in structured_data:
                # --- PERBAIKAN ANTI-ERROR (ROBUST) ---
                # Kita cari key 'nomor' ATAU 'pasal_ke'. Kalau tidak ada dua-duanya, pakai string kosong.
                nomor_pasal = pasal.get('nomor') or pasal.get('pasal_ke')
                judul_pasal = pasal.get('judul', 'Tanpa Judul')
                isi_list = pasal.get('isi', [])
                # -------------------------------------

                if not nomor_pasal:
                    print(f"⚠️ Skip data aneh (tidak punya nomor pasal): {pasal}")
                    continue

                # C. Loop setiap Ayat/Isi
                for i, ayat_text in enumerate(isi_list):
                    # 1. Generate Contextual Embedding
                    context_text = f"Pasal {nomor_pasal} {judul_pasal}: {ayat_text}"
                    vector = self.embedder.get_embedding(context_text)
                    
                    if not vector:
                        continue 

                    # 2. Simpan ke Neo4j
                    session.run("""
                        MATCH (d:Document {filename: $filename})
                        
                        MERGE (p:Pasal {nomor: $nomor, source_doc: $filename})
                        ON CREATE SET p.judul = $judul
                        
                        MERGE (d)-[:MEMILIKI]->(p)
                        
                        MERGE (a:Ayat { 
                            source_pasal: $nomor,
                            urutan: $urutan,
                            source_doc: $filename
                        })
                        ON CREATE SET 
                            a.teks = $teks,
                            a.embedding = $vector
                        
                        MERGE (p)-[:BERISI]->(a)
                    """, 
                    filename=filename,
                    nomor=nomor_pasal,
                    judul=judul_pasal,
                    teks=ayat_text,
                    urutan=i+1,
                    vector=vector
                    )
        
        print(f"🎉 Sukses menyimpan data Pasal dari {filename} ke Neo4j.")

# --- TEST RUN ---
if __name__ == "__main__":
    try:
        store = GraphStore()
        store.setup_database()
        store.close()
        print("Test Koneksi OK!")
    except Exception as e:
        print(f"Test Koneksi Gagal: {e}")