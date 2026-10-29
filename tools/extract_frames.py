import cv2
import os

print("=" * 50)
print("🚀 Extractor de Cadre Video (cu Redimensionare) 🚀")
print("=" * 50)

# --- Setări ---
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1024

# Cere numele fișierului video de la utilizator
video_name = input("➡️ Introduceți numele fișierului video (ex: bufnita.mp4): ")

# Verifică dacă fișierul video există
if not os.path.exists(video_name):
    print(f"❌ EROARE: Fișierul '{video_name}' nu a fost găsit.")
    print("Asigurați-vă că scriptul și videoclipul sunt în același folder.")
    input("\nApăsați Enter pentru a ieși.")
else:
    # Cere numele folderului de output
    output_folder = input("➡️ Introduceți numele folderului unde se vor salva cadrele (ex: cadre_extrase): ")

    # Creează folderul de output dacă nu există
    if not os.path.exists(output_folder):
        print(f"📁 Se creează folderul '{output_folder}'...")
        os.makedirs(output_folder)

    # Deschide fișierul video
    cap = cv2.VideoCapture(video_name)
    count = 0
    print("\n⏳ Încep extragerea și redimensionarea cadrelor... Acest proces poate dura câteva momente.\n")

    # Parcurge videoclipul cadru cu cadru
    while True:
        # Citește un cadru
        ret, frame = cap.read()

        # Dacă 'ret' este False, înseamnă că am ajuns la finalul videoclipului
        if not ret:
            break

        # =============================================================
        # ✅ NOU: Pasul de Redimensionare
        # =============================================================
        # Redimensionăm cadrul la 1024x1024 folosind o metodă de interpolare de calitate (LANCZOS4)
        resized_frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        # =============================================================

        # Construiește numele fișierului pentru cadru (ex: frame_0001.png)
        frame_name = f"frame_{count:04d}.png"
        output_path = os.path.join(output_folder, frame_name)

        # Salvează cadrul REDIMENSIONAT ca imagine
        cv2.imwrite(output_path, resized_frame)
        
        # Afișează progresul la fiecare 50 de cadre
        if count % 50 == 0:
            print(f"  -> Salvat cadrul redimensionat {frame_name}")

        count += 1

    # Eliberează resursa video
    cap.release()

    print("\n" + "=" * 50)
    print(f"✅ Extragere finalizată!")
    print(f"{count} cadre au fost salvate cu succes în folderul '{output_folder}' la rezoluția {TARGET_WIDTH}x{TARGET_HEIGHT}.")
    print("=" * 50)
    input("\nApăsați Enter pentru a închide.")