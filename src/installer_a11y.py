import platform
import sys
import subprocess
import os
import shutil
import glob
import threading
import tkinter as tk

# Importa a interface visual do programa.
from interface_a11y import InstallerGUI

# ---------------------------------------------------------
# >> Classe Base com Funções Auxiliares
# ---------------------------------------------------------
# Módulo inicial de instalação e definição de ambiente geral.
class BaseInstaller:
    def __init__(self, logger_func):
        self.log = logger_func

    # Executa limpando a tela para redução de textos e informações desnecessárias para o usuário.
    def run_command(self, cmd, shell=False, cwd=None, env=None):
        """Executa comandos ocultando o output padrão para não poluir o leitor de telas."""
        try:
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd, env=env, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.log(f"[bold red]Ocorreu um erro crítico ao executar a etapa:[/bold red] {' '.join(cmd)}")
            self.log(f"[red]Detalhes do erro:[/red] {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            raise Exception("Falha na execução de comando do sistema.")

    def check_native_prerequisites(self):
        """Método base para verificar se os pré-requisitos para o ambiente nativo estão instalados."""
        pass

    def inject_accessibility_el(self, os_name, use_native):
        """Copia o arquivo .el de acessibilidade correspondente para a pasta do usuário."""
        emacs_dir = os.path.expanduser("~/.emacs.d")
        lisp_dir = os.path.join(emacs_dir, "lisp")
        os.makedirs(lisp_dir, exist_ok=True)
        dest_file = os.path.join(lisp_dir, "init-accessibility.el")
        
        # Define qual módulo de acessibilidade será utilizado.
        if os_name == "Windows" and not use_native:
            source_name = "init-a11y-win-dev.el" # Para Windows (Desenvolvedor).
        elif os_name == "Windows" and use_native: # Para Windows (NVDA).
            source_name = "init-a11y-win-native.el"
        else:
            # Para Linux (eSpeak NG).
            source_name = "init-a11y-linux-native.el"
            
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
        source_path = os.path.join(base_path, source_name)
        
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_file)
                self.log(f"[green]Módulo de configuração '{source_name}' injetado com sucesso.[/green]")
            else:
                self.log(f"[bold red]Erro crítico: Arquivo '{source_name}' não encontrado no pacote do instalador.[/bold red]")
                raise Exception(f"Arquivo '{source_name}' ausente no pacote.")
        except Exception as e:
            self.log(f"[bold red]Erro ao copiar o arquivo de acessibilidade:[/bold red] {e}")
            raise Exception("Falha na injeção do arquivo de acessibilidade.")

    # Configurações base do ambiente (carrega o módulo de acessibilidade e aspectos base do ambiente).
    def inject_init_el(self, server_name, extra_elisp=""):
        """Gera e injeta o arquivo de configuração base (init.el) automaticamente."""
        self.log("[yellow]Gerando e injetando arquivo de configuração base. Por favor, aguarde.[/yellow]")
        
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
"""
        try:
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(elisp_code)
            self.log("[green]Arquivo de configuração base injetado com sucesso.[/green]")
        except Exception as e:
            self.log(f"[bold red]Erro ao escrever o arquivo de configuração base:[/bold red] {e}")
            raise Exception("Falha ao salvar init.el")

    # Carregamento do loaddefs para inicialização correta do emacspeak.
    def generate_emacspeak_loaddefs(self, emacspeak_dir):
        """Gera o arquivo de mapeamento do Emacspeak usando o próprio GNU Emacs."""
        self.log("[yellow]Gerando mapa de funções do Emacspeak...[/yellow]")
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
                self.log("[bold red]O Emacs foi instalado, mas o instalador não conseguiu localizá-lo para a etapa final.[/bold red]")
                self.log("[yellow]Solução: Feche o instalador, abra novamente e tente mais uma vez.[/yellow]")
                raise Exception("Executável do Emacs não localizado.")
                
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
                
            self.log("[green]Arquivo emacspeak-loaddefs.el gerado com sucesso.[/green]")
        except Exception as e:
            self.log(f"[bold red]Erro ao gerar os loaddefs do Emacspeak:[/bold red] {e}")
            raise Exception("Falha na geração dos loaddefs.")


# ---------------------------------------------------------
# >> Módulo Windows (10/11)
# ---------------------------------------------------------
# Módulo direcionado para instalação e configuração do ambiente para usuários Windows.
class WindowsInstaller(BaseInstaller):

    def check_native_prerequisites(self):
        if os.environ.get("CI_MOCK_NVDA") == "1":
            self.log("[green]Modo CI: Verificação do NVDA nativo ignorada.[/green]")
            return

        self.log("[yellow]Verificando pré-requisitos do ambiente nativo (NVDA)...[/yellow]")
        has_nvda = False
        
        # Verifica caminhos de instalação padrão do NVDA no Windows.
        nvda_paths = [
            r"C:\Program Files\NVDA\nvda.exe",
            r"C:\Program Files (x86)\NVDA\nvda.exe"
        ]
        if any(os.path.exists(p) for p in nvda_paths):
            has_nvda = True
            
        # Verifica se o processo está em execução para evitar possíveis compilações incorretas.
        if not has_nvda:
            try:
                output = subprocess.check_output('tasklist /FI "IMAGENAME eq nvda.exe"', text=True)
                if "nvda.exe" in output.lower():
                    has_nvda = True
            except Exception:
                pass
                
        if not has_nvda:
            raise Exception("NVDA não detectado no sistema!\n\nA configuração 'Leitor de Telas Nativo' requer que o NVDA esteja instalado fisicamente ou em execução.\nPor favor, instale o NVDA ou escolha a Configuração do Desenvolvedor (Opção 1).")
            
        self.log("[green]Pré-requisito confirmado: NVDA detectado com sucesso.[/green]")

    # Realiza a instalação das dependências do ambiente caso necessário.
    def install_windows_package(self, package_name, winget_id, choco_id):
        if shutil.which("winget"):
            self.run_command(["winget", "install", winget_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"])
        elif shutil.which("choco"):
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])
        else:
            self.log("[yellow]Gerenciador de pacotes não encontrado. Instalando Chocolatey...[/yellow]")
            choco_cmd = 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))'
            self.run_command(["powershell", "-Command", choco_cmd])
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])

    # Verificação de dependências do ambiente.
    def install_dependencies(self):
        self.log("[yellow]Verificando dependências no sistema Windows.[/yellow]")
        if not shutil.which("git"):
            self.log("[yellow]Instalando Git. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("Git", "Git.Git", "git")
        if not shutil.which("emacs"):
            self.log("[yellow]Instalando GNU Emacs. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("GNU Emacs", "GNU.Emacs", "emacs")

    # Carregamento das configurações de voz nativa do usuário.
    def setup_emacspeak(self, use_native):
        self.log("[yellow]Extraindo e configurando o servidor de áudio da aplicação.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        os.makedirs(emacs_dir, exist_ok=True)

        # Instalação do Emacspeak para as configurações de desenvolvedor.
        if not os.path.exists(emacspeak_dir):
            self.log("[yellow]Baixando repositório oficial do Emacspeak. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                self.log("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório...[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                raise Exception("Falha de conexão ao baixar o Emacspeak.")
            
            self.generate_emacspeak_loaddefs(emacspeak_dir)
        
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")

        # Carregamento da biblioteca de uso do NVDA para as configurações nativas de usuário.
        if use_native:
            is_64bit = platform.architecture()[0] == '64bit'
            dll_name = "nvdaControllerClient64.dll" if is_64bit else "nvdaControllerClient32.dll"
            files_to_copy = ["connect_a11y.exe", dll_name]
            server_executable = "connect_a11y.exe"
        else:

            # Carregamento do servidor de voz para as configurações de desenvolvedor.
            files_to_copy = ["SharpWin.exe"]
            server_executable = "SharpWin.exe"
            
        # Injeta o arquivo de acessibilidade de acordo com o ambiente do usuário.
        self.inject_accessibility_el("Windows", use_native)
            
        for file_name in files_to_copy:
            source = os.path.join(base_path, file_name)
            dest = os.path.join(emacs_dir, file_name)
            try:
                if os.path.exists(source):
                    shutil.copy2(source, dest)
                else:
                    self.log(f"[red]Aviso: O arquivo {file_name} não foi encontrado no pacote.[/red]")
            except Exception as e:
                self.log(f"[bold red]Erro ao copiar {file_name}:[/bold red] {e}")

        server_elisp_path = os.path.join(emacs_dir, server_executable).replace("\\", "/")
        self.inject_init_el(
            server_name=server_elisp_path,
            extra_elisp="(setq explicit-shell-file-name \"powershell.exe\")"
        )


# ---------------------------------------------------------
# >> Módulo Linux (Debian/Ubuntu)
# ---------------------------------------------------------
# Módulo direcionado para instalação e configuração do ambiente para usuários Linux.
class LinuxInstaller(BaseInstaller):

    def check_native_prerequisites(self):
        self.log("[yellow]Verificando pré-requisitos do ambiente nativo (eSpeak NG)...[/yellow]")
        
        # Verifica se o binário do espeak ou espeak-ng existe no sistema Linux.
        has_espeak = shutil.which("espeak") or shutil.which("espeak-ng")
        
        if not has_espeak:
            raise Exception("Sintetizador nativo (eSpeak / eSpeak NG) não detectado no sistema!\n\nA configuração 'Leitor de Telas Nativo' requer que o ambiente de acessibilidade do Linux já esteja instalado e funcional.\nInstale o eSpeak NG antes de prosseguir.")
            
        self.log("[green]Pré-requisito confirmado: eSpeak / eSpeak-NG detectado com sucesso.[/green]")

    # Instalação de dependências do ambiente.
    def install_dependencies(self):
        self.log("[cyan]Sistema Debian ou Ubuntu detectado. Verificando dependências.[/cyan]")
        pacotes = ["emacs", "git", "tcl", "tclx", "espeak-ng", "make", "g++"]
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        
        self.log("[yellow]Atualizando repositórios de sistema silenciosamente.[/yellow]")
        self.run_command(["sudo", "apt-get", "update", "-qq"])
        
        self.log("[yellow]Instalando pacotes base. Esse processo é silencioso.[/yellow]")
        self.run_command(["sudo", "-E", "apt-get", "install", "-y", "-qq"] + pacotes, env=env)

    # Carregamento do Emacspeak para as configurações de usuário.
    def setup_emacspeak(self, use_native):
        self.log("[yellow]Configurando Emacspeak e compilando integração nativa.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")

        if not os.path.exists(emacspeak_dir):
            self.log("[yellow]Baixando repositório oficial. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                self.log("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório...[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                raise Exception("Falha de conexão ao baixar o Emacspeak.")

            self.log("[yellow]Gerando arquivos base de configuração (make config).[/yellow]")
            self.run_command(["make", "config", "-s"], cwd=emacspeak_dir)

        # Compilação do servidor de voz do usuário.
        self.log("[yellow]Compilando servidor de áudio internamente.[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        self.run_command(["make", "-s"], cwd=make_dir)
        self.log("[green]Servidor de áudio compilado com sucesso.[/green]")

        # Injeção do arquivo de acessibilidade do programa (init-a11y.el).
        self.inject_accessibility_el("Linux", use_native)
        self.inject_init_el(server_name="espeak")


# ---------------------------------------------------------
# >> Controlador Principal da Instalação
# ---------------------------------------------------------
# Definição base das instalações do ambiente.
def processo_background(use_native, app_gui):
    """Executa as rotinas de instalação em uma Thread secundária."""
    try:
        os_name = platform.system()
        installer = None

        # Analise do sistema opreacional do usuário Windows (10/11) ou Linux (Ubuntu/Debian)
        if os_name == "Windows":
            installer = WindowsInstaller(logger_func=app_gui.safe_log)
        elif os_name == "Linux":
            if shutil.which("apt-get") is None:
                raise Exception("Este script suporta apenas distribuições baseadas em Debian ou Ubuntu.")
            installer = LinuxInstaller(logger_func=app_gui.safe_log)
        else:
            raise Exception("Sistema operacional não suportado pelo instalador.")

        # Validação de pré-requisitos nativos do usuário.
        if use_native:
            installer.check_native_prerequisites()

        # Inicia a sequência de instalação.
        installer.install_dependencies()
        installer.setup_emacspeak(use_native)
        
        # Avisa a interface que o processo concluiu.
        app_gui.root.after(0, app_gui.finalizar_sucesso)

    except Exception as e:
        app_gui.safe_log(f"[bold red]Processo interrompido.[/bold red]")
        app_gui.root.after(0, lambda: app_gui.finalizar_erro(str(e)))


# ---------------------------------------------------------
# >> Execução Principal (Interface visual e Compilação normal)
# ---------------------------------------------------------
if __name__ == "__main__":
    # Bloco de execução em ambiente do CI.
    if os.environ.get("CI_AUTO_INSTALL"):
        escolha = os.environ.get("CI_AUTO_INSTALL")
        use_native = (escolha == "2")
        
        # Cria um "Dublê" (Mock) da interface visual para imprimir os logs no terminal.
        class HeadlessGUI:
            def safe_log(self, text):
                print(text) # Apenas imprime o log no console do CI.
            def finalizar_sucesso(self):
                print("Instalação Headless concluída com sucesso.")
            def finalizar_erro(self, erro_msg):
                print(f"Erro Crítico Headless: {erro_msg}")
                sys.exit(1)

            class MockRoot:
                def after(self, delay, func):
                    func()
            root = MockRoot()

        # Roda o processo diretamente, sem thread e sem tkinter.
        print(f"--- Iniciando Instalador em Modo Headless (Opção {escolha}) ---")
        processo_background(use_native, HeadlessGUI())
        sys.exit(0)

    # Inicializa o framework de interface da biblioteca Tkinker.
    root = tk.Tk()
    
    # função chamada pela interface gráfica quando o usuário fizer uma escolha.
    def iniciar_thread_instalacao(use_native):
        threading.Thread(
            target=processo_background, 
            args=(use_native, app), 
            daemon=True
        ).start()

    # Cria a janela principal da interface visual.
    app = InstallerGUI(root, callback_iniciar=iniciar_thread_instalacao)
    
    # Mantém o programa rodando capturando as interações da tela.
    root.mainloop()