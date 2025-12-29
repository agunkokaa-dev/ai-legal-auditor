import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EmbeddingService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY tidak ditemukan di .env")
        
        self.client = OpenAI(api_key=api_key)
        # Model 'small' sudah sangat bagus dan murah untuk hukum
        self.model = "text-embedding-3-small" 

    def get_embedding(self, text: str) -> List[float]:
        """
        Mengubah teks tunggal menjadi vektor list float.
        """
        # Bersihkan newline berlebih agar akurasi vektor lebih bagus
        text = text.replace("\n", " ")
        
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Embedding Error] Gagal memproses teks: {e}")
            return []

# --- TEST CODE ---
if __name__ == "__main__":
    embedder = EmbeddingService()
    vector = embedder.get_embedding("Pasal 1: Pihak Pertama wajib membayar lunas.")
    print(f"Dimensi Vektor: {len(vector)}") # Harusnya 1536 dimensi
    print(f"Contoh data: {vector[:5]}...")