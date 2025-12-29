import re
import json
from typing import List, Dict, Optional

class LegalDocParser:
    """
    Parser khusus untuk dokumen hukum Indonesia (PPJB, SHM, UU).
    Mengubah teks mentah menjadi struktur JSON hierarkis (Pasal -> Ayat).
    """

    def __init__(self):
        # --- REGEX PATTERNS ---
        # 1. Menangkap "PASAL 1", "Pasal 20", "PASAL  3" (Case insensitive)
        # ^\s* = Toleransi spasi di awal baris
        self.PASAL_PATTERN = r"(?i)^\s*PASAL\s+(\d+)"
        
        # 2. Menangkap Sub-poin/Ayat: "1.", "a.", "1)", "a)"
        # \s* = Spasi di awal
        # ([a-zA-Z0-9]+) = Huruf atau Angka
        # [\.\)] = Diikuti Titik atau Kurung Tutup
        self.SUBPOINT_PATTERN = r"^\s*([a-zA-Z0-9]+)[\.\)]\s+"

        # State Variables
        self.current_article: Optional[Dict] = None
        self.parsed_data: List[Dict] = []

    def _reset_state(self):
        """Menyiapkan wadah untuk pasal baru"""
        self.current_article = {
            "nomor": "",
            "judul": "",
            "isi": [] # List of strings (Ayat)
        }

    def _save_current_article(self):
        """Menyimpan pasal yang sedang diproses ke list hasil"""
        if self.current_article and self.current_article["nomor"]:
            self.parsed_data.append(self.current_article)
            self.current_article = None

    def parse(self, text: str) -> List[Dict]:
        """
        Main logic: Menerima string panjang, mengembalikan List of Dict.
        """
        # Reset data setiap kali parse dipanggil
        self.parsed_data = []
        self.current_article = None

        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # --- LOGIC 1: DETEKSI PASAL BARU ---
            pasal_match = re.search(self.PASAL_PATTERN, line)
            if pasal_match:
                # Simpan pasal sebelumnya jika ada
                self._save_current_article()
                
                # Buka pasal baru
                self._reset_state()
                self.current_article["nomor"] = pasal_match.group(1)
                continue

            # --- LOGIC 2: DETEKSI KONTEN (Jika sedang di dalam Pasal) ---
            if self.current_article:
                # Cek apakah ini Ayat/Sub-poin?
                if re.search(self.SUBPOINT_PATTERN, line):
                    self.current_article["isi"].append(line)
                else:
                    # Jika bukan ayat, kemungkinan ini JUDUL atau kelanjutan teks
                    if self.current_article["judul"] == "":
                        # Asumsi: Baris pertama setelah "PASAL X" yang bukan ayat adalah JUDUL
                        self.current_article["judul"] = line
                    else:
                        # Jika judul sudah ada, anggap ini kelanjutan ayat terakhir
                        # Atau teks narasi bebas (masukkan ke isi saja)
                        self.current_article["isi"].append(line)

        # Jangan lupa simpan pasal terakhir (End of File)
        self._save_current_article()
        
        return self.parsed_data

    def save_to_json(self, output_path: str):
        """Helper untuk menyimpan hasil ke file JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.parsed_data, f, indent=2, ensure_ascii=False)

# --- BLOK TESTING (Opsional, hapus saat production) ---
if __name__ == "__main__":
    sample_text = """
    PASAL 1
    DEFINISI
    1. "Tanah" adalah sebidang tanah...
    Pasal 2
    HARGA
    1. Harga jual beli adalah Rp 500jt.
    2. Pembayaran dilakukan bertahap.
       a. Tahap 1 sebesar 30%
    """
    parser = LegalDocParser()
    result = parser.parse(sample_text)
    print(json.dumps(result, indent=2))