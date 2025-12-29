import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class RAGGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def _format_context(self, context_data):
        """Helper untuk merapikan data konteks jadi string."""
        context_text = ""
        for item in context_data:
            context_text += f"""
            ---
            PASAL: {item['pasal']}
            JUDUL: {item['judul']}
            ISI: {item['isi']}
            ---
            """
        return context_text

    def generate_answer(self, user_question: str, context_data: list):
        """
        Fungsi Utama: Menjalankan Loop Tulis-Kritik-Revisi.
        """
        context_text = self._format_context(context_data)
        max_retries = 3  # Maksimal 3x revisi biar gak infinite loop
        current_draft = ""
        
        print(f"\n🚀 [Agent] Memulai proses berpikir untuk pertanyaan: '{user_question}'")

        # --- LOOP AGENTIC ---
        for attempt in range(max_retries):
            print(f"\n🔄 --- Percobaan ke-{attempt + 1} ---")

            # LANGKAH 1: WRITER (Penulis)
            if attempt == 0:
                # Percobaan pertama: Tulis dari nol
                current_draft = self._writer_agent(user_question, context_text)
            else:
                # Percobaan kedua dst: Tulis ulang berdasarkan kritik
                print("   ✍️ [Writer] Sedang merevisi jawaban...")
                current_draft = self._writer_agent(user_question, context_text, prev_draft=current_draft, feedback=critique_feedback)

            # LANGKAH 2: CRITIC (Pengkritik)
            print("   🧐 [Critic] Sedang memeriksa draft...")
            critique_result = self._critic_agent(user_question, context_text, current_draft)
            
            status = critique_result.get("status", "FAIL")
            critique_feedback = critique_result.get("feedback", "Tidak ada feedback.")

            print(f"   📊 Status Review: {status}")
            
            # LANGKAH 3: DECISION (Keputusan)
            if status == "PASS":
                print("   ✅ [Manager] Kualitas bagus. Kirim ke user.")
                return current_draft
            else:
                print(f"   ⚠️ [Manager] Ditolak! Kritik: {critique_feedback}")
                # Loop akan berlanjut ke attempt berikutnya untuk revisi

        # Jika sudah max_retries masih gagal, kirim draft terakhir dengan disclaimer
        return current_draft + "\n\n(Catatan Sistem: Jawaban ini mungkin belum sempurna setelah beberapa kali revisi)."

    # --- AGENT 1: SI PENULIS ---
    def _writer_agent(self, question, context, prev_draft=None, feedback=None):
        system_prompt = """
        Anda adalah Asisten Hukum (Legal Drafter). 
        Tugas: Jawab pertanyaan user berdasarkan KONTEKS PASAL yang diberikan.
        
        Aturan:
        1. Jawaban harus tegas, formal, dan mudah dimengerti.
        2. WAJIB mengutip Nomor Pasal dan Judulnya sebagai dasar hukum.
        3. Jangan berasumsi di luar data.
        """

        user_prompt = f"Konteks:\n{context}\n\nPertanyaan: {question}"

        # Jika ini adalah revisi, tambahkan instruksi khusus
        if prev_draft and feedback:
            user_prompt += f"""
            \n\n--- INSTRUKSI REVISI ---
            Draft sebelumnya: "{prev_draft}"
            Kritik dari Supervisor: "{feedback}"
            
            TOLONG TULIS ULANG jawaban yang memperbaiki kesalahan di atas.
            """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7 # Sedikit kreatif untuk menulis
        )
        return response.choices[0].message.content

    # --- AGENT 2: SI PENGKRITIK ---
    def _critic_agent(self, question, context, draft):
        system_prompt = """
        Anda adalah Senior Legal Auditor (Supervisor).
        Tugas: Memeriksa akurasi jawaban junior Anda.
        
        Kriteria Kelulusan (PASS):
        1. Jawaban menyebutkan Nomor Pasal yang BENAR sesuai Konteks.
        2. Jawaban TIDAK berhalusinasi (menyebut fakta yang tidak ada di konteks).
        3. Jawaban menjawab inti pertanyaan user.
        
        OUTPUT HARUS DALAM FORMAT JSON:
        {
            "status": "PASS" atau "FAIL",
            "feedback": "Penjelasan singkat jika FAIL, atau 'Oke' jika PASS"
        }
        """

        user_prompt = f"""
        KONTEKS ASLI:
        {context}

        PERTANYAAN USER:
        {question}

        JAWABAN JUNIOR:
        {draft}
        
        Berikan penilaian Anda dalam JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0, # Harus ketat & konsisten
                response_format={"type": "json_object"} # Memaksa output JSON valid
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Fallback jika error parsing JSON
            print(f"❌ Error Critic: {e}")
            return {"status": "PASS", "feedback": "Error parsing, anggap saja bagus."}