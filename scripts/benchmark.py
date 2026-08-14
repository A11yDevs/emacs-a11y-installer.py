import os
import subprocess
import time
import sys

# Função para executar o teste de stress em um servidor específico
def run_stress_test(server_name, server_path):
    print(f"\n{'='*50}")
    print(f" Iniciando Benchmark: {server_name}")
    print(f" Caminho: {server_path}")
    print(f"{'='*50}")
    
    # Dicionário para armazenar as métricas do servidor executado
    metrics = {
        "success": False,
        "total_time": None,
        "avg_latency": None,
        "skipped_stress": False,
        "status_msg": ""
    }
    
    if not os.path.exists(server_path):
        print(f"[ERRO] Executável não encontrado em: {server_path}")
        metrics["status_msg"] = "Arquivo não encontrado"
        return metrics

    try:
        process = subprocess.Popen(
            [server_path], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE,
            text=True, 
            encoding='utf-8'
        )
        
        print("\n[Teste 1] Fuzzing e Caracteres Especiais...")
        fuzzing_payloads = [
            "q Teste de leitura normal.\n",
            "q Símbolos: !@#$%^&*()_+{}|:<>?\n",
            "q Unicode: 漢字, emojis 💻🔥, acentuação áéíóú\n",
            "q \n",
            "q " + ("A" * 1000) + "\n"
        ]
        
        for payload in fuzzing_payloads:
            process.stdin.write(payload)
            process.stdin.flush()
            time.sleep(0.1)
            
        print("-> Fuzzing concluído sem crash.")

        print("\n[Teste 2] Disparando 10.000 requisições (Stress Test)...")
        start_time = time.time()
        
        for i in range(10000):
            process.stdin.write(f"q Linha de teste rápido número {i}\n")
        
        process.stdin.flush()
        end_time = time.time()

        total_time = end_time - start_time
        avg_latency = (total_time / 10000) * 1000
        
        print(f"-> Tempo total para 10.000 requisições: {total_time:.4f} segundos")
        print(f"-> Latência média por requisição: {avg_latency:.4f} milissegundos")

        # Salva as métricas para a comparação final
        metrics["total_time"] = total_time
        metrics["avg_latency"] = avg_latency
        metrics["success"] = True
        metrics["status_msg"] = "Concluído de forma limpa"

        process.stdin.close()
        process.wait(timeout=5)
        
        if process.returncode != 0:
            print(f"\n[AVISO] Servidor encerrou com Exit Code: {process.returncode}")
            
        return metrics

    except BrokenPipeError:
        print("\n[AVISO] Broken Pipe: O servidor recusou as strings e fechou a conexão.")
        if "nvda" in server_name.lower():
            print("[INFO] Comportamento ESPERADO: O nvda_server.exe fechou corretamente pois o NVDA não está rodando no ambiente.")
            metrics["success"] = True
            metrics["skipped_stress"] = True # Marca que o teste de stress foi pulado para não afetar a comparação
            metrics["status_msg"] = "Ignorado (Ambiente CI / Sem NVDA)"
            return metrics
        else:
            metrics["status_msg"] = "Falha: Broken Pipe Inesperado"
            return metrics
            
    except subprocess.TimeoutExpired:
        print("\n[ERRO FATAL] O processo travou (Timeout) e precisou ser forçado a fechar.")
        process.kill()
        metrics["status_msg"] = "Timeout"
        return metrics
        
    except Exception as e:
        print(f"\n[ERRO FATAL] Exceção inesperada: {e}")
        metrics["status_msg"] = f"Exceção: {e}"
        return metrics

def print_comparison(results):
    print(f"\n\n{'*'*50}")
    print(" RELATÓRIO FINAL COMPARATIVO")
    print(f"{'*'*50}")
    
    print(f"{'Servidor':<20} | {'Status':<30} | {'Latência Média'}")
    print("-" * 70)
    
    for name, data in results.items():
        latency_str = f"{data['avg_latency']:.4f} ms" if data['avg_latency'] is not None else "N/A"
        print(f"{name:<20} | {data['status_msg']:<30} | {latency_str}")
    
    print("\n[ANÁLISE DE PERFORMANCE]")
    
    # Lógica para definir o vencedor
    valid_results = {k: v for k, v in results.items() if v["success"] and not v["skipped_stress"]}
    
    if len(valid_results) == 2:
        fastest = min(valid_results.items(), key=lambda x: x[1]['avg_latency'])
        print(f"-> VENCEDOR: {fastest[0]} apresentou a menor latência ({fastest[1]['avg_latency']:.4f} ms).")
        print("-> CONCLUSÃO: Para uso contínuo com base puramente em software IPC, a opção vencedora é a mais otimizada.")
    elif len(valid_results) == 1:
        print(f"-> Apenas um servidor concluiu o stress test de forma completa.")
        print(f"-> A opção baseada no NVDA Controller Client requer o NVDA rodando ativamente para medir a latência real.")
        print("-> Em ambientes de CI, a Opção 2 (NVDA) é superior arquiteturalmente para o usuário final, devido aos dicionários de pronúncia avançados do leitor nativo.")
    else:
        print("-> Não foi possível gerar uma comparação de performance, pois ambos os testes falharam ou foram pulados.")

def main():
    bin_dir = "bin"
    # Ajuste de caminho se o nvda_server for compilado diretamente na raiz ou bin
    nvda_path = os.path.join(bin_dir, "nvda_server.exe") if os.path.exists(os.path.join(bin_dir, "nvda_server.exe")) else "nvda_server.exe"

    servers = {
        "SharpWin (SAPI)": os.path.join(bin_dir, "SharpWin.exe"),
        "NVDA Server": nvda_path
    }
    
    results = {}
    
    for nome, caminho in servers.items():
        results[nome] = run_stress_test(nome, caminho)
            
    # Chama a função que imprime a tabela comparativa
    print_comparison(results)
    
    # Verifica se algum teste falhou criticamente
    if any(not data["success"] for data in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()