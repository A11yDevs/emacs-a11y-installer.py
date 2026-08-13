# README - `e2e-tests.yml`

Documentação do workflow de testes end-to-end do projeto `emacs-a11y-installer.py`.

Arquivo:

```text
.github/workflows/e2e-tests.yml
```

## Objetivo

O workflow verifica, em um ambiente Windows fornecido pelo GitHub Actions, se o executável do instalador consegue ser construído, executado e utilizado para produzir a estrutura básica esperada do Emacs/Emacspeak.

Além de verificar a configuração comum, o pipeline executa o instalador duas vezes por meio de uma matriz:

```yaml
user_choice: [1, 2]
```

onde:

| Opção | Configuração |
|---|---|
| `1` | Configuração do Desenvolvedor |
| `2` | Leitor de Telas Nativo |

## Quando o workflow é executado

O workflow é acionado em:

```yaml
push:
  branches: [ "main" ]

pull_request:
  branches: [ "main" ]
```

Portanto, ele é executado quando há:

- push para `main`;
- pull request direcionado a `main`.

## Ambiente

O job é executado em:

```yaml
runs-on: windows-latest
```

A versão do Python é fixada em:

```text
Python 3.11
```

Isso é importante porque o teste depende de componentes específicos do ambiente Windows e não é uma validação genérica multiplataforma.

## Estratégia de matriz

O workflow define:

```yaml
strategy:
  matrix:
    user_choice: [1, 2]
```

Isso gera duas execuções do mesmo job.

### Execução da opção 1

A entrada simulada é:

```text
1
```

O instalador deve produzir:

```text
%USERPROFILE%\.emacs.d\init.el
%USERPROFILE%\.emacs.d\emacspeak\
%USERPROFILE%\.emacs.d\lisp\init-accessibility.el
%USERPROFILE%\.emacs.d\SharpWin.exe
```

### Execução da opção 2

A entrada simulada é:

```text
2
```

O instalador deve produzir:

```text
%USERPROFILE%\.emacs.d\init.el
%USERPROFILE%\.emacs.d\emacspeak\
%USERPROFILE%\.emacs.d\nvda_server.exe
```

e pelo menos uma das DLLs:

```text
%USERPROFILE%\.emacs.d\nvdaControllerClient32.dll
%USERPROFILE%\.emacs.d\nvdaControllerClient64.dll
```

## Etapas do workflow

### 1. Checkout

```yaml
uses: actions/checkout@v4
```

Baixa o conteúdo do repositório para o runner.

### 2. Configuração do Python

```yaml
uses: actions/setup-python@v5
with:
  python-version: '3.11'
```

Instala e configura o Python 3.11 no ambiente de teste.

### 3. Dependências de build

O pipeline executa:

```powershell
python -m pip install --upgrade pip
pip install pyinstaller rich
```

`PyInstaller` é necessário para gerar o executável, enquanto `rich` é utilizado pelo instalador em `scr/installer-a11y.py`.

### 4. Preparação do `SharpWin.exe`

O workflow cria:

```text
bin/
```

e baixa:

```text
SharpWin.exe
```

a partir da release:

```text
deps-v1
```

A URL utilizada pelo workflow é:

```text
https://github.com/A11yDevs/emacs-a11y-installer/releases/download/deps-v1/SharpWin.exe
```

Esse executável é uma dependência necessária para a configuração do desenvolvedor.

### 5. Build

O workflow executa:

```powershell
python scripts/build.py
```

Depois espera que o resultado esteja em:

```text
dist\installer-a11y.exe
```

## Ponto de atenção do repositório

Na versão atualmente publicada do branch `main`, o diretório `scripts/` apresenta:

```text
README.md
build.yml
```

mas não apresenta `build.py`.

Logo, existe uma dependência quebrada entre o workflow e a árvore atual do repositório:

```text
e2e-tests.yml
      │
      └── chama → scripts/build.py
                       │
                       └── arquivo não presente na árvore atual
```

Enquanto essa inconsistência existir, o workflow não conseguirá concluir a etapa de build.

## 6. Execução do instalador

A seleção do usuário é simulada sem interação manual:

```powershell
Write-Output "${{ matrix.user_choice }}`n`n" | .\dist\installer-a11y.exe
```

Isso envia a opção da matriz para o executável e também fornece os `Enter` necessários para avançar pelo fluxo interativo.

O método permite automatizar um programa que originalmente espera entrada humana.

## 7. Validação comum

Independentemente da opção escolhida, o workflow verifica:

```powershell
Test-Path "$EmacsDir\init.el"
Test-Path "$EmacsDir\emacspeak"
```

Se qualquer um desses caminhos não existir, a execução termina com:

```powershell
exit 1
```

## 8. Validação da opção 1

Para a configuração do desenvolvedor, o workflow exige:

```text
lisp\init-accessibility.el
SharpWin.exe
```

Esses arquivos confirmam que a configuração específica do desenvolvedor foi instalada.

## 9. Validação da opção 2

Para a configuração nativa, o workflow exige:

```text
nvda_server.exe
```

e verifica se pelo menos uma das DLLs do NVDA Controller Client existe:

```powershell
$Dll32 = Test-Path "$EmacsDir\nvdaControllerClient32.dll"
$Dll64 = Test-Path "$EmacsDir\nvdaControllerClient64.dll"
```

A condição de falha é:

```powershell
if (-Not ($Dll32 -or $Dll64)) {
    exit 1
}
```

Ou seja, o teste aceita a DLL correspondente à arquitetura do runner, sem exigir simultaneamente as duas variantes.

## O que este workflow realmente testa

O workflow é um teste de integração do instalador empacotado. Ele confirma principalmente:

- construção do executável;
- execução do executável em Windows;
- aceitação das opções 1 e 2;
- criação de `init.el`;
- obtenção/configuração do Emacspeak;
- presença das dependências específicas de cada modo.

Ele **não** valida profundamente a qualidade da fala, o comportamento completo do Emacspeak, todas as funções Lisp ou a experiência de uso do leitor de tela.

## Relação com o código Python

O comportamento esperado pelo workflow corresponde ao fluxo em `scr/installer-a11y.py`:

```text
entrada do usuário
    ↓
get_installer()
    ↓
install_dependencies()
    ↓
setup_emacspeak(use_native)
    ↓
arquivos em ~/.emacs.d
```

A opção `1` leva à utilização do `SharpWin.exe` no Windows.

A opção `2` leva à utilização de `nvda_server.exe` e da DLL do NVDA Controller Client.

## Resultado esperado

Uma execução bem-sucedida deve terminar sem `exit 1` e apresentar as mensagens de sucesso específicas de cada opção:

```text
Tudo OK com a Opção 1!
```

ou:

```text
Tudo OK com a Opção 2!
```
