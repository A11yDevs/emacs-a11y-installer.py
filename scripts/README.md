# `build.py`

Documentação do arquivo de teste da arquitetura e ambiente do projeto `emacs-a11y-installer.py` 

Arquivo:

```text
scripts/build.py
```

## Objetivo

O conteúdo de `scripts/build.py` resume-se como um pipeline de build e teste do instalador para Windows.

O fluxo descrito no arquivo é:

```text
Checkout
   ↓
Python 3.11
   ↓
Instala PyInstaller + Rich
   ↓
Baixa SharpWin.exe
   ↓
Executa scripts/build.py
   ↓
Executa dist/installer-a11y.exe
   ↓
Valida ~/.emacs.d
```

### Executando o Script de Build Localmente

O arquivo `scripts/build.py` serve para testar a compilação em uma máquina própria antes do envio de qualquer "coisa" para o GitHub.

**Pré-requisitos na sua máquina:**
Como o GitHub Actions vai baixar o `SharpWin.exe` automaticamente na nuvem, para rodar esse script no seu computador, é necessário garantir que a pasta `bin/` já exista na raiz do projeto e contenha o `SharpWin.exe` e as duas `.dll` do NVDA.

**Como executar:**

1. Via terminal (PowerShell, CMD ou terminal do VS Code).
2. Certifique-se de estar na pasta raiz do projeto (emacs-installer-a11y.py/scripts).
3. Instale as dependências (se ausentes):
```bash
pip install pyinstaller rich

```

4. Execute o script:
```bash
python scripts/build.py

```

## Estrutura

O arquivo define:

```yaml
name: Testes E2E - Instalador A11y
```

e contém uma seção:

```yaml
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
```

Também define o job:

```yaml
jobs:
  build-and-test:
```

com executor:

```yaml
runs-on: windows-latest
```

e uma matriz:

```yaml
matrix:
  user_choice: [1, 2]
```

## Conteúdo do pipeline

### Checkout

```yaml
- name: Checkout do Repositório
  uses: actions/checkout@v4
```

Obtém o código-fonte do repositório no runner.

### Python

```yaml
- name: Configurar Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
```

Define Python 3.11.

### Dependências

```powershell
python -m pip install --upgrade pip
pip install pyinstaller rich
```

Essas dependências são necessárias para o processo de empacotamento e para o programa Python.

### SharpWin

O arquivo cria a pasta:

```text
bin
```

e baixa:

```text
bin\SharpWin.exe
```

usando a release:

```text
deps-v1
```

Isso prepara o recurso externo utilizado no modo de configuração do desenvolvedor.

### Build do executável

A etapa seguinte chama:

```powershell
python scripts/build.py
```

O objetivo esperado é construir:

```text
dist\installer-a11y.exe
```

### Execução automatizada

Depois do build, o arquivo tenta alimentar o executável com a opção da matriz:

```powershell
Write-Output "${{ matrix.user_choice }}`n`n" | .\dist\installer-a11y.exe
```

Assim, as duas configurações são testadas automaticamente.

## Validação da instalação

O arquivo verifica primeiro os arquivos comuns:

```text
%USERPROFILE%\.emacs.d\init.el
%USERPROFILE%\.emacs.d\emacspeak\
```

Depois valida arquivos específicos de cada opção.

### Configuração do desenvolvedor

Exige:

```text
%USERPROFILE%\.emacs.d\lisp\init-accessibility.el
%USERPROFILE%\.emacs.d\SharpWin.exe
```

### Leitor nativo

Exige:

```text
%USERPROFILE%\.emacs.d\nvda_server.exe
```

e pelo menos uma DLL:

```text
%USERPROFILE%\.emacs.d\nvdaControllerClient32.dll
%USERPROFILE%\.emacs.d\nvdaControllerClient64.dll
```

## Resumo

O `build.yml` representa uma verificação de construção + teste que:

```text
1. prepara Windows
2. instala Python 3.11
3. instala PyInstaller e Rich
4. obtém SharpWin.exe
5. chama scripts/build.py
6. executa installer-a11y.exe
7. testa as opções 1 e 2
8. valida os arquivos do Emacs/Emacspeak
```
