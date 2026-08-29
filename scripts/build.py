import os
import subprocess
import shutil
import sys

# Função auxiliar para executar comandos do sistema
def run_command(cmd):
    print(f"Executando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    print("=== Iniciando Processo de Build ===")

    # Limpeza de builds anteriores
    print("\n[1/4] Limpando diretórios 'build' e 'dist'...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    # Compilar o connect_a11y.py
    print("\n[2/4] Compilando connect_a11y.py...")
    run_command([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        os.path.join("src", "connect_a11y.py")
    ])

    # Prepara e copia os binários necessários
    print("\n[3/4] Preparando dependências na pasta bin/...")
    if os.path.exists(os.path.join("dist", "connect_a11y.exe")):
        os.makedirs("bin", exist_ok=True)
        shutil.copy(os.path.join("dist", "connect_a11y.exe"), "bin")
        print("connect_a11y.exe copiado para a pasta bin/.")
    else:
        print("Erro: connect_a11y.exe não foi gerado.")
        sys.exit(1)

    # Compila o instalador principal apontando para os arquivos binários e de dados necessários
    print("\n[4/4] Compilando installer_a11y.py...")
    
    # Define o separador de caminho correto para o sistema operacional
    separator = ";" if os.name == "nt" else ":"
    
    run_command([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        # Adiciona todos os binários para a raiz do executável
        f"--add-binary=bin/connect_a11y.exe{separator}.",
        f"--add-binary=bin/nvdaControllerClient64.dll{separator}.",
        f"--add-binary=bin/nvdaControllerClient32.dll{separator}.",
        f"--add-binary=bin/SharpWin.exe{separator}.",
        
        # Adiciona os arquivos Lisp separados para a raiz executável
        f"--add-data=src/init-a11y-win-dev.el{separator}.",
        f"--add-data=src/init-a11y-win-native.el{separator}.",
        f"--add-data=src/init-a11y-linux-dev.el{separator}.",
        f"--add-data=src/init-a11y-linux-native.el{separator}.",
        
        os.path.join("src", "installer_a11y.py")
    ])

    print("\n=== Build concluído com sucesso! ===")
    print("O executável final 'installer_a11y.exe' está na pasta 'dist/'.")

if __name__ == '__main__':
    main()