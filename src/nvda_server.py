import ctypes
import sys
import os
import platform

def init_nvda():
    # Verifica a arquitetura do processo atual
    is_64bit = sys.maxsize > 2**32
    dll_name = "nvdaControllerClient64.dll" if is_64bit else "nvdaControllerClient32.dll"

    # Verifica se está rodando a partir do binário compilado pelo PyInstaller
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        # Fallback para caso esteja rodando diretamente via interpretador Python
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    # Define o caminho completo da DLL dinamicamente
    dll_path = os.path.join(base_dir, dll_name)
    
    try:
        nvda = ctypes.windll.LoadLibrary(dll_path)
        if nvda.nvdaController_testIfRunning() != 0:
            return None
            
        nvda.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
        return nvda
    except Exception:
        return None

def main():
    nvda = init_nvda()
    if not nvda:
        sys.exit(1) # Encerra se o NVDA não estiver rodando

    # Loop principal lendo a saída do Emacspeak
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            # Processa a linha recebida do Emacspeak
            if line.startswith("q "): 
                texto = line[2:].strip()
                nvda.nvdaController_speakText(texto)
                
        except KeyboardInterrupt:
            break

# Ponto de entrada do script
if __name__ == "__main__":
    main()