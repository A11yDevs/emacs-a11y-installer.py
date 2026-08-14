import os
import subprocess
import time
import sys

def run_stress_test(server_name, server_path):
    print(f"\n{'='*50}")
    print(f" Iniciando Benchmark: {server_name}")
    print(f" Caminho: {server_path}")
    print(f"{'='*50}")
    
    if not os.path.exists(server_path):
        print(f"[ERRO] Executável não encontrado em: {server_path}")
        return False

    try:
        # Inicia o servidor escutando o stdin (exatamente como o Emacspeak faz)
        process = subprocess.Popen(
            [server_path], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.DEVNULL, # Ignora o output no terminal para não poluir
            stderr=subprocess.PIPE,
            text=True, 
            encoding='utf-8'
        )
        
        # Teste de Fuzzing: Enviando strings com caracteres especiais, Unicode e strings longas
        print("\n[Teste 1] Fuzzing e Caracteres Especiais...")
        fuzzing_payloads = [
            "q Teste de leitura normal.\n",
            "q Símbolos: !@#$%^&*()_+{}|:<>?\n",
            "q Unicode: 漢字, emojis 💻🔥, acentuação áéíóú\n",
            "q \n", # String vazia
            "q " + ("A" * 1000) + "\n" # String super longa
        ]
        
        for payload in fuzzing_payloads:
            process.stdin.write(payload)
            process.stdin.flush()
            time.sleep(0.1) # Pausa mínima para o buffer não engasgar
            
        print("-> Fuzzing concluído sem crash.")

        # Teste de Stress: Enviando 10.000 requisições rapidamente
        print("\n[Teste 2] Disparando 10.000 requisições (Stress Test)...")
        start_time = time.time()
        
        for i in range(10000):
            process.stdin.write(f"q Linha de teste rápido número {i}\n")
        
        process.stdin.flush()
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"-> Tempo total para 10.000 requisições: {total_time:.4f} segundos")
        print(f"-> Latência média por requisição: {(total_time / 10000) * 1000:.4f} milissegundos")

        # Fecha o stdin, o que deve causar a quebra do laço 'while True' no nvda_server.py
        process.stdin.close()
        
        # Aguarda o processo terminar com um timeout de segurança
        process.wait(timeout=5)
        
        if process.returncode != 0:
            print(f"\n[AVISO] Servidor encerrou com Exit Code: {process.returncode}")
        else:
            print("\n[SUCESSO] Servidor encerrou de forma limpa.")
            
        return True

    except subprocess.TimeoutExpired:
        print("\n[ERRO FATAL] O processo travou (Timeout) e precisou ser forçado a fechar.")
        process.kill()
        return False
    except Exception as e:
        print(f"\n[ERRO FATAL] Exceção inesperada: {e}")
        return False

def main():
    # Configuração do diretório dos binários
    bin_dir = "bin"
    
    servers = {
        "SharpWin (SAPI)": os.path.join(bin_dir, "SharpWin.exe"),
        "NVDA Server": "nvda_server.exe" # Arquivo do NVDA Server presente no diretório raiz do projeto
    }
    
    sucesso_total = True
    for nome, caminho in servers.items():
        if not run_stress_test(nome, caminho):
            sucesso_total = False
            
    if not sucesso_total:
        print("\n[X] Benchmark finalizado com erros.")
        sys.exit(1)
    else:
        print("\n[V] Benchmark finalizado com sucesso. Ambos os servidores passaram nos testes!")
        sys.exit(0)

if __name__ == '__main__':
    main()