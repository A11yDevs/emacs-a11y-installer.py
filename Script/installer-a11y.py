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
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd, env=env, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Ocorreu um erro crítico ao executar a etapa:[/bold red] {' '.join(cmd)}")
            console.print(f"[red]Detalhes do erro:[/red] {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            sys.exit(1)

    def inject_accessibility_el(self):
        """Gera o arquivo de configurações de voz do desenvolvedor (init-accessibility.el)."""
        emacs_dir = os.path.expanduser("~/.emacs.d")
        lisp_dir = os.path.join(emacs_dir, "lisp")
        os.makedirs(lisp_dir, exist_ok=True)
        acc_file = os.path.join(lisp_dir, "init-accessibility.el")
        
        elisp_code = """;; init-accessibility.el --- Voz e Acessibilidade ---

;; --- Configurações Básicas de Áudio e Feedback ---
(setq emacspeak-play-program nil)
(setq emacspeak-use-auditory-icons nil)
(setq emacspeak-line-echo t)
(setq echo-keystrokes 0.1)
(setq ring-bell-function #'ignore)

(defgroup my-accessibility nil
  "Configurações de acessibilidade do usuário."
  :group 'applications)

;; --- Hooks de Sistema e Limpeza de Processos ---
(defun my-speak-saved ()
  "Anuncia que o arquivo foi salvo."
  (message "Arquivo salvo.")
  (when (fboundp 'emacspeak-speak-line)
    (emacspeak-speak-line)))
(add-hook 'after-save-hook #'my-speak-saved)

(defun my/emacspeak-process-p (proc)
  "Retorna t se PROC parecer ser um processo do Emacspeak."
  (let ((name (process-name proc))
        (buf  (process-buffer proc)))
    (or (eq proc (and (boundp 'dtk-speaker-process) dtk-speaker-process))
        (and name (string-match-p "speaker\\\\|dtk\\\\|tts\\\\|sharpwin" name))
        (and buf
             (buffer-live-p buf)
             (string-match-p "speaker\\\\|dtk\\\\|tts\\\\|sharpwin"
                             (buffer-name buf))))))

(defun my/emacspeak-disable-exit-query ()
  "Desativa a pergunta de saída para processos do Emacspeak."
  (dolist (proc (process-list))
    (when (and (process-live-p proc)
               (my/emacspeak-process-p proc))
      (set-process-query-on-exit-flag proc nil))))

(defun my/emacspeak-cleanup ()
  "Desativa query-on-exit e encerra processos do Emacspeak ao fechar."
  (my/emacspeak-disable-exit-query)
  (dolist (proc (process-list))
    (when (and (process-live-p proc)
               (my/emacspeak-process-p proc))
      (ignore-errors
        (delete-process proc)))))

;; --- Configuração de Idioma ---
(defun my/emacspeak-apply-language ()
  "Aplica português do Brasil forçando o nome exato da voz no SAPI."
  (interactive)
  ;; Força a cultura para o .NET (case-sensitive)
  (when (fboundp 'dtk-set-language)
    (dtk-set-language "pt-BR"))
  ;; Envia o comando 'v' para o SharpWin com o nome da voz
  (when (fboundp 'dtk-set-voice)
    (dtk-set-voice "Microsoft Maria Desktop"))
  (setq dtk-speech-rate 180))

;; Inicialização de hooks temporizados para garantir carregamento seguro
(add-hook 'emacs-startup-hook
          (lambda ()
            (run-with-idle-timer 1 nil #'my/emacspeak-disable-exit-query)
            (run-with-idle-timer 2 nil #'my/emacspeak-apply-language)))

(add-hook 'kill-emacs-hook #'my/emacspeak-cleanup)

;; --- Alternância Dinâmica de Idiomas (Atalho) ---
(defvar my/emacspeak-current-language "pt-br"
  "Idioma atual do Emacspeak controlado pelo usuário.")

(defun my/emacspeak-toggle-language ()
  "Alterna rapidamente entre português do Brasil (Maria) e inglês (Zira)."
  (interactive)
  (when (fboundp 'dtk-stop)
    (dtk-stop))
  (condition-case nil
      (if (string= my/emacspeak-current-language "pt-br")
          (progn
            ;; Transição para Inglês
            (dtk-set-language "en-US")
            (dtk-set-voice "Microsoft Zira Desktop")
            (setq my/emacspeak-current-language "en")
            (run-with-timer
             0.2 nil
             (lambda ()
               (when (fboundp 'dtk-speak)
                 (dtk-speak "English mode")))))
        ;; Transição para Português
        (dtk-set-language "pt-BR")
        (dtk-set-voice "Microsoft Maria Desktop")
        (setq my/emacspeak-current-language "pt-br")
        (run-with-timer
         0.2 nil
         (lambda ()
           (when (fboundp 'dtk-speak)
             (dtk-speak "Modo português")))))
    (error
     (when (fboundp 'emacspeak-emergency-tts-restart)
       (emacspeak-emergency-tts-restart)))))

(global-set-key (kbd "C-c t") #'my/emacspeak-toggle-language)

(provide 'init-accessibility)
;; init-accessibility.el --- Fim das configurações de acessibilidade ---
"""
        try:
            with open(acc_file, "w", encoding="utf-8") as f:
                f.write(elisp_code)
        except Exception as e:
            console.print(f"[bold red]Erro ao escrever init-accessibility.el:[/bold red] {e}")
            sys.exit(1)

    def inject_init_el(self, server_name, extra_elisp="", use_dev_config=False):
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
        
        if use_dev_config:
            elisp_code += "\n;; Carregando configurações de acessibilidade do desenvolvedor\n"
            elisp_code += "(add-to-list 'load-path \"~/.emacs.d/lisp\")\n"
            elisp_code += "(require 'init-accessibility)\n"

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
        if shutil.which("winget"):
            self.run_command(["winget", "install", winget_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"])
        elif shutil.which("choco"):
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])
        else:
            console.print("[yellow]Gerenciador de pacotes não encontrado. Instalando Chocolatey em segundo plano...[/yellow]")
            choco_cmd = 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))'
            self.run_command(["powershell", "-Command", choco_cmd])
            self.run_command(["choco", "install", choco_id, "-y", "--limit-output"])

    def install_dependencies(self):
        console.print("[yellow]Verificando dependências no sistema Windows.[/yellow]")
        if not shutil.which("git"):
            console.print("[yellow]Instalando Git. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("Git", "Git.Git", "git")
        if not shutil.which("emacs"):
            console.print("[yellow]Instalando GNU Emacs.Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("GNU Emacs", "GNU.Emacs", "emacs")
        
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Extraindo e configurando o servidor de áudio da aplicação.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        os.makedirs(emacs_dir, exist_ok=True)
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
        
        if use_native:
            # Configuração NVDA Controller Client
            files_to_copy = ["nvda_server.exe", "nvdaControllerClient64.dll"]
            server_executable = "nvda_server.exe"
        else:
            # Configuração do Provedor/Desenvolvedor (SharpWin)
            files_to_copy = ["SharpWin.exe"]
            server_executable = "SharpWin.exe"
            self.inject_accessibility_el()
            
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

        server_elisp_path = os.path.join(emacs_dir, server_executable).replace("\\", "/")
        self.inject_init_el(
            server_name=server_elisp_path,
            extra_elisp="(setq explicit-shell-file-name \"powershell.exe\")",
            use_dev_config=(not use_native)
        )


# ---------------------------------------------------------
# >> Módulo Linux (Debian/Ubuntu)
# ---------------------------------------------------------
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
        
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Configurando Emacspeak e compilando integração nativa.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial. Aguarde.[/yellow]")
            self.run_command(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir])
            
        console.print("[yellow]Compilando servidor de áudio internamente.[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        self.run_command(["make", "-s"], cwd=make_dir)
        console.print("[green]Servidor de áudio compilado com sucesso.[/green]")
        
        if not use_native:
            self.inject_accessibility_el()
            
        self.inject_init_el(server_name="espeak", use_dev_config=(not use_native))


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
    
    console.print("[bold]Selecione a configuração de acessibilidade de sua preferência:[/bold]")
    console.print("  [1] Configuração do Provefor/Desenvolvedor (Vozes customizadas pelo arquivo init-accessibility.el)")
    console.print("  [2] Leitor de Telas Nativo (Windows: NVDA | Linux: eSpeak padrão do sistema)")
    
    escolha = ""
    while escolha not in ["1", "2"]:
        escolha = input("\nDigite 1 ou 2 para selecionar: ").strip()
        
    use_native = (escolha == "2")
    console.print("\n")
    
    installer = get_installer()
    installer.install_dependencies()
    installer.setup_emacspeak(use_native)
    
    console.print("\n[bold green]Todas as etapas foram concluídas com sucesso. O ambiente está pronto para uso.[/bold green]")
    input("\nPressione a tecla Enter para finalizar e fechar o instalador.")
