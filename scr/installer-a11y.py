import platform # Biblioteca para detectar o sistema operacional e arquitetura
import sys # Biblioteca para interagir com o interpretador Python
import subprocess # Biblioteca para executar comandos do sistema operacional
import os # Biblioteca para manipulação de arquivos e diretórios
import shutil # Biblioteca para operações de alto nível em arquivos e diretórios
import glob # Biblioteca para correspondência de padrões em nomes de arquivos
from rich.console import Console # Biblioteca para exibir mensagens coloridas e formatadas no terminal

console = Console()

# ---------------------------------------------------------
# >> Classe Base com Funções Auxiliares
# ---------------------------------------------------------
# Classe base que fornece funções auxiliares para instalação e configuração de acessibilidade.
class BaseInstaller:
    def run_command(self, cmd, shell=False, cwd=None, env=None):
        """Executa comandos ocultando o output padrão para não poluir o leitor de telas. 
        Só exibe texto em caso de erro crítico."""
        try:
            # Executa o comando com captura de saída e verificação de erros
            subprocess.run(cmd, check=True, shell=shell, cwd=cwd, env=env, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Ocorreu um erro crítico ao executar a etapa:[/bold red] {' '.join(cmd)}")
            console.print(f"[red]Detalhes do erro:[/red] {e.stderr.strip() if e.stderr else e.stdout.strip()}")
            sys.exit(1)

    # Função para injetar o arquivo de configuração de acessibilidade (init-accessibility.el) no diretório do usuário.
    # Este arquivo contém configurações de voz e acessibilidade para o GNU Emacs/Emacspeak, verifica o sistema operacional e aplica a voz adequada.
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
        (and name (string-match-p "speaker\\|dtk\\|tts\\|sharpwin" name))
        (and buf
             (buffer-live-p buf)
             (string-match-p "speaker\\|dtk\\|tts\\|sharpwin"
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

;; --- Configuração de Idioma Multiplataforma ---
(defun my/emacspeak-apply-language ()
  "Aplica português do Brasil adequando a voz ao sistema."
  (interactive)
  (ignore-errors (dtk-set-language "pt-br"))
  
  ;; Checa se é Windows (SharpWin) ou Linux (eSpeak)
  (if (eq system-type 'windows-nt)
      (ignore-errors (dtk-set-voice "Microsoft Maria Desktop"))
    (ignore-errors (dtk-set-voice "pt")))
    
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
  "Alterna rapidamente entre português e inglês adequando ao sistema."
  (interactive)
  (when (fboundp 'dtk-stop)
    (dtk-stop))
  
  (if (string= my/emacspeak-current-language "pt-br")
      ;; Bloco: Transição para Inglês
      (progn
        (ignore-errors (dtk-set-language "en"))
        (if (eq system-type 'windows-nt)
            (ignore-errors (dtk-set-voice "Microsoft Zira Desktop"))
          (ignore-errors (dtk-set-voice "en")))
        (setq my/emacspeak-current-language "en")
        (run-with-timer
         0.2 nil
         (lambda ()
           (when (fboundp 'dtk-speak)
             (dtk-speak "English mode")))))
             
    ;; Bloco: Transição para Português
    (progn
      (ignore-errors (dtk-set-language "pt-br"))
      (if (eq system-type 'windows-nt)
          (ignore-errors (dtk-set-voice "Microsoft Maria Desktop"))
        (ignore-errors (dtk-set-voice "pt")))
      (setq my/emacspeak-current-language "pt-br")
      (run-with-timer
       0.2 nil
       (lambda ()
         (when (fboundp 'dtk-speak)
           (dtk-speak "Modo português")))))))

(global-set-key (kbd "C-c t") #'my/emacspeak-toggle-language)

(provide 'init-accessibility)
;; init-accessibility.el --- Fim da configuração de acessibilidade ---
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

        # Configuração do desenvolvedor é injetada antes do carregamento do Emacspeak
        dev_config_str = ""
        if use_dev_config:
            dev_config_str = """
;; Carrega as configurações de acessibilidade do desenvolvedor (Não remova)
(load (expand-file-name "lisp/init-accessibility.el" user-emacs-directory))
"""

        elisp_code = f"""
;; Configuração Base do GNU Emacs/Emacspeak
{dev_config_str}
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

;; Otimizações Visuais (Opcional: Descomente para desativar elementos gráficos)
;; (menu-bar-mode -1)
;; (tool-bar-mode -1)
;; (scroll-bar-mode -1)
"""

        try:
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(elisp_code)
            console.print("[green]Arquivo de configuração base injetado com sucesso.[/green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao escrever o arquivo de configuração base:[/bold red] {e}")
            sys.exit(1)

    # Função para gerar o arquivo de mapeamento do Emacspeak usando o próprio GNU Emacs.
    def generate_emacspeak_loaddefs(self, emacspeak_dir):
        """Gera o arquivo de mapeamento do Emacspeak usando o próprio GNU Emacs."""
        console.print("[yellow]Gerando mapa de funções do Emacspeak...[/yellow]")
        lisp_dir = os.path.join(emacspeak_dir, "lisp").replace("\\", "/")
        loaddefs_file = os.path.join(lisp_dir, "emacspeak-loaddefs.el").replace("\\", "/")
        
        build_el = os.path.join(emacspeak_dir, "build-loaddefs.el")
        
        # Verifica se o Emacs está disponível no PATH do sistema
        emacs_cmd = shutil.which("emacs")
        
        # Fallback de busca absoluta caso o Emacs não esteja no PATH atual
        if not emacs_cmd:
            if platform.system() == "Windows":
                possiveis_caminhos = glob.glob(r"C:\Program Files\Emacs\*\bin\emacs.exe") + \
                                     glob.glob(r"C:\Program Files\GNU Emacs\*\bin\emacs.exe") + \
                                     glob.glob(r"C:\Program Files\Emacs\bin\emacs.exe")
            else:
                possiveis_caminhos = ["/usr/bin/emacs", "/usr/local/bin/emacs"]
                # Filtra mantendo apenas os caminhos que realmente existem
                possiveis_caminhos = [p for p in possiveis_caminhos if os.path.exists(p)]
            
            if possiveis_caminhos:
                emacs_cmd = possiveis_caminhos[0]
            else:
                console.print("[bold red]O Emacs foi instalado, mas o instalador não conseguiu localizá-lo para a etapa final.[/bold red]")
                console.print("[yellow]Solução: Feche este terminal, abra um novo (para recarregar o PATH) e rode o instalador novamente.[/yellow]")
                sys.exit(1)
                
        emacs_cmd = emacs_cmd or "emacs"
        
        # Script Lisp temporário para inicialização correta do GNU Emacs 
        elisp_code = f"""
        (require 'autoload)
        (let ((generated-autoload-file "{loaddefs_file}"))
          (if (fboundp 'loaddefs-generate)
              (loaddefs-generate "{lisp_dir}" generated-autoload-file)
            (update-directory-autoloads "{lisp_dir}")))
        """
        
        try:
            # Cria o script temporário
            with open(build_el, "w", encoding="utf-8") as f:
                f.write(elisp_code)
                
            # Executa o Emacs silenciosamente para processar a geração
            self.run_command([emacs_cmd, "--batch", "-l", build_el])
            
            # Limpa o ambiente apagando o script temporário
            if os.path.exists(build_el):
                os.remove(build_el)
                
            console.print("[green]Arquivo emacspeak-loaddefs.el gerado com sucesso.[/green]")
        except Exception as e:
            console.print(f"[bold red]Erro ao gerar os loaddefs do Emacspeak:[/bold red] {e}")
            sys.exit(1)


# ---------------------------------------------------------
# >> Módulo Windows (10/11)
# ---------------------------------------------------------
# Módulo específico para sistemas Windows, garantindo a instalação de dependências essenciais e configuração do Emacspeak.
class WindowsInstaller(BaseInstaller):
    # Verifica e instala pacotes usando winget ou chocolatey, dependendo da disponibilidade.
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

    # Instala dependências essenciais no Windows, como Git e GNU Emacs.
    def install_dependencies(self):
        console.print("[yellow]Verificando dependências no sistema Windows.[/yellow]")
        if not shutil.which("git"):
            console.print("[yellow]Instalando Git. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("Git", "Git.Git", "git")
        if not shutil.which("emacs"):
            console.print("[yellow]Instalando GNU Emacs. Esse processo pode demorar um pouco.[/yellow]")
            self.install_windows_package("GNU Emacs", "GNU.Emacs", "emacs")

    # Configura o Emacspeak no Windows, incluindo a clonagem do repositório e a configuração do servidor de áudio.    
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Extraindo e configurando o servidor de áudio da aplicação.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")
        os.makedirs(emacs_dir, exist_ok=True)
        
        # Clonagem do repositório do Emacspeak com sistema de rollback em caso de falha de rede
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial do Emacspeak. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                console.print("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório para evitar corrupção.[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                sys.exit(1)
            
            # Geração do arquivo loaddefs
            self.generate_emacspeak_loaddefs(emacspeak_dir)
        
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
        
        if use_native:
            # Verifica a arquitetura do sistema do usuário
            is_64bit = platform.architecture()[0] == '64bit'
            dll_name = "nvdaControllerClient64.dll" if is_64bit else "nvdaControllerClient32.dll"

            # Configuração de voz via NVDA Controller Client
            files_to_copy = ["nvda_server.exe", dll_name]
            server_executable = "nvda_server.exe"
        else:
            # Configuração de voz do Desenvolvedor (SharpWin)
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
# Módulo específico para sistemas Linux baseados em Debian ou Ubuntu, garantindo a instalação de dependências essenciais e configuração do Emacspeak.
class LinuxInstaller(BaseInstaller):
    def install_dependencies(self):
        # Verifica as dependências primárias e instala pacotes essenciais no Linux (Debian/Ubuntu).
        console.print("[cyan]Sistema Debian ou Ubuntu detectado. Verificando dependências.[/cyan]")
        pacotes = ["emacs", "git", "tcl", "tclx", "espeak-ng", "make", "g++"]
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        
        console.print("[yellow]Atualizando repositórios de sistema silenciosamente.[/yellow]")
        self.run_command(["sudo", "apt-get", "update", "-qq"])
        
        console.print("[yellow]Instalando pacotes base. Esse processo é silencioso.[/yellow]")
        self.run_command(["sudo", "-E", "apt-get", "install", "-y", "-qq"] + pacotes, env=env)

    # Configura o Emacspeak no Linux, incluindo a clonagem do repositório, compilação do servidor de áudio e configuração do arquivo init.el.    
    def setup_emacspeak(self, use_native):
        console.print("[yellow]Configurando Emacspeak e compilando integração nativa.[/yellow]")
        emacs_dir = os.path.expanduser("~/.emacs.d")
        emacspeak_dir = os.path.join(emacs_dir, "emacspeak")

        # Clonagem do repositório do Emacspeak com sistema de rollback em caso de falha de rede
        if not os.path.exists(emacspeak_dir):
            console.print("[yellow]Baixando repositório oficial. Aguarde.[/yellow]")
            try:
                subprocess.run(["git", "clone", "-q", "https://github.com/tvraman/emacspeak.git", emacspeak_dir], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                console.print("[bold red]Erro de conectividade ao clonar o repositório. Limpando diretório para evitar corrupção.[/bold red]")
                if os.path.exists(emacspeak_dir):
                    shutil.rmtree(emacspeak_dir, ignore_errors=True)
                sys.exit(1)

            # Geração de arquivos base via Make
            console.print("[yellow]Gerando arquivos base de configuração (make config).[/yellow]")
            self.run_command(["make", "config", "-s"], cwd=emacspeak_dir)

        # Configuração de voz via eSpeak NG   
        console.print("[yellow]Compilando servidor de áudio internamente.[/yellow]")
        make_dir = os.path.join(emacspeak_dir, "servers", "native-espeak")
        self.run_command(["make", "-s"], cwd=make_dir)
        console.print("[green]Servidor de áudio compilado com sucesso.[/green]")

        # Configuração de voz do Desenvolvedor (SharpWin)
        if not use_native:
            self.inject_accessibility_el()
            
        self.inject_init_el(server_name="espeak", use_dev_config=(not use_native))


# ---------------------------------------------------------
# >> Análise de Ambiente
# ---------------------------------------------------------
# Verifica o sistema operacional e retorna a classe de instalação apropriada.
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
# Roda o instalador principal, guiando o usuário na configuração do ambiente de acessibilidade.
if __name__ == "__main__":
    console.print("[bold cyan]Iniciando instalação do ambiente de acessibilidade audível - A11yDevs.[/bold cyan]\n")
    
    console.print("[bold]Selecione a configuração de acessibilidade de sua preferência:[/bold]")
    console.print("  [1] Configuração do Desenvolvedor (Arquivo de acessibilidade)")
    console.print("  [2] Leitor de Telas Nativo (Windows: NVDA | Linux: eSpeak )")
    
    escolha = ""
    while escolha not in ["1", "2"]:
        escolha = input("\nDigite 1 ou 2 para selecionar: ").strip()
        
    use_native = (escolha == "2")
    
    installer = get_installer()
    installer.install_dependencies()
    installer.setup_emacspeak(use_native)

    # Input final para manter o terminal aberto após a conclusão da instalação
    console.print("\n[bold green]Todas as etapas foram concluídas com sucesso. O ambiente está pronto para uso.[/bold green]")
    input("\nPressione a tecla Enter para finalizar e fechar o instalador.")