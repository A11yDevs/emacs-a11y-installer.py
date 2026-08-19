import ctypes
import sys
import os

# Mock do NVDA Controller para testes de integração contínua (CI)
class MockNVDADriver:
    """
    Driver simulado para absorver as chamadas de áudio durante o CI.
    Ele possui a mesma assinatura de métodos que a DLL do NVDA espera.
    """
    def nvdaController_speakText(self, text):
        # Absorve o comando de fala silenciosamente no ambiente de testes
        pass

    def nvdaController_cancelSpeech(self):
        # Absorve o comando de parada de fala (Silence/Stop) silenciosamente no ambiente de testes
        pass

# Função para obter a instância do NVDA Controller, seja real ou mock
def get_nvda_controller():
    """
    Módulo/Fábrica responsável por instanciar a comunicação com o leitor.
    Retorna a conexão real no uso normal ou o Mock no ambiente de testes.
    """
    # Verifica se estamos no ambiente de automação (CI)
    if os.environ.get("CI_MOCK_NVDA") == "1":
        return MockNVDADriver()

    # Lógica padrão de carregamento da DLL Real
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
        # Define o tipo de retorno do método cancelSpeech como void (sem retorno)
        return nvda
    except Exception:
        return None

def main():
    # A fábrica entrega a DLL conectada ou o Mock, de acordo com o ambiente
    nvda = get_nvda_controller()
    
    if not nvda:
        sys.exit(1) # Encerra se o NVDA real não estiver rodando

    # Loop principal lendo a saída do Emacspeak via stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            # Limpa quebras de linha e espaços excedentes da string recebida
            line_clean = line.strip()
                
            # Processa a linha recebida do Emacspeak (Comando de Fala)
            if line_clean.startswith("q "): 
                texto = line_clean[2:].strip()
                nvda.nvdaController_speakText(texto)
                
            # Intercepta o comando de interrupção de fala
            elif line_clean == "s":
                nvda.nvdaController_cancelSpeech()
                
        except KeyboardInterrupt:
            break

# Ponto de entrada do script
if __name__ == "__main__":
    main()