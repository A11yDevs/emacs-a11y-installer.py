import platform
import sys
import subprocess
import os
import shutil
from rich.console import Console

console = Console()

# ---------------------------------------------------------
# >> Classe Base com Funções Auxiliares
# ---------------------------------------------------------
class BaseInstaller:
    def run_command(self, cmd, shell=False, cwd=None, env=None):
        """Executa comandos ocultando o output padrão para não poluir o leitor de telas. 
        Só exibe texto em caso de erro crítico."""
        try:
            # Esconde logs de download e compilação.
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd, env=env, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Ocorreu um erro crítico ao executar a etapa:[/bold red] {' '.join(cmd)}")
            # Imprime o erro real capturado para diagnóstico do usuário, mas sem poluir o leitor de telas com logs desnecessários.
            console.print(f"[red]Detalhes do erro:[/red] {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            sys.exit(1)

    def inject_init_el(self, server_name, extra_elisp=""):
        """Gera e injeta o arquivo de configuração base (init.el) automaticamente."""
        console.print("[yellow]Gerando e injetando arquivo de configuração base. Por favor, aguarde.[/yellow]")
        
        emacs_dir = os.path.expanduser("~/.emacs.d")
        os.makedirs(emacs_dir, exist_ok=True)
        init_file = os.path.join(emacs_dir, "init.el")

        elisp_code = f"""
;; Configuração Base do GNU Emacs/Emacspeak

;; Carregamento do Emacspeak
(setq emacspeak-directory "~/.emacs.d/emacspeak")
(load-file (expand-file-name "lisp/emacspeak-setup.el" emacspeak-directory))

;; Definição do Servidor de Áudio
(setq dtks-program "{server_name}")

;; Otimizações para Sessões Interativas
;; Garante bom comportamento do leitor com PowerShell, aplicações em texto ou buffers gerais.
(add-hook 'comint-mode-hook 
          (lambda () 
            (setq comint-prompt-read-only t)
            (emacspeak-auditory-icon 'open-object)))

;; Configurações Específicas da Plataforma
{extra_elisp}

;; Otimizações Visuais
;; Evita que a interface gráfica atrapalhe a performance do leitor
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


# ---------------------------------------------------------
# >> Módulo Windows (10/11)
# ---------------------------------------------------------
class WindowsInstaller(BaseInstaller):
    def install_windows_package(self, package_name, winget_id, choco_id):
        """Tenta instalar via Winget. Se falhar, usa ou instala o Chocolatey."""
        if shutil.which("winget"):
            self.run_command(["winget", "install", winget_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"])
        elif shutil.which("choco"):
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])
        else:
            console.print("[yellow]Gerenciador de pacotes não encontrado. Instalando Chocolatey em segundo plano...[/yellow]")
            choco_cmd = 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))'
            self.run_command(["powershell", "-Command", choco_cmd])
            # Após instalar o chocolatey, tenta instalar o pacote novamente
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])

    def install_dependencies(self):
        console.print("[yellow]Verificando dependências no sistema Windows.[/yellow]")
        
        if shutil.which("git"):
            console.print("[green]Git já está instalado. Pulando etapa.[/green]")
        else:
            console.print("[yellow]Instalando Git. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("Git", "Git.Git", "git")

        if shutil.which("emacs"):
            console.print("[green]GNU Emacs já está instalado. Pulando etapa.[/green]")
        else:
            console.print("[yellow]Instalando GNU Emacs.Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("GNU Emacs", "GNU.Emacs", "emacs")
        
    def setup_emacspeak(self):
        console.print("[yellow]Extraindo e configurando o servidor de áudio da aplicação.[/yellow]")
        
        emacs_dir = os.path.expanduser("~/.emacs.d")
        os.makedirs(emacs_dir, exist_ok=True)
        
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
            
        sharpwin_source = os.path.join(base_path, "SharpWin.exe")
        sharpwin_dest = os.path.join(emacs_dir, "SharpWin.exe")
        
        try:
            if os.path.exists(sharpwin_source):
                shutil.copy2(sharpwin_source, sharpwin_dest)
                console.print("[green]Servidor de áudio extraído e copiado com sucesso.[/green]")
            else:
                console.print("[red]Aviso: O arquivo do servidor de áudio não foi encontrado no pacote.[/red]")
        except Exception as e:
            console.print(f"[bold red]Erro ao copiar o servidor de áudio:[/bold red] {e}")

        sharpwin_elisp_path = sharpwin_dest.replace("\\", "/")
        self.inject_init_el(
            server_name=sharpwin_elisp_path,
            extra_elisp="(setq explicit-shell-file-name \"powershell.exe\")"
        )


# ---------------------------------------------------------
# >> Módulo Linux (Debian/Ubuntu)
# ---------------------------------------------------------
class LinuxInstaller(BaseInstaller):
    def install_dependencies(self):
        console.print("[cyan]Sistema Debian ou Ubuntu detectado. Verificando dependências.[/cyan]")
        
        pacotes = ["emacs", "git", "tcl", "tclx", "espeak-ng", "make", "g++"]
        
        # Configura o ambiente para não exibir prompts interativos na tela
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        
        console.print("[yellow]Atualizando repositórios de sistema silenciosamente. Se necessário, o terminal pedirá sua senha.[/yellow]")
        self.run_command(["sudo", "apt-get", "update", "-qq"])
        
        console.print("[yellow]Instalando pacotes base. Esse processo é silencioso e pode demorar alguns minutos.[/yellow]")
        # Comando de instalação silenciosa dos pacotes necessários, suprimindo a saída padrão para não poluir o leitor de telas
        self.run_command(["sudo", "-E", "apt-get", "install", "-y", "-qq"] + pacotes, env=env)
        
    def setup_emacspeak(self):
        console.print("[yellow]Configurando Emacspeak e compilando integração nativa.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial. Aguarde.[/yellow]")
            # Clonagem silenciosa do repositório oficial do Emacspeak
            self.run_command(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir])
            
        console.print("[yellow]Compilando servidor de áudio internamente.[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        # Compilação silenciosa do servidor de áudio nativo (espeak)
        self.run_command(["make", "-s"], cwd=make_dir)
        console.print("[green]Servidor de áudio compilado com sucesso.[/green]")
            
        self.inject_init_el(server_name="espeak")


# ---------------------------------------------------------
# >> Análise de Ambiente
# ---------------------------------------------------------
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
if __name__ == "__main__":
    console.print("[bold cyan]Iniciando Instalador do Ambiente de Desenvolvimento.[/bold cyan]\n")
    
    installer = get_installer()
    installer.install_dependencies()
    installer.setup_emacspeak()
    
    console.print("\n[bold green]Todas as etapas foram concluídas com sucesso. O ambiente está pronto para uso.[/bold green]")
    
    # Input final para manter a janela aberta em caso de execução direta no Windows
    input("\nPressione a tecla Enter para finalizar e fechar o instalador.")
