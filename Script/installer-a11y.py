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
    def run_command(self, cmd, shell=False, cwd=None):
        """Executa comandos no sistema operacional e captura erros."""
        try:
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Erro crítico ao executar:[/bold red] {' '.join(cmd)}")
            console.print(f"[red]Detalhes: {e}[/red]")
            sys.exit(1)

    def inject_init_el(self, server_name, extra_elisp=""):
        """Gera e injeta o arquivo de configuração base (init.el) automaticamente na máquina do usuário."""
        console.print("[yellow]Gerando e injetando configuração base (init.el)...[/yellow]")
        
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
            console.print(f"[green]Arquivo de configuração base (init.el) injetado com sucesso em: {init_file}[/green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao escrever o arquivo de configuração base:[/bold red] {e}")
            sys.exit(1)


# ---------------------------------------------------------
# >> Módulo Windows (10/11)
# ---------------------------------------------------------
class WindowsInstaller(BaseInstaller):
    def install_dependencies(self):
        console.print("[yellow]Verificando/Instalando Git e Emacs no Windows (via winget)...[/yellow]")
        # Instala Git e Emacs silenciosamente usando winget
        self.run_command(["winget", "install", "Git.Git", "--silent"])
        self.run_command(["winget", "install", "GNU.Emacs", "--silent"])
        
    def setup_emacspeak(self):
        console.print("[yellow]Extraindo e configurando SharpWin.exe...[/yellow]")
        
        emacs_dir = os.path.expanduser("~/.emacs.d")
        os.makedirs(emacs_dir, exist_ok=True)
        
        # Identifica se está rodando como script .py ou como .exe
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
            
        sharpwin_source = os.path.join(base_path, "SharpWin.exe")
        sharpwin_dest = os.path.join(emacs_dir, "SharpWin.exe")
        
        try:
            if os.path.exists(sharpwin_source):
                shutil.copy2(sharpwin_source, sharpwin_dest)
                console.print("[green]SharpWin.exe extraído e copiado com sucesso.[/green]")
            else:
                console.print("[red]Aviso: SharpWin.exe não foi encontrado!.[/red]")
        except Exception as e:
            console.print(f"[bold red]Erro ao copiar SharpWin.exe:[/bold red] {e}")

        # Injeta o init.el com caminhos usando o modo padrão do Lisp
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
        console.print("[cyan]Detectado Debian/Ubuntu. Instalando dependências via apt...[/cyan]")
        
        pacotes = ["emacs", "git", "tcl", "tclx", "espeak-ng", "make", "g++"]
        
        console.print("[yellow]Atualizando repositórios (pode solicitar senha root)...[/yellow]")
        self.run_command(["sudo", "apt", "update"])
        
        console.print("[yellow]Instalando pacotes base...[/yellow]")
        self.run_command(["sudo", "apt", "install", "-y"] + pacotes)
        
    def setup_emacspeak(self):
        console.print("[yellow]Configurando Emacspeak e compilando servidor de áudio nativo...[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        
        # Clona o repositório
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Clonando repositório oficial do Emacspeak...[/yellow]")
            self.run_command(["git", "clone", "https://github.com/tvraman/emacspeak.git", emacspeak_dir])
            
        # Compila o servidor eSpeak nativo
        console.print("[yellow]Compilando integração com eSpeak-ng...[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        self.run_command(["make"], cwd=make_dir)
        console.print("[green]Servidor de áudio compilado com sucesso![/green]")
            
        # Injeta o init.el apontando para o servidor padrão do eSpeak
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
        if shutil.which("apt") is None:
            console.print("[bold red]Erro: Este script atualmente suporta apenas distribuições baseadas em Debian/Ubuntu (apt).[/bold red]")
            sys.exit(1)
            
        console.print("[bold blue]Ambiente Linux (Debian/Ubuntu) detectado.[/bold blue]")
        return LinuxInstaller()
        
    else:
        console.print(f"[bold red]Erro: Sistema {os_name} não suportado.[/bold red]")
        sys.exit(1)


# ---------------------------------------------------------
# >> Execução Principal
# ---------------------------------------------------------
if __name__ == "__main__":
    console.print("[bold cyan]--- Iniciando Instalador do Ambiente Emacs/Emacspeak ---[/bold cyan]\n")
    
    installer = get_installer()
    installer.install_dependencies()
    installer.setup_emacspeak()
    
    console.print("\n[bold green]Instalação e configuração concluídas com sucesso![/bold green]")