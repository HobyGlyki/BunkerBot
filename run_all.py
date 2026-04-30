import subprocess
import sys
import time
import urllib.request
import threading
import re
import os
import io


os.system('chcp 65001 > nul')

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Подготавливаем окружение для подпроцессов
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUTF8"] = "1"  # <--- ВОТ ЭТА ШТУКА ТВОРИТ ЧУДЕСА

# Цвета
C_SERVER = "\033[94m[SERVER]\033[0m"
C_BOT = "\033[92m[  BOT ]\033[0m" # Добавил пробелы для ровности
C_NGROK = "\033[93m[NGROK ]\033[0m"
C_OLLAMA = "\033[95m[OLLAMA]\033[0m"
C_CYAN = "\033[96m"
C_END = "\033[0m"

def log_reader(pipe, prefix):
    """Читает поток и выводит его с префиксом, корректно обрабатывая UTF-8"""
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
                # Декодируем аккуратно, игнорируя битые символы
                text = line.decode('utf-8', errors='replace').strip()
                if text:
                    # Принудительно выводим через flush, чтобы не было задержек
                    print(f"{prefix} {text}", flush=True)
    except Exception:
        pass

def get_ngrok_url():
    """Спрашивает у API Ngrok текущую публичную ссылку"""
    try:
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as response:
            data = response.read().decode('utf-8')
            # Исправленная регулярка: ищет и .app, и .dev
            match = re.search(r'https://[a-zA-Z0-9.-]+\.ngrok-free\.[a-z]+', data)
            return match.group(0) if match else None
    except:
        return None

def is_ollama_running():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1) as response:
            return response.getcode() == 200
    except: return False

print(f"{C_CYAN}  ЗАПУСК СИСТЕМ УЁБИЩА  {C_END}")
processes = []

try:
    # 1. Ollama
    if not is_ollama_running():
        print(f"{C_OLLAMA} Запускаю сервис...")
        ollama = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(("Ollama", ollama))
        while not is_ollama_running(): time.sleep(1)
    print(f"{C_OLLAMA}  Готова")

    # 2. Сервер
    # log-level error спрячет лишний мусор, оставив только критику
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.api.main:app", "--port", "8000"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env # Передаем кодировку UTF-8 в подпроцесс
    )
    threading.Thread(target=log_reader, args=(server.stdout, C_SERVER), daemon=True).start()
    processes.append(("Server", server))

    # 3. Ngrok
    # Добавляем --log=stdout, чтобы он не перехватывал управление экраном
    tunnel = subprocess.Popen(
        ["ngrok", "http", "8000", "--log=stdout", "--log-level=info"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    threading.Thread(target=log_reader, args=(tunnel.stdout, C_NGROK), daemon=True).start()
    processes.append(("Tunnel", tunnel))

    # 4. Бот
    bot = subprocess.Popen(
        [sys.executable, "app/api/Bot.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env
    )
    threading.Thread(target=log_reader, args=(bot.stdout, C_BOT), daemon=True).start()
    processes.append(("Bot", bot))

    # Ждем инициализации туннеля
    print(f"{C_CYAN}📡 Настройка связи...{C_END}")
    time.sleep(2) 
    
    url = get_ngrok_url()
    
    print("\n" + "═"*50)
    print(f" {C_CYAN}ВСЕ СИСТЕМЫ ВКЛЮЧЕНЫ!{C_END}")
    if url:
        print(f"🔗 ССЫЛКА ДЛЯ БОТА: {url}")
    else:
        print(f" {C_SERVER} Не удалось вытащить ссылку автоматически.")
    print("═"*50 + "\n")

    # Держим основной поток
    server.wait()

except KeyboardInterrupt:
    print(f"\n {C_SERVER} Глушим реактор...")
    for name, proc in processes:
        proc.terminate()
    print(f" {C_CYAN}Уёбиище законсервировано.{C_END}")