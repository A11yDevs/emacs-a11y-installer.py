import ctypes
import sys
import os

class MockNVDADriver:
    """
    Driver simulado para absorver as chamadas de áudio durante o CI.
    Ele possui a mesma assinatura de método que a DLL do NVDA espera.
    """
    def nvdaController_speakText(self, text):
        # No modo mock, simplesmente consumimos a string sem fazer nada.
        # Isso evita que o teste falhe devido à ausência do NVDA real.
        pass

def get_nvda_controller():
    """
    Módulo/Fábrica responsável por instanciar a comunicação com o leitor.
    Retorna a conexão real no uso normal ou o Mock no ambiente de testes.
    """
    # Verifica se estamos no ambiente de automação (CI)
    if os.environ.get("CI_MOCK_NVDA") == "1":
        return MockNVDADriver()

    # Lógica padrão de carregamento da DLL no Windows
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
        # Testa se o leitor físico está aberto no Windows
        if nvda.nvdaController_testIfRunning() != 0:
            return None
            
        nvda.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
        return nvda
    except Exception:
        return None

def main():
    # A fábrica encapsula a complexidade. A main apenas usa o controlador recebido.
    nvda = get_nvda_controller()
    
    if not nvda:
        sys.exit(1) # Encerra graciosamente se o NVDA real não estiver rodando

    # Loop principal lendo a saída do Emacspeak
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            # Processa a linha recebida do Emacspeak
            if line.startswith("q "): 
                texto = line[2:].strip()
                # Chama a leitura na DLL (ou no Mock)
                nvda.nvdaController_speakText(texto)
                
        except KeyboardInterrupt:
            break

# Ponto de entrada do script
if __name__ == "__main__":
    main()