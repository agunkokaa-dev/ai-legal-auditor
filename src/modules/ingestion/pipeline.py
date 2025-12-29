import json
import os
import sys

# --- FIX PATH (PERBAIKAN) ---
# Ambil lokasi file ini berada
current_dir = os.path.dirname(os.path.abspath(__file__))

# Naik 3 level ke atas untuk cari folder root project
# (ingestion -> modules -> src -> ROOT)
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# Masukkan root ke daftar jalan pintas Python
sys.path.insert(0, project_root)

# Cek print untuk memastikan path benar (Opsional, buat debug)
print(f"📂 Project Root diset ke: {project_root}")
# -----------------------------

# --- BARU LAKUKAN IMPORT SETELAH PATH DI-SET ---
try:
    from src.modules.ingestion.pdf_extractor import PDFExtractor
    from src.modules.ingestion.parser import LegalDocParser
    from src.modules.rag.graph_store import GraphStore
except ImportError as e:
    print(f"❌ Masih Error Import: {e}")
    print("Pastikan Anda menjalankan terminal dari folder 'ai-legal-auditor'")
    sys.exit(1)

def run_ingestion_pipeline(file_path: str, output_json_path: str):
    print("🚀 MEMULAI PIPELINE...")

    # 1. INISIALISASI (Siapkan Karyawan)
    try:
        extractor = PDFExtractor()    # Karyawan 1: Tukang Baca
        parser = LegalDocParser()     # Karyawan 2: Tukang Rapikan Struktur
        graph_store = GraphStore()    # Karyawan 3: Penjaga Gudang Neo4j
    except Exception as e:
        print(f"❌ [INIT ERROR] Gagal inisialisasi modul: {e}")
        return

    # 2. EKSTRAKSI (Tugas Karyawan 1)
    try:
        print("step 1")
        raw_text = extractor.extract_text(file_path)
        print(f"   ✅ Berhasil membaca PDF. Total: {len(raw_text)} karakter")
    except Exception as e:
        print(f"   ❌ Gagal baca PDF, pipeline berhenti.")
        return

    # 3. TRANSFORMASI (Tugas Karyawan 2)
    print("⚙️ [Step 2] Parsing Struktur Pasal...")
    structured_data = parser.parse(raw_text)
    print(f"   ✅ Ditemukan {len(structured_data)} Pasal.")

    # 4. BACKUP DATA (Administrasi)
    print("💾 [Step 3] Menyimpan backup JSON...")
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    # 5. LOADING KE GRAPH (Tugas Karyawan 3)
    print("🧠 [Step 4] Menyimpan ke Knowledge Graph (Neo4j)...")
    try:
        graph_store.setup_database()
        filename = os.path.basename(file_path)
        graph_store.ingest_document(filename, structured_data)
        graph_store.close()
        print("🎉 SUKSES BESAR! Data PDF sudah masuk ke Otak AI.")
    except Exception as e:
        print(f"   ❌ Gagal menyimpan ke Neo4j: {e}")
        return

if __name__ == "__main__":
    # Pastikan file sample_ppjb.pdf sudah ada di folder data/raw/
    sample_pdf = "data/raw/sample_ppjb.pdf" 
    output_json = "data/processed/result.json"
    
    if os.path.exists(sample_pdf):
        run_ingestion_pipeline(sample_pdf, output_json)
    else:
        print(f"⚠️ File tidak ditemukan: {sample_pdf}")