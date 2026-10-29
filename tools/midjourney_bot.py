import pyautogui
import pyperclip
import time
import os

# --- CONFIGURARE ---
DELAY_BETWEEN_COMMANDS = 30
COUNTDOWN_SECONDS = 10
PROMPT_FILE = 'prompts.txt'

def automate_prompts():
    """
    Funcția principală care citește prompt-urile (ignorând numele fișierelor) și le trimite.
    """
    if not os.path.exists(PROMPT_FILE):
        print(f"EROARE: Fișierul '{PROMPT_FILE}' nu a fost găsit!")
        return

    # --- BLOC MODIFICAT ---
    prompts = []
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Căutăm doar liniile care conțin comanda /imagine
            if '/imagine' in line:
                # Găsim poziția unde începe comanda
                start_index = line.find('/imagine')
                # Extragem doar comanda, ignorând tot ce este înainte
                command = line[start_index:]
                prompts.append(command)
    # --- SFÂRȘIT BLOC MODIFICAT ---

    if not prompts:
        print("EROARE: Nu am găsit nicio comandă validă care să înceapă cu /imagine.")
        return

    # --- Numărătoarea Inversă ---
    print("="*50)
    print(f"SCRIPTUL VA ÎNCEPE ÎN {COUNTDOWN_SECONDS} SECUNDE.")
    print("!!! ACUM, DU-TE LA FEREASTRA DISCORD ȘI DĂ CLICK ÎN CĂSUȚA DE MESAJ!!!")
    print("="*50)

    for i in range(COUNTDOWN_SECONDS, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("\n🚀 START! Se trimit comenzile...")

    # --- Bucla Principală de Automatizare ---
    total_prompts = len(prompts)
    for index, prompt in enumerate(prompts):
        print("-" * 50)
        print(f"Se trimite comanda {index + 1} din {total_prompts}:")
        print(f"   -> {prompt[:70]}...")

        pyperclip.copy(prompt)
        time.sleep(0.5)

        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')

        if index < total_prompts - 1:
            print(f"✅ Comandă trimisă. Se așteaptă {DELAY_BETWEEN_COMMANDS} secunde...")
            time.sleep(DELAY_BETWEEN_COMMANDS)
        else:
            print("✅ Ultima comandă a fost trimisă!")

    print("\n" + "="*50)
    print("🎉🎉🎉 AUTOMATIZARE COMPLETĂ! Toate prompt-urile au fost trimise.")
    print("="*50)

if __name__ == "__main__":
    automate_prompts()