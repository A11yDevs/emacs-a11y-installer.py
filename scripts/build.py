import os
import subprocess
import shutil
import sys

def run_command(cmd):
    print(f"Executando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    print("=== Iniciando Processo de Build ===")

    # Limpeza de builds anteriores
    print("\n[1/4] Limpando diretórios 'build' e 'dist'...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    # Compilar o nvda_server.py (na pasta src/)
    print("\n[2/4] Compilando nvda_server.py...")
    run_command([
        sys.executable, "python-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        os.path.join("src", "nvda_server.py")
    ])

    # Move o nvda_server.exe gerado para a pasta bin/
    # Isso organiza todas as dependências em um lugar só antes do empacotamento final
    print("\n[3/4] Preparando dependências na pasta bin/...")
    if os.path.exists(os.path.join("dist", "nvda_server.exe")):
        os.makedirs("bin", exist_ok=True)
        shutil.copy(os.path.join("dist", "nvda_server.exe"), "bin")
        print("nvda_server.exe copiado para a pasta bin/.")
    else:
        print("Erro: nvda_server.exe não foi gerado.")
        sys.exit(1)

    # Compila o instalador principal apontando para os arquivos na pasta bin/
    print("\n[4/4] Compilando installer-a11y.py...")
    
    # O separador do PyInstaller para --add-binary é ';' no Windows e ':' no Linux
    separator = ";" if os.name == "nt" else ":"
    
    run_command([
        sys.executable, "python", "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        # Adiciona todos os binários da pasta 'bin' para a raiz ('.') do executável
        f"--add-binary=bin/nvda_server.exe{separator}.",
        f"--add-binary=bin/nvdaControllerClient64.dll{separator}.",
        f"--add-binary=bin/nvdaControllerClient32.dll{separator}.",
        f"--add-binary=bin/SharpWin.exe{separator}.",
        os.path.join("src", "installer-a11y.py")
    ])

    print("\n=== Build concluído com sucesso! ===")
    print("O executável final 'installer-a11y.exe' está na pasta 'dist/'.")

if __name__ == '__main__':
    main()