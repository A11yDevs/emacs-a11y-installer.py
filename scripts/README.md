# `build.yml`

Documentação do arquivo `scripts/build.yml` do projeto `emacs-a11y-installer.py`.

Arquivo:

```text
scripts/build.yml
```

## Objetivo aparente

O conteúdo de `scripts/build.yml` descreve um pipeline de build e teste do instalador para Windows.

Sua estrutura é praticamente a mesma do workflow atualmente localizado em:

```text
.github/workflows/e2e-tests.yml
```

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

## O problema do local do arquivo

O GitHub Actions procura workflows dentro de:

```text
.github/workflows/
```

Entretanto, este arquivo está em:

```text
scripts/build.yml
```

Logo, ele não funciona como workflow ativo apenas por estar no repositório.

Na prática, o workflow reconhecido pelo GitHub é:

```text
.github/workflows/e2e-tests.yml
```

O `build.yml` em `scripts/` é apenas um arquivo YAML armazenado no repositório, a menos que alguma ferramenta externa o leia explicitamente.

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

## Relação com `e2e-tests.yml`

No estado atual do repositório, os dois arquivos descrevem essencialmente o mesmo processo.

| Arquivo | Localização | Reconhecido automaticamente pelo GitHub Actions? | Função |
|---|---|---:|---|
| `e2e-tests.yml` | `.github/workflows/` | Sim | Workflow ativo de CI |
| `build.yml` | `scripts/` | Não | Cópia/descrição de workflow armazenada como YAML |

Isso torna `build.yml` potencialmente redundante.

## Dependência de `scripts/build.py`

Tanto `build.yml` quanto `e2e-tests.yml` chamam:

```powershell
python scripts/build.py
```

Entretanto, a árvore atualmente publicada em `scripts/` não apresenta `build.py`.

A estrutura observada é:

```text
scripts/
├── README.md
└── build.yml
```

Portanto, o arquivo `build.yml` documenta uma etapa que depende de um script que não está presente na árvore atual.

## Consequência prática

Se o workflow ativo seguir exatamente esta configuração, a execução chegará à etapa:

```powershell
python scripts/build.py
```

e falhará caso `build.py` realmente não exista no commit utilizado pelo runner.

Uma documentação correta deve manter essa condição explícita, porque esconder uma dependência ausente só transforma um problema de repositório em uma sessão coletiva de arqueologia digital depois.

## Possíveis formas de organização

A estrutura pode ser normalizada de algumas maneiras:

### Alternativa 1: manter um único workflow

Manter:

```text
.github/workflows/e2e-tests.yml
```

e remover a duplicação de:

```text
scripts/build.yml
```

quando ele não tiver finalidade independente.

### Alternativa 2: transformar `build.yml` em documentação

Se a intenção for documentar o pipeline, o conteúdo pode ser convertido para Markdown em vez de permanecer como YAML fora de `.github/workflows`.

### Alternativa 3: criar o `build.py` esperado

Se o `build.py` foi removido acidentalmente ou está previsto para existir, ele deve ser restaurado em:

```text
scripts/build.py
```

para que o workflow possa executar a etapa definida.

## Resumo

O `build.yml` representa um pipeline de construção + teste que:

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

Porém, atualmente ele está localizado fora do diretório de workflows e, portanto, não é um workflow ativo do GitHub Actions.

Além disso, ele referencia `scripts/build.py`, que não aparece na árvore atual de `scripts/`.
