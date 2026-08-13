

### Executável Python destinado a automatizar a instalação e a configuração básica de um ambiente acessível baseado em **GNU Emacs + Emacspeak**, com suporte a diferentes servidores de voz.

## Visão geral

O projeto fornece um instalador que identifica o sistema operacional, instala dependências, obtém e configura o Emacspeak e cria os arquivos de configuração necessários para iniciar o ambiente audível.

O fluxo principal está concentrado em `scr/installer-a11y.py`. O programa apresenta duas opções de configuração:

1. **Configuração do Desenvolvedor**
   - Windows: utiliza `SharpWin.exe` como servidor de voz.
   - Gera `~/.emacs.d/lisp/init-accessibility.el`.
   - Configura voz, idioma, limpeza de processos do Emacspeak e alternância entre português e inglês.
2. **Leitor de Telas Nativo**
   - Windows: utiliza `nvda_server.exe` e a DLL correspondente do NVDA Controller Client.
   - Linux: utiliza o servidor nativo do Emacspeak com eSpeak NG.

A escolha é feita pelo usuário no início da execução e determina o restante do processo.

## Fluxo de execução

```text
Início
  │
  ├─ Exibe as opções 1 e 2
  │
  ├─ Recebe a escolha
  │
  ├─ Detecta o sistema operacional
  │    ├─ Windows → WindowsInstaller
  │    └─ Linux   → LinuxInstaller
  │
  ├─ Instala dependências
  │
  ├─ Configura o Emacspeak
  │
  ├─ Cria ~/.emacs.d/init.el
  │
  └─ Finaliza informando que o ambiente está pronto
```

O código rejeita sistemas operacionais diferentes de Windows e Linux. No Linux, a implementação exige uma distribuição baseada em Debian ou Ubuntu, pois verifica a existência de `apt-get`.

## Estrutura do repositório

```text
emacs-a11y-installer.py/
├── .github/
│   └── workflows/
│       ├── README.md
│       └── e2e-tests.yml
├── bin/
├── scr/
│   ├── README.md
│   ├── installer-a11y.py
│   └── nvda_server.py
├── scripts/
│   ├── README.md
│   └── build.yml
├── .gitattributes
├── .gitignore
├── LICENSE
└── README.md
```

## Componentes principais

### `scr/installer-a11y.py`

É o núcleo do instalador.

O arquivo contém:

- `BaseInstaller`: funções comuns de execução de comandos e geração de configurações.
- `WindowsInstaller`: instalação das dependências do Windows e configuração do Emacspeak.
- `LinuxInstaller`: instalação das dependências Debian/Ubuntu e compilação do servidor nativo do Emacspeak.
- `get_installer()`: seleção da implementação adequada ao sistema operacional.
- bloco `if __name__ == "__main__"`: fluxo interativo principal.

### `scr/nvda_server.py`

Implementa um pequeno servidor que conecta o Emacspeak ao NVDA no Windows.

O programa:

1. Detecta se o processo Python é de 32 ou 64 bits.
2. Seleciona `nvdaControllerClient32.dll` ou `nvdaControllerClient64.dll`.
3. Carrega a DLL dinamicamente com `ctypes`.
4. Verifica se o NVDA está em execução.
5. Lê a entrada recebida em `stdin`.
6. Para linhas iniciadas por `q `, envia o texto ao NVDA para síntese de fala.

## Configuração do Windows

No Windows, o instalador verifica primeiro a existência de `winget`. Caso ele esteja disponível, utiliza-o para instalar:

- Git;
- GNU Emacs.

Se `winget` não estiver disponível, tenta utilizar Chocolatey. Caso nenhum dos dois esteja disponível, o instalador tenta instalar o Chocolatey e, em seguida, instala as dependências.

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
~/.emacs.d/nvda_server.exe
~/.emacs.d/nvdaControllerClient32.dll
ou
~/.emacs.d/nvdaControllerClient64.dll
```

O arquivo final `init.el` configura o servidor de voz e carrega o Emacspeak.

## Configuração do Linux

O suporte Linux atualmente é direcionado a sistemas Debian/Ubuntu.

O instalador utiliza `apt-get` para instalar:

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

Por fim, gera o `init.el` com `espeak` como servidor de voz.

## Geração de `emacspeak-loaddefs.el`

Quando o Emacspeak é clonado no Windows, o instalador tenta localizar o GNU Emacs no `PATH` ou em caminhos comuns de instalação.

Em seguida, cria temporariamente:

```text
build-loaddefs.el
```

Esse script Lisp é executado pelo Emacs em modo batch para gerar:

```text
lisp/emacspeak-loaddefs.el
```

Depois da geração, o arquivo temporário `build-loaddefs.el` é removido.

Esse procedimento permite que o próprio Emacs gere o mapa de autoloads do Emacspeak, em vez de depender de um arquivo previamente preparado.

## Arquivos gerados

Ao final da instalação, a estrutura principal esperada em `~/.emacs.d` é semelhante a:

```text
.emacs.d/
├── init.el
├── emacspeak/
├── lisp/
│   └── init-accessibility.el   # somente na configuração do desenvolvedor
├── SharpWin.exe                # Windows + configuração do desenvolvedor
├── nvda_server.exe             # Windows + configuração nativa
└── nvdaControllerClient*.dll   # Windows + configuração nativa
```

## Configuração de acessibilidade do desenvolvedor

Quando a opção 1 é selecionada, `init-accessibility.el` configura, entre outros pontos:

- desativação de ícones auditivos do Emacspeak;
- eco de linha;
- atraso de eco de teclas;
- desativação do beep tradicional;
- anúncio após salvar arquivos;
- limpeza de processos relacionados ao Emacspeak ao fechar o Emacs;
- voz `Microsoft Maria Desktop` para português do Brasil;
- voz `Microsoft Zira Desktop` para inglês;
- taxa de fala configurada em 180;
- alternância de idioma através de `C-c t`.

## Tratamento de erros

Os comandos externos são executados por meio de `subprocess.run(..., check=True, ...)`.

Quando uma etapa falha, o instalador:

1. mostra uma mensagem de erro;
2. exibe a saída retornada pelo comando quando disponível;
3. encerra o processo com código de erro.

No clone do Emacspeak, existe ainda um mecanismo de limpeza do diretório incompleto caso a operação falhe.

## Execução

O código-fonte pode ser executado diretamente com Python:

```bash
python scr/installer-a11y.py
```

Para gerar um executável Windows, o fluxo de CI chama:

```powershell
python scripts/build.py
```

e espera encontrar:

```text
dist/installer-a11y.exe
```

### Observação importante sobre o estado atual do repositório

Na árvore atualmente publicada do repositório, `scripts/` contém `README.md` e `build.yml`, enquanto o workflow `e2e-tests.yml` referencia `scripts/build.py`.

Isso significa que, no estado atualmente visível no branch `main`, existe uma inconsistência entre o workflow e a árvore de arquivos: o pipeline espera um `build.py` que não aparece em `scripts/`.

Essa inconsistência deve ser corrigida antes de considerar o pipeline de build reproduzível.

## Integração contínua

O projeto possui um workflow de testes E2E em:

```text
.github/workflows/e2e-tests.yml
```

Esse workflow:

- roda em `windows-latest`;
- utiliza Python 3.11;
- instala `pyinstaller` e `rich`;
- baixa `SharpWin.exe` de uma release;
- executa `scripts/build.py`;
- executa o instalador gerado;
- testa as duas escolhas de configuração;
- valida os arquivos criados em `~/.emacs.d`.

O arquivo `scripts/build.yml` contém atualmente uma configuração YAML muito semelhante ao workflow E2E, mas por estar fora de `.github/workflows`, ele não é automaticamente tratado pelo GitHub Actions como workflow.
