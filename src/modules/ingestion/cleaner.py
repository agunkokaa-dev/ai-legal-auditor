import cv2
import numpy as np
import os

class DocumentCleaner:
    """
    Bertugas membersihkan citra dokumen sebelum dikirim ke OCR.
    Fokus utama: Deskewing (Meluruskan orientasi teks).
    """

    def clean_image(self, image_path: str, output_path: str):
        # 1. Baca Gambar
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Gambar tidak ditemukan atau format salah: {image_path}")

        # 2. Konversi ke Grayscale (Hitam Putih)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 3. Inversi warna (Hitam jadi Putih, Teks Putih jadi Hitam) untuk deteksi
        gray = cv2.bitwise_not(gray)

        # 4. Thresholding (Membuat teks menonjol)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # 5. Cari koordinat semua piksel teks (yang > 0)
        coords = np.column_stack(np.where(thresh > 0))
        
        # 6. Hitung sudut kemiringan (Minimum Area Rectangle)
        angle = cv2.minAreaRect(coords)[-1]

        # Koreksi sudut (Logic OpenCV berbeda tergantung versi)
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # 7. Putar balik gambar (Deskewing)
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        rotated = cv2.warpAffine(
            image, M, (w, h), 
            flags=cv2.INTER_CUBIC, 
            borderMode=cv2.BORDER_REPLICATE
        )

        # 8. Simpan hasil
        print(f"[Cleaner] Meluruskan gambar sebesar {angle:.2f} derajat.")
        cv2.imwrite(output_path, rotated)
        return output_path

# --- TEST CODE ---
if __name__ == "__main__":
    # Pastikan Anda punya gambar miring di sini untuk tes
    # cleaner = DocumentCleaner()
    # cleaner.clean_image("data/raw/miring.jpg", "data/processed/lurus.jpg")
    pass