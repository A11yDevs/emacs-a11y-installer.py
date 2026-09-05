# Executável Python destinado a automatizar a instalação e a configuração básica de um ambiente acessível baseado em **GNU Emacs + Emacspeak**.

## Visão geral

O projeto fornece um instalador que identifica o sistema operacional, instala dependências, obtém e configura o Emacspeak e cria os arquivos de configuração necessários para iniciar o ambiente audível.

O fluxo principal está concentrado em `src/installer_a11y.py`. O programa apresenta duas opções de configuração:

1. **Configuração do Desenvolvedor**
   - Windows: utiliza `SharpWin.exe` como servidor de voz.
   - Gera `~/.emacs.d/lisp/init-accessibility.el`.
   - Configura voz, idioma, limpeza de processos do Emacspeak e alternância entre português e inglês.
2. **Leitor de Telas Nativo**
   - Windows: utiliza `connect_a11y.exe` e a DLL correspondente do NVDA Controller Client.
   - Linux: utiliza o servidor nativo do Emacspeak com eSpeak NG.

A escolha é feita pelo usuário no início da execução (através de uma interface gráfica Tkinter) e determina o restante do processo, que roda em uma thread secundária.

## Fluxo de execução

```text
Início
  │
  ├─ Exibe a Interface Gráfica (Tkinter) com opções 1 e 2
  │
  ├─ Recebe a escolha e inicia rotina em background (Thread)
  │
  ├─ Detecta o sistema operacional
  │    ├─ Windows → WindowsInstaller
  │    └─ Linux   → LinuxInstaller
  │
  ├─ Instala dependências (via winget, choco ou apt-get)
  │
  ├─ Configura o Emacspeak (Clona repositório e compila se necessário)
  │
  ├─ Injeta ~/.emacs.d/lisp/init-accessibility.el
  │
  ├─ Cria ~/.emacs.d/init.el
  │
  └─ Finaliza informando via Interface que o ambiente está pronto

```

O código rejeita sistemas operacionais diferentes de Windows e Linux. No Linux, a implementação exige uma distribuição baseada em Debian ou Ubuntu, pois verifica a existência de `apt-get`.

## Estrutura do repositório

```text
emacs-a11y-installer.py/
├── .github/
│   └── workflows/
│       ├── README_github_workflows.md
│       └── e2e-tests.yml
├── bin/
├── src/
│   ├── README_src.md
│   ├── installer_a11y.py
│   ├── interface_a11y.py
│   ├── connect_a11y.py
│   ├── init-a11y-windows-native.el
│   ├── init-a11y-windows-dev.el
│   ├── init-a11y-linux-native.el
│   └── init-a11y-linux-dev.el
├── scripts/
│   ├── README_scripts.md
│   ├── build.py
│   └── benchmark.py
├── .gitattributes
├── .gitignore
├── LICENSE
└── README.md

```

## Componentes principais

### `src/installer_a11y.py`

É o controlador principal (Orquestrador) do instalador.

O arquivo contém:

* `BaseInstaller`: funções comuns de execução de comandos (subprocessos ocultos) e geração de configurações.
* `WindowsInstaller`: instalação das dependências do Windows e configuração do Emacspeak.
* `LinuxInstaller`: instalação das dependências Debian/Ubuntu e compilação do servidor nativo do Emacspeak.
* `processo_background()`: função que isola a execução da instalação em uma Thread.
* bloco `if __name__ == "__main__"`: fluxo inicial que suporta tanto interface interativa Tkinter quanto modo de testes autônomo (Headless).

### `src/interface_a11y.py`

Camada de apresentação desenvolvida em `tkinter`.
A interface impede travamentos visuais, expondo botões de acessibilidade imediata e uma caixa de texto segura (`scrolledtext`) atualizada assincronamente a partir da thread principal.

### `src/connect_a11y.py`

Implementa um *middleware* IPC que conecta o Emacspeak ao NVDA no Windows de forma nativa e de baixa latência.

O programa:

1. Detecta o ambiente, e se acionado pelo GitHub Actions (`CI_MOCK_NVDA=1`), usa o `MockNVDADriver` silencioso.
2. Em uso real, seleciona `nvdaControllerClient32.dll` ou `nvdaControllerClient64.dll` baseado na arquitetura (`sys.maxsize > 2**32`).
3. Carrega a DLL dinamicamente com `ctypes.windll.LoadLibrary`.
4. Verifica se o NVDA está em execução fisicamente.
5. Em loop, lê a entrada recebida em `stdin`.
6. Repassa falas ou cancela falas chamando métodos diretos em C++.

### `src/init-a11y-*.el`

Cargas úteis em Lisp. São arquivos específicos de injeção que determinam como o Emacs deve se comportar perante as vozes, taxas de áudio, limpezas de zumbis de processos IPC (usando `process-query-on-exit-flag`) e alternâncias entre os idiomas. O Emacs atende ao suporte para aplicações textuais, execução de comandos e projetos baseados em ferramentas mecatrônicas.

## Configuração do Windows

No Windows, o instalador verifica primeiro a existência de `winget`. Caso ele esteja disponível, utiliza-o para instalar:

* Git;
* GNU Emacs.

Se `winget` não estiver disponível, tenta utilizar Chocolatey. Caso nenhum dos dois esteja disponível, o instalador tenta instalar o Chocolatey silenciosamente via PowerShell e, em seguida, instala as dependências.

Depois disso, o instalador obtém o repositório do Emacspeak em:

```text
~/.emacs.d/emacspeak

```

Na configuração do desenvolvedor, o executável `SharpWin.exe` é copiado para:

```text
~/.emacs.d/SharpWin.exe

```

Na configuração nativa, são utilizados:

```text
~/.emacs.d/connect_a11y.exe
~/.emacs.d/nvdaControllerClient32.dll
ou
~/.emacs.d/nvdaControllerClient64.dll

```

O arquivo final `init.el` é criado e o payload selecionado em `init-a11y-*.el` é injetado como `init-accessibility.el`.

## Configuração do Linux

O suporte Linux atualmente é direcionado a sistemas Debian/Ubuntu.

O instalador utiliza `apt-get` silenciosamente para instalar:

```text
emacs
git
tcl
tclx
espeak-ng
make
g++

```

Depois clona o Emacspeak, executa:

```bash
make config

```

e compila o servidor:

```text
~/.emacs.d/emacspeak/servers/native-espeak

```

Por fim, copia o payload `.el` correspondente (Dev ou Nativo) e gera o `init.el` com `espeak` como servidor de voz.

## Geração de `emacspeak-loaddefs.el`

Quando o Emacspeak é clonado no Windows, o instalador tenta localizar o GNU Emacs no sistema.

Em seguida, cria temporariamente:

```text
build-loaddefs.el

```

Esse script Lisp é executado pelo Emacs em modo batch para gerar:

```text
lisp/emacspeak-loaddefs.el

```

Depois da geração, o arquivo temporário é removido. Isso permite que o próprio Emacs construa as referências corretas.

## Arquivos gerados

Ao final da instalação, a estrutura principal esperada em `~/.emacs.d` é semelhante a:

```text
.emacs.d/
├── init.el
├── emacspeak/
├── lisp/
│   └── init-accessibility.el    # O arquivo Lisp injetado de acordo com a opção escolhida
├── SharpWin.exe                 # Windows + configuração do desenvolvedor
├── connect_a11y.exe             # Windows + configuração nativa
└── nvdaControllerClient*.dll    # Windows + configuração nativa

```

## Configurações de Acessibilidade (Arquivos Lisp)

O instalador insere `init-accessibility.el` que padroniza o ambiente, ajustando (variando entre ambientes):

* desativação de ícones auditivos do Emacspeak;
* eco de linha e atraso (0.1) de eco de teclas;
* desativação do beep visual (`ring-bell-function`);
* hooks como anúncio de "Arquivo salvo" após ações.
* `my/emacspeak-cleanup` (Limpeza de processos zumbis ao fechar).
* Vozes: Configuração do SAPI (`Microsoft Maria/Zira`) para Windows Dev, ou chamadas diretas ao `eSpeak` para Linux/Nativo.
* Alternância de idioma instantânea no atalho `C-c t`.

## Tratamento de erros

Os comandos externos são executados ocultamente. Quando uma etapa falha, o instalador:

1. aborta e captura a exceção (`subprocess.CalledProcessError`);
2. sinaliza o erro via método assíncripto `app_gui.finalizar_erro()` para a GUI Tkinter, garantindo legibilidade ao leitor de telas.
3. permite retomada caso o usuário queira.

## Testes de implementação (scripts)

Além do núcleo, existem automações para engenharia de release:

* **`scripts/build.py`**: Empacota estaticamente o programa (`PyInstaller`), integrando as dependências `DLL`, os executáveis auxiliares C# e os scripts `Lisp`, para gerar um único `installer_a11y.exe`.
* **`scripts/benchmark.py`**: Script de *profiling*. Envia fuzzings pesados nos buffers dos executáveis IPC do projeto, disparando milhares de requisições de áudio e coletando métricas sistêmicas de CPU, Pico de RAM e Latência (ms) via `psutil`.

## Integração contínua (CI)

O projeto possui um workflow robusto e integrado de testes em:

```text
.github/workflows/e2e-tests.yml

```

Esse workflow independente:

* roda em `windows-latest` usando Python 3.11;
* afere o impacto na memória (Benchmark comparativo) com telemetria avançada;
* compila estaticamente (Build Pipeline);
* testa automaticamente a instalação injetando as varíaveis `CI_AUTO_INSTALL` e o Mock de áudio `CI_MOCK_NVDA`;
* audita diretamente as partições via `PowerShell` validando que todos os binários foram injetados perfeitamente nas duas estratégias de matrizes ("Desenvolvedor" e "Nativo").