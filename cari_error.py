import os

print("Memulai pencarian file dengan encoding bermasalah...\n")

for root, dirs, files in os.walk("."):
    for file in files:
        filepath = os.path.join(root, file)
        
        # Abaikan folder git, virtual environment, dan cache
        if ".git" in filepath or "__pycache__" in filepath or "venv" in filepath or "env" in filepath:
            continue
            
        # Hanya periksa file text/kode
        if filepath.endswith(('.py', '.txt', '.pem', '.md', '.json', '.yml', '.yaml')):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    f.read()
            except UnicodeDecodeError as e:
                print(f"🚨 BINGO! File bermasalah ditemukan: {filepath}")
                print(f"   Detail error: {e}\n")

print("Pencarian selesai.")