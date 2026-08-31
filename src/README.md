# 📂 Diretório `src` (Centro da Aplicação)

Este diretório abriga o código-fonte central do instalador e a infraestrutura de comunicação interprocessos (IPC). Os módulos aqui definidos são responsáveis por orquestrar a configuração do sistema, manipular instâncias da API do Windows nativamente e injetar código Emacs Lisp que gerencia o ciclo de vida dos servidores de TTS (Text-to-Speech). Esta arquitetura garante uma resposta auditiva de baixíssima latência, ideal para a configuração do ambiente Emacs voltado para aplicações baseadas em texto, jogos interativos e execução contínua de comandos.

## 📄 Detalhamento Dos Arquivos

* **`installer_a11y.py` (Controlador / Orquestrador)**:
  * Funciona através de uma classe `BaseInstaller` que injeta o arquivo de configuração `init.el` dinamicamente no sistema do usuário.
  * Este script adiciona *hooks* na inicialização do Emacs, como o `comint-mode-hook`, que define o buffer de comandos como `read-only` e emite ícones auditivos, otimizando interações de terminal.
  * Ele utiliza o comando `emacs --batch` nativo do sistema operacional para rodar rotinas Lisp em background e compilar o arquivo de mapeamento `emacspeak-loaddefs.el`.
  * As subclasses `WindowsInstaller` e `LinuxInstaller` fazem a gestão de dependências invocando gerenciadores de pacotes silenciosamente via `subprocess.run` (como `winget`, `choco` ou `apt-get`).

* **`connect_a11y.py` (Middleware de Comunicação IPC)**:
  * Atua como uma ponte de comunicação direta com a API do leitor de telas, utilizando a biblioteca `ctypes.windll.LoadLibrary` para injetar a DLL do NVDA (`nvdaControllerClient32.dll` ou `nvdaControllerClient64.dll`) no espaço de memória da aplicação.
  * Mantém um *loop* infinito (Thread principal) aguardando o *stream* de dados de `sys.stdin.readline()` enviado pelo processo pai [Emacspeak].
  * Implementa um sistema de *parsing* que intercepta a string, removendo espaços, e aciona chamadas C++ nativas: `q <texto>` aciona `nvdaController_speakText`, e `s` emite uma interrupção via `nvdaController_cancelSpeech`.
  * Inclui uma classe `MockNVDADriver` para absorver os comandos de áudio silenciosamente durante a execução em ambientes de Integração Contínua (ativado pela variável de ambiente `CI_MOCK_NVDA=1`).

* **`interface_a11y.py` (Camada de Apresentação Assíncrona)**:
  * Implementada via `tkinter`, utilizando `threading.Thread` para delegar a execução da instalação a uma *thread* secundária (Daemon), evitando o travamento do *Main Loop* gráfico.
  * Garante a segurança de atualização da UI entre *threads* (Thread-Safety) utilizando o método `self.root.after(0, ...)` para renderizar os logs de forma síncrona.

* **`init-a11y-*.el` (Carga Útil em Emacs Lisp)**:
  * Gerencia o ecossistema interno de subprocessos do Emacs Lisp (função `my/emacspeak-process-p`), interceptando buffers que correspondam a instâncias de áudio como "dtk" ou "espeak".
  * Resolve o problema clássico de processos zumbis ao fechar o editor, iterando sobre o `process-list` e definindo a *flag* `set-process-query-on-exit-flag` como nula, encerrando-os forçadamente no `kill-emacs-hook`.
  * Disponibiliza o *binding* global `C-c t`, permitindo ao usuário alternar a voz do sintetizador e a taxa de leitura (`dtk-speech-rate`) nativamente em tempo de execução.
