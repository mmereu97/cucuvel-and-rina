import google.generativeai as genai
import os
from dotenv import load_dotenv

def investigate_models():
    """
    Acest script se conectează la API-ul Gemini și listează toate modelele
    disponibile pentru cheia API configurată, verificând care dintre ele
    suportă metoda 'generateContent' necesară pentru chat.
    """
    print("=====================================================")
    print("🔍 Script de Diagnostic pentru Modelele Gemini")
    print("=====================================================\n")

    try:
        # Pasul 1: Încarcă cheia API din fișierul .env
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            print("❌ EROARE: Nu am găsit cheia 'GOOGLE_API_KEY' în fișierul .env.")
            print("Asigură-te că fișierul .env există în același folder și conține cheia corectă.")
            return

        print("✅ Cheia API a fost încărcată cu succes din .env.")

        # Pasul 2: Configurează biblioteca cu cheia ta
        genai.configure(api_key=api_key)
        print("⏳ Se cere lista de modele de la Google...\n")

        # Pasul 3: Listează toate modelele disponibile pentru cheia ta
        model_list = list(genai.list_models())
        
        if not model_list:
            print("⚠️ Nu a fost găsit niciun model. Verifică dacă cheia API este validă și are permisiuni.")
            return
            
        print(f"✅ Am găsit {len(model_list)} modele disponibile. Le analizez:\n")
        
        print("-----------------------------------------------------")
        for model in model_list:
            # --- LINIA CORECTATĂ AICI ---
            # Acum afișează numele corect, fără prefix duplicat.
            print(f"🔹 Nume Model (pentru cod): {model.name}")
            
            print(f"   Nume Afișare: {model.display_name}")
            
            if 'generateContent' in model.supported_generation_methods:
                print("   ✅ Poate genera conținut (chat)? DA")
            else:
                print("   ❌ Poate genera conținut (chat)? NU")
            
            print("-----------------------------------------------------")
            
        print("\n💡 RECOMANDARE:")
        print("Folosește în scriptul tău unul dintre numele de model de mai sus")
        print("care are '✅ DA' la generarea de conținut.")
        print("Exemplu: `self.model = genai.GenerativeModel('gemini-pro')`")

    except Exception as e:
        print(f"\n❌ A apărut o eroare neașteptată în timpul diagnosticării:")
        print(f"   Tip eroare: {type(e).__name__}")
        print(f"   Mesaj: {e}")
        print("\n   POSIBILE CAUZE:")
        print("   1. Cheia API este invalidă sau a expirat.")
        print("   2. Nu ai acces la internet.")
        print("   3. API-ul 'Generative Language' nu este activat în proiectul tău Google Cloud.")


if __name__ == "__main__":
    investigate_models()