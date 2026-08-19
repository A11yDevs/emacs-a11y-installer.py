import platform
import sys
import subprocess
import os
import shutil
import glob
from rich.console import Console

console = Console()

# ---------------------------------------------------------
# >> Classe Base com Funções Auxiliares
# ---------------------------------------------------------
# Classe que fornece funcionalidades básicas para a instalação e configuração do ambiente de acessibilidade audível.
class BaseInstaller:
    def run_command(self, cmd, shell=False, cwd=None, env=None):
        """Executa comandos ocultando o output padrão para não poluir o leitor de telas."""
        try:
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd, env=env, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Ocorreu um erro crítico ao executar a etapa:[/bold red] {' '.join(cmd)}")
            console.print(f"[red]Detalhes do erro:[/red] {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            sys.exit(1)

    # Função que injeta o arquivo de configuração de acessibilidade correspondente ao sistema operacional.
    def inject_accessibility_el(self, os_name, use_native):
        """Copia o arquivo .el de acessibilidade correspondente para a pasta do usuário."""
        emacs_dir = os.path.expanduser("~/.emacs.d")
        lisp_dir = os.path.join(emacs_dir, "lisp")
        os.makedirs(lisp_dir, exist_ok=True)
        dest_file = os.path.join(lisp_dir, "init-accessibility.el")
        
        # Define qual módulo de acessibilidade será utilizado
        if os_name == "Windows" and not use_native: # Para Windows (Desenvolvedor)
            source_name = "init-a11y-win-dev.el"
        elif os_name == "Windows" and use_native: # Para Windows (NVDA)
            source_name = "init-a11y-win-native.el"
        else:
            # Para Linux (eSpeak NG)
            source_name = "init-a11y-linux-native.el"
            
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
        source_path = os.path.join(base_path, source_name)
        
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_file)
                console.print(f"[green]Módulo de configuração '{source_name}' injetado com sucesso.[/green]")
            else:
                console.print(f"[bold red]Erro crítico: Arquivo '{source_name}' não encontrado no pacote do instalador.[/bold red]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Erro ao copiar o arquivo de acessibilidade:[/bold red] {e}")
            sys.exit(1)

    def inject_init_el(self, server_name, extra_elisp=""):
        """Gera e injeta o arquivo de configuração base (init.el) automaticamente."""
        console.print("[yellow]Gerando e injetando arquivo de configuração base. Por favor, aguarde.[/yellow]")
        
        emacs_dir = os.path.expanduser("~/.emacs.d")
        os.makedirs(emacs_dir, exist_ok=True)
        init_file = os.path.join(emacs_dir, "init.el")

        elisp_code = f"""
;; Configuração Base do GNU Emacs/Emacspeak

;; Carrega as configurações de acessibilidade de acordo com a arquitetura/escolha do usuário
(load (expand-file-name "lisp/init-accessibility.el" user-emacs-directory))

;; Definição do Servidor de Áudio
(setq dtk-program "{server_name}")

;; Carregamento do Emacspeak
(setq emacspeak-directory "~/.emacs.d/emacspeak")
(load-file (expand-file-name "lisp/emacspeak-setup.el" emacspeak-directory))

;; Otimizações para Sessões Interativas
(add-hook 'comint-mode-hook 
          (lambda () 
            (setq comint-prompt-read-only t)
            (emacspeak-auditory-icon 'open-object)))

;; Configurações Específicas da Plataforma
{extra_elisp}

;; Otimizações Visuais
(menu-bar-mode -1)
(tool-bar-mode -1)
(scroll-bar-mode -1)
"""
        try:
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(elisp_code)
            console.print("[green]Arquivo de configuração base injetado com sucesso.[/green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao escrever o arquivo de configuração base:[/bold red] {e}")
            sys.exit(1)

    # Função que gera o arquivo de mapeamento do Emacspeak usando o próprio GNU Emacs.
    def generate_emacspeak_loaddefs(self, emacspeak_dir):
        """Gera o arquivo de mapeamento do Emacspeak usando o próprio GNU Emacs."""
        console.print("[yellow]Gerando mapa de funções do Emacspeak...[/yellow]")
        lisp_dir = os.path.join(emacspeak_dir, "lisp").replace("\\", "/")
        loaddefs_file = os.path.join(lisp_dir, "emacspeak-loaddefs.el").replace("\\", "/")
        
        build_el = os.path.join(emacspeak_dir, "build-loaddefs.el")
        emacs_cmd = shutil.which("emacs")
        
        if not emacs_cmd:
            if platform.system() == "Windows":
                possiveis_caminhos = glob.glob(r"C:\Program Files\Emacs\*\bin\emacs.exe") + \
                                     glob.glob(r"C:\Program Files\GNU Emacs\*\bin\emacs.exe") + \
                                     glob.glob(r"C:\Program Files\Emacs\bin\emacs.exe")
            else:
                possiveis_caminhos = ["/usr/bin/emacs", "/usr/local/bin/emacs"]
                possiveis_caminhos = [p for p in possiveis_caminhos if os.path.exists(p)]
            
            if possiveis_caminhos:
                emacs_cmd = possiveis_caminhos[0]
            else:
                console.print("[bold red]O Emacs foi instalado, mas o instalador não conseguiu localizá-lo para a etapa final.[/bold red]")
                console.print("[yellow]Solução: Feche este terminal, abra um novo (para recarregar o PATH) e rode o instalador novamente.[/yellow]")
                sys.exit(1)
                
        emacs_cmd = emacs_cmd or "emacs"
        
        elisp_code = f"""
        (require 'autoload)
        (let ((generated-autoload-file "{loaddefs_file}"))
          (if (fboundp 'loaddefs-generate)
              (loaddefs-generate "{lisp_dir}" generated-autoload-file)
            (update-directory-autoloads "{lisp_dir}")))
        """
        try:
            with open(build_el, "w", encoding="utf-8") as f:
                f.write(elisp_code)
                
            self.run_command([emacs_cmd, "--batch", "-l", build_el])
            
            if os.path.exists(build_el):
                os.remove(build_el)
                
            console.print("[green]Arquivo emacspeak-loaddefs.el gerado com sucesso.[/green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao gerar os loaddefs do Emacspeak:[/bold red] {e}")
            sys.exit(1)


# ---------------------------------------------------------
# >> Módulo Windows (10/11)
# ---------------------------------------------------------
# Classe que implementa a instalação e configuração do ambiente em sistemas Windows.
class WindowsInstaller(BaseInstaller):
    def install_windows_package(self, package_name, winget_id, choco_id):
        if shutil.which("winget"):
            self.run_command(["winget", "install", winget_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"])
        elif shutil.which("choco"):
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])
        else:
            console.print("[yellow]Gerenciador de pacotes não encontrado. Instalando Chocolatey...[/yellow]")
            choco_cmd = 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))'
            self.run_command(["powershell", "-Command", choco_cmd])
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])

    # Função que verifica e instala as dependências necessárias no sistema Windows.
    def install_dependencies(self):
        console.print("[yellow]Verificando dependências no sistema Windows.[/yellow]")
        if not shutil.which("git"):
            console.print("[yellow]Instalando Git. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("Git", "Git.Git", "git")
        if not shutil.which("emacs"):
            console.print("[yellow]Instalando GNU Emacs. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("GNU Emacs", "GNU.Emacs", "emacs")

    # Função que configura o Emacspeak e injeta os arquivos necessários para a integração com NVDA.
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Extraindo e configurando o servidor de áudio da aplicação.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        os.makedirs(emacs_dir, exist_ok=True)
        
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial do Emacspeak. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                console.print("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório...[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                sys.exit(1)
            
            self.generate_emacspeak_loaddefs(emacspeak_dir)
        
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")

        # Copia os arquivos binários necessários para a pasta do Emacs
        if use_native:
            is_64bit = platform.architecture()[0] == '64bit'
            dll_name = "nvdaControllerClient64.dll" if is_64bit else "nvdaControllerClient32.dll"
            files_to_copy = ["nvda_server.exe", dll_name]
            server_executable = "nvda_server.exe"
        else:
            files_to_copy = ["SharpWin.exe"]
            server_executable = "SharpWin.exe"
            
        # Injeta o arquivo Lisp de acordo com o ambiente
        self.inject_accessibility_el("Windows", use_native)
            
        for file_name in files_to_copy:
            source = os.path.join(base_path, file_name)
            dest = os.path.join(emacs_dir, file_name)
            try:
                if os.path.exists(source):
                    shutil.copy2(source, dest)
                else:
                    console.print(f"[red]Aviso: O arquivo {file_name} não foi encontrado no pacote.[/red]")
            except Exception as e:
                console.print(f"[bold red]Erro ao copiar {file_name}:[/bold red] {e}")

        # Define o caminho do servidor de áudio para o Emacspeak
        server_elisp_path = os.path.join(emacs_dir, server_executable).replace("\\", "/")
        self.inject_init_el(
            server_name=server_elisp_path,
            extra_elisp="(setq explicit-shell-file-name \"powershell.exe\")"
        )


# ---------------------------------------------------------
# >> Módulo Linux (Debian/Ubuntu)
# ---------------------------------------------------------
# Classe que implementa a instalação e configuração do ambiente em sistemas Linux baseados em Debian ou Ubuntu.
class LinuxInstaller(BaseInstaller):
    def install_dependencies(self):
        console.print("[cyan]Sistema Debian ou Ubuntu detectado. Verificando dependências.[/cyan]")
        pacotes = ["emacs", "git", "tcl", "tclx", "espeak-ng", "make", "g++"]
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        
        console.print("[yellow]Atualizando repositórios de sistema silenciosamente.[/yellow]")
        self.run_command(["sudo", "apt-get", "update", "-qq"])
        
        console.print("[yellow]Instalando pacotes base. Esse processo é silencioso.[/yellow]")
        self.run_command(["sudo", "-E", "apt-get", "install", "-y", "-qq"] + pacotes, env=env)

    # Função que configura o Emacspeak e compila a integração nativa com eSpeak NG.
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Configurando Emacspeak e compilando integração nativa.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")

        # Cria o diretório do Emacspeak se não existir
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                console.print("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório...[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                sys.exit(1)

            console.print("[yellow]Gerando arquivos base de configuração (make config).[/yellow]")
            self.run_command(["make", "config", "-s"], cwd=emacspeak_dir)

        console.print("[yellow]Compilando servidor de áudio internamente.[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        self.run_command(["make", "-s"], cwd=make_dir)
        console.print("[green]Servidor de áudio compilado com sucesso.[/green]")

        # Injeta o arquivo Lisp de acordo com o ambiente
        self.inject_accessibility_el("Linux", use_native)
        self.inject_init_el(server_name="espeak")


# ---------------------------------------------------------
# >> Análise de Ambiente
# ---------------------------------------------------------
# Função que detecta o sistema operacional e retorna a classe de instalador correspondente.
def get_installer():
    os_name = platform.system()
    if os_name == "Windows":
        console.print("[bold blue]Ambiente Windows detectado.[/bold blue]")
        return WindowsInstaller()
    elif os_name == "Linux":
        if shutil.which("apt-get") is None:
            console.print("[bold red]Erro crítico: Este script suporta apenas distribuições baseadas em Debian ou Ubuntu.[/bold red]")
            sys.exit(1)
        console.print("[bold blue]Ambiente Linux detectado.[/bold blue]")
        return LinuxInstaller()
    else:
        console.print(f"[bold red]Erro crítico: Sistema operacional não suportado pelo instalador.[/bold red]")
        sys.exit(1)


# ---------------------------------------------------------
# >> Execução Principal
# ---------------------------------------------------------
# Módulo principal do instalador, que inicia a execução das etapas de instalação e configuração.
if __name__ == "__main__":
    console.print("[bold cyan]Iniciando instalação do ambiente de acessibilidade audível - A11yDevs.[/bold cyan]\n")
    
    console.print("[bold]Selecione a configuração de acessibilidade de sua preferência:[/bold]")
    console.print("  [1] Configuração do Desenvolvedor (Arquivo de acessibilidade customizado)")
    console.print("  [2] Leitor de Telas Nativo (Windows: NVDA | Linux: eSpeak )")
    
    escolha = ""
    while escolha not in ["1", "2"]:
        escolha = input("\nDigite 1 ou 2 para selecionar: ").strip()
        
    use_native = (escolha == "2")
    
    installer = get_installer()
    installer.install_dependencies()
    installer.setup_emacspeak(use_native)

    # Finalização do executável
    console.print("\n[bold green]Todas as etapas foram concluídas com sucesso. O ambiente está pronto para uso.[/bold green]")
    input("\nPressione a tecla Enter para finalizar e fechar o instalador.")