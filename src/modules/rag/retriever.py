import os
from neo4j import GraphDatabase
from src.modules.rag.embeddings import EmbeddingService

class GraphRetriever:
    def __init__(self, driver: GraphDatabase.driver):
        self.driver = driver
        self.embedder = EmbeddingService()

    def retrieve(self, query: str, top_k: int = 5): # Kita naikkan jadi 5 kandidat
        """
        Melakukan Hybrid Search: Menggabungkan Vector Search + Keyword Search sederhana.
        """
        # 1. Siapkan Vector
        query_vector = self.embedder.get_embedding(query)
        
        # 2. Ekstrak kata kunci sederhana (misal user tanya "denda", kita cari kata "denda")
        # Kita ambil kata yang panjangnya > 3 huruf agar kata sambung tidak ikut
        keywords = [word for word in query.lower().split() if len(word) > 3]
        keyword_clause = " OR ".join([f"toLower(node.teks) CONTAINS '{word}'" for word in keywords])
        
        if not keyword_clause:
            keyword_clause = "1=0" # Kalau tidak ada keyword, abaikan bagian ini

        # 3. Query Cypher: GABUNGAN (UNION)
        # Bagian A: Cari berdasarkan Vector (Makna)
        # Bagian B: Cari berdasarkan Teks (Keyword match)
        cypher_query = f"""
        // BAGIAN 1: VECTOR SEARCH
        CALL db.index.vector.queryNodes('ayat_vector', $top_k, $query_vector)
        YIELD node, score
        RETURN node, score, 'vector' as source
        
        UNION
        
        // BAGIAN 2: KEYWORD SEARCH (Backup jika vector meleset)
        MATCH (node:Ayat)
        WHERE {keyword_clause}
        RETURN node, 1.0 as score, 'keyword' as source
        LIMIT $top_k
        """
        
        results = []
        seen_ids = set() # Untuk mencegah duplikat (kalau ketemu di vector & keyword)

        print(f"🔍 [Retriever] Mencari: '{query}'")

        with self.driver.session() as session:
            records = session.run(cypher_query, 
                                query_vector=query_vector, 
                                top_k=top_k)
            
            for record in records:
                node = record['node']
                score = record['score']
                source_method = record['source']
                
                # Cek Duplikat (Kita pakai ID internal Neo4j)
                if node.element_id in seen_ids:
                    continue
                seen_ids.add(node.element_id)

                # Ambil data Bapaknya (Pasal)
                # Kita perlu query kecil lagi untuk cari parent-nya karena UNION tadi memutus rantai
                parent_info = session.run("""
                    MATCH (n)-[:BERISI]-(p:Pasal) 
                    WHERE elementId(n) = $node_id
                    RETURN p.nomor AS nomor, p.judul AS judul
                """, node_id=node.element_id).single()

                if parent_info:
                    print(f"   ✅ Ketemu via {source_method.upper()}: Pasal {parent_info['nomor']} (Score: {score:.2f})")
                    
                    results.append({
                        "pasal": parent_info["nomor"],
                        "judul": parent_info["judul"],
                        "isi": node["teks"],
                        "score": score
                    })
        
        return results