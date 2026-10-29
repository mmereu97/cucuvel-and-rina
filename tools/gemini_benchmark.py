import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from datetime import datetime

def benchmark_chat_models():
    """
    Acest script testează latența (Time to First Token) pentru toate modelele de chat
    disponibile, trimițând o cerere simplă și măsurând timpul de răspuns.
    """
    print("=====================================================")
    print("⏱️  Benchmark de Latență pentru Modelele Gemini")
    print("=====================================================\n")

    try:
        # Pasul 1: Configurare
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ EROARE: Nu am găsit cheia 'GOOGLE_API_KEY' în fișierul .env.")
            return

        genai.configure(api_key=api_key)
        print("✅ Cheia API a fost încărcată și configurată.")

        # Pasul 2: Obținerea modelelor eligibile pentru chat
        print("⏳ Se obține lista de modele de la Google...")
        all_models = genai.list_models()
        chat_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        if not chat_models:
            print("⚠️ Nu a fost găsit niciun model care să suporte chat.")
            return
            
        print(f"✅ Am găsit {len(chat_models)} modele eligibile pentru testare.\n")

        # Pasul 3: Testarea fiecărui model
        test_prompt = "Salut"
        results = []
        
        print(f"🚀 Încep testarea. Întrebare de test pentru fiecare: '{test_prompt}'\n")

        for i, model in enumerate(chat_models):
            print(f"[{i+1}/{len(chat_models)}] Testez modelul: {model.name}...")
            
            try:
                # Inițializăm modelul și pornim cronometrul
                model_instance = genai.GenerativeModel(model.name)
                start_time = time.perf_counter()

                # Trimitem cererea în mod streaming
                response_stream = model_instance.generate_content(test_prompt, stream=True)

                # Așteptăm primul chunk pentru a măsura TTFT
                # `next(iter(...))` este o modalitate rapidă de a obține primul element
                first_chunk = next(iter(response_stream))

                # Oprim cronometrul imediat ce am primit primul răspuns
                end_time = time.perf_counter()
                
                duration_ms = (end_time - start_time) * 1000
                print(f"  └──> ✅ SUCCES! Timp de răspuns (TTFT): {duration_ms:.0f}ms\n")
                results.append({'name': model.name, 'time': duration_ms, 'status': 'Success'})

            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                error_message = str(e).split('\n')[0] # Luăm doar prima linie a erorii
                print(f"  └──> ❌ EROARE! (după {duration_ms:.0f}ms) - {error_message}\n")
                results.append({'name': model.name, 'time': float('inf'), 'status': f'FAIL: {error_message}'})
        
        # Pasul 4: Afișarea clasamentului
        print("\n=====================================================")
        print("🏆 CLASAMENT FINAL - Timp până la Primul Răspuns (TTFT)")
        print("=====================================================")
        
        successful_results = [r for r in results if r['status'] == 'Success']
        failed_results = [r for r in results if r['status'] != 'Success']

        # Sortăm rezultatele de la cel mai rapid la cel mai lent
        successful_results.sort(key=lambda x: x['time'])

        if not successful_results:
            print("\nNiciun model nu a răspuns cu succes.")
        else:
            for i, result in enumerate(successful_results):
                place = f"#{i+1}"
                if i == 0:
                    place += " 🥇 Câștigător"
                print(f"{place:<15} | {result['time']:>7.0f}ms | {result['name']}")
        
        if failed_results:
            print("\n-----------------------------------------------------")
            print("⚠️ Modele care au eșuat testul:")
            print("-----------------------------------------------------")
            for result in failed_results:
                print(f"-> {result['name']} | Motiv: {result['status']}")

    except Exception as e:
        print(f"\n❌ A apărut o eroare generală în timpul scriptului: {e}")

if __name__ == "__main__":
    benchmark_chat_models()