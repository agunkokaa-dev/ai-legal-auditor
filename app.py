import os
import sys
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Setup Path agar modul src terbaca
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.rag.retriever import GraphRetriever
from src.modules.rag.generator import RAGGenerator

# Load Environment
load_dotenv()

app = Flask(__name__)

# --- INISIALISASI SISTEM (Hanya sekali saat server nyala) ---
try:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    retriever = GraphRetriever(driver)
    generator = RAGGenerator()
    print("✅ Flask siap! Terkoneksi ke Neo4j.")
except Exception as e:
    print(f"❌ Gagal koneksi Database: {e}")
    driver = None

# --- ROUTE 1: TAMPILAN HALAMAN UTAMA ---
@app.route('/')
def home():
    return render_template('index.html')

# --- ROUTE 2: API UNTUK TANYA JAWAB ---
@app.route('/ask', methods=['POST'])
def ask():
    if not driver:
        return jsonify({"error": "Database tidak terkoneksi."}), 500

    data = request.json
    user_question = data.get('question')

    if not user_question:
        return jsonify({"error": "Pertanyaan kosong"}), 400

    print(f"📩 Menerima pertanyaan: {user_question}")

    try:
        # 1. Retrieve (Cari Pasal)
        context = retriever.retrieve(user_question, top_k=3)
        
        if not context:
            return jsonify({
                "answer": "Maaf, saya tidak menemukan pasal yang relevan dalam dokumen kontrak ini.",
                "sources": []
            })

        # 2. Generate 
        answer = generator.generate_answer(user_question, context)

        # 3. Kirim Balik ke Browser
        return jsonify({
            "answer": answer,
            "sources": context  # Kita kirim juga sumbernya biar keren
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Terjadi kesalahan internal"}), 500
    # --- ROUTE BARU: API UNTUK VISUALISASI GRAPH ---
@app.route('/get-graph', methods=['POST'])
def get_graph():
    data = request.json
    # Kita ambil pasal yang ditemukan dari hasil search sebelumnya
    # (Di aplikasi real, logic ini bisa lebih kompleks)
    pasal_list = data.get('pasal_list', []) # List nomor pasal, misal [4, 2]
    
    if not pasal_list:
        return jsonify({"nodes": [], "edges": []})

    # Query Cypher untuk mengambil Pasal DAN Ayat-ayatnya untuk digambar
    cypher_query = """
    MATCH (p:Pasal)-[r:BERISI]->(a:Ayat)
    WHERE p.nomor IN $pasal_list
    RETURN p.nomor AS pasal, p.judul AS judul, a.teks AS ayat, elementId(a) as ayat_id
    """
    
    nodes = []
    edges = []
    added_nodes = set()

    with driver.session() as session:
        records = session.run(cypher_query, pasal_list=pasal_list)
        
        for record in records:
            p_id = f"pasal_{record['pasal']}"
            a_id = f"ayat_{record['ayat_id']}"
            
            # 1. Buat Node PASAL (Induk) - Warna Biru
            if p_id not in added_nodes:
                nodes.append({
                    "id": p_id, 
                    "label": f"Pasal {record['pasal']}\n{record['judul']}", 
                    "color": "#3498db",
                    "shape": "box",
                    "font": {"color": "white"}
                })
                added_nodes.add(p_id)

            # 2. Buat Node AYAT (Anak) - Warna Kuning
            # Kita potong teksnya biar gak kepanjangan di layar
            short_text = record['ayat'][:20] + "..."
            nodes.append({
                "id": a_id, 
                "label": short_text, 
                "title": record['ayat'], # Tooltip (muncul pas mouse hover)
                "color": "#f1c40f",
                "shape": "ellipse"
            })
            
            # 3. Buat Garis Hubung
            edges.append({"from": p_id, "to": a_id})

    return jsonify({"nodes": nodes, "edges": edges})

if __name__ == '__main__':
    app.run(debug=True, port=5000)