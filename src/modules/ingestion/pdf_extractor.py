import pdfplumber

class PDFExtractor:
    """
    Kelas khusus untuk membaca teks dari PDF secara gratis (Offline).
    Menggantikan fungsi Azure Document Intelligence.
    """
    
    def extract_text(self, file_path: str) -> str:
        print(f"📄 [PDFExtractor] Membaca file: {file_path}")
        full_text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Gabungkan teks dan beri jeda baris
                        full_text += text + "\n"
            return full_text
            
        except Exception as e:
            print(f"❌ Error saat membaca PDF: {e}")
            raise e