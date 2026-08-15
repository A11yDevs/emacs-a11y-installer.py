import os
import subprocess
import time
import sys
import psutil

# Função para executar o benchmark de estresse e latência
def run_stress_test(server_name, server_path):
    print(f"\n{'='*50}")
    print(f" Iniciando Benchmark: {server_name}")
    print(f" Caminho: {server_path}")
    print(f"{'='*50}")

    # Inicializa o dicionário de métricas com valores padrão
    metrics = {
        "success": False,
        "total_time": None,
        "avg_latency": None,
        "peak_ram_mb": None,
        "cpu_percent": None,
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
        
        # Usando psutil para monitorar o processo filho
        ps_process = psutil.Process(process.pid)
        
        print("\n[Teste 1] Fuzzing e Caracteres Especiais...")
        # Envia uma série de payloads de teste para o servidor, incluindo caracteres especiais e strings longas
        fuzzing_payloads = [
            "q Teste normal.\n",
            "q Símbolos: !@#$%^&*()_+{}|:<>?\n",
            "q Unicode: 漢字, emojis 💻🔥, acentuação áéíóú\n",
            "q \n",
            "q " + ("A" * 1000) + "\n"
        ]
        
        for payload in fuzzing_payloads:
            process.stdin.write(payload)
            process.stdin.flush()
            time.sleep(0.1)
            
        print("-> Fuzzing concluído.")

        print("\n[Teste 2] Disparando 10.000 requisições (Stress & Profiling)...")
        
        # Prepara a medição de CPU (a primeira chamada serve de âncora/ponto de partida)
        ps_process.cpu_percent(interval=None)
        
        peak_ram = 0
        start_time = time.time()

        # Envia 10.000 requisições de teste para o servidor
        for i in range(10000):
            process.stdin.write(f"q Linha de teste {i}\n")
            
            # A cada 1000 envios, mede a RAM para registrar o pico sem gargalar o teste
            if i % 1000 == 0:
                current_ram = ps_process.memory_info().rss / (1024 * 1024) # Converte bytes para Megabytes
                if current_ram > peak_ram:
                    peak_ram = current_ram
        
        process.stdin.flush()
        end_time = time.time()

        # Mede o uso de CPU desde a chamada da âncora antes do loop
        cpu_usage = ps_process.cpu_percent(interval=None)
        
        # Última checagem de RAM após o fim do loop
        final_ram = ps_process.memory_info().rss / (1024 * 1024)
        if final_ram > peak_ram:
            peak_ram = final_ram

        total_time = end_time - start_time
        avg_latency = (total_time / 10000) * 1000
        
        print(f"-> Tempo total: {total_time:.4f} segundos")
        print(f"-> Latência média: {avg_latency:.4f} ms")
        print(f"-> Pico de RAM: {peak_ram:.2f} MB")
        print(f"-> Uso médio de CPU do processo: {cpu_usage:.2f}%")

        metrics["total_time"] = total_time
        metrics["avg_latency"] = avg_latency
        metrics["peak_ram_mb"] = peak_ram
        metrics["cpu_percent"] = cpu_usage
        metrics["success"] = True
        metrics["status_msg"] = "Concluído de forma limpa"

        process.stdin.close()
        process.wait(timeout=5)
            
        return metrics

    # Lidando com exceções específicas para BrokenPipeError e NoSuchProcess
    except BrokenPipeError:
        print("\n[AVISO] Broken Pipe: Conexão fechada.")
        if "nvda" in server_name.lower():
            metrics["success"] = True
            metrics["skipped_stress"] = True
            metrics["status_msg"] = "Ignorado (Sem NVDA)"
            return metrics
        else:
            metrics["status_msg"] = "Falha: Broken Pipe"
            return metrics

    # Lidando com a exceção NoSuchProcess caso o processo seja encerrado prematuramente
    except psutil.NoSuchProcess:
        print("\n[ERRO] O processo foi encerrado antes da coleta de métricas de hardware.")
        metrics["status_msg"] = "Processo morreu prematuramente"
        return metrics

    # Lidando com qualquer outra exceção inesperada
    except Exception as e:
        print(f"\n[ERRO FATAL] Exceção inesperada: {e}")
        metrics["status_msg"] = f"Exceção: {e}"
        return metrics

# Função para imprimir o relatório final comparativo
def print_comparison(results):
    print(f"\n\n{'*'*85}")
    print(" RELATÓRIO FINAL COMPARATIVO (PERFORMANCE E HARDWARE)")
    print(f"{'*'*85}")
    
    print(f"{'Servidor':<18} | {'Status':<25} | {'Latência':<10} | {'Pico RAM':<10} | {'CPU'}")
    print("-" * 85)
    
    for name, data in results.items():
        if data['skipped_stress'] or not data['success']:
            print(f"{name:<18} | {data['status_msg']:<25} | {'N/A':<10} | {'N/A':<10} | {'N/A'}")
        else:
            latency = f"{data['avg_latency']:.3f} ms"
            ram = f"{data['peak_ram_mb']:.2f} MB"
            cpu = f"{data['cpu_percent']:.1f}%"
            print(f"{name:<18} | {data['status_msg']:<25} | {latency:<10} | {ram:<10} | {cpu}")
    
    print("\n[ANÁLISE DO SISTEMA]")
    
    valid_results = {k: v for k, v in results.items() if v["success"] and not v["skipped_stress"]}
    
    if len(valid_results) == 2:
        fastest = min(valid_results.items(), key=lambda x: x[1]['avg_latency'])
        lightest_ram = min(valid_results.items(), key=lambda x: x[1]['peak_ram_mb'])
        
        print(f"-> MAIS RÁPIDO: {fastest[0]} ({fastest[1]['avg_latency']:.3f} ms/req)")
        print(f"-> MENOR CONSUMO DE RAM: {lightest_ram[0]} ({lightest_ram[1]['peak_ram_mb']:.2f} MB)")
        
        if fastest[0] == lightest_ram[0]:
            print(f"-> VENCEDOR ABSOLUTO: {fastest[0]} dominou tanto em velocidade quanto em eficiência de memória.")
        else:
            print("-> EMPATE TÉCNICO: Uma opção é mais rápida, mas a outra consome menos memória do sistema.")
            
    elif len(valid_results) == 1:
        print("-> Apenas um servidor concluiu o stress test de forma completa com métricas de hardware.")

# Função principal para executar o benchmark
def main():
    bin_dir = "bin"
    nvda_path = os.path.join(bin_dir, "nvda_server.exe") if os.path.exists(os.path.join(bin_dir, "nvda_server.exe")) else "nvda_server.exe"

    servers = {
        "SharpWin (SAPI)": os.path.join(bin_dir, "SharpWin.exe"),
        "NVDA Server": nvda_path
    }
    
    results = {}
    
    for nome, caminho in servers.items():
        results[nome] = run_stress_test(nome, caminho)
            
    print_comparison(results)
    
    if any(not data["success"] for data in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()