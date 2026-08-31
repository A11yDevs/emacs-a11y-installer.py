# 📦 Dependências Binárias e Drivers de Acessibilidade

Este documento detalha a arquitetura dos arquivos binários externos (`nvdaControllerClient32.dll`, `nvdaControllerClient64.dll` e `SharpWin.exe`) integrados no ecossistema do instalador do Emacs Acessível.

---

## 🎯 Visão Geral

O ecossistema do Emacspeak requer um servidor de áudio (Text-to-Speech) ou uma ponte de comunicação interprocessos (IPC) para traduzir os comandos textuais gerados pelo Emacs em síntese de voz auditable no sistema operacional Windows. Como o Windows possui diferentes arquiteturas de leitores de tela e ambientes de desenvolvimento, o projeto gerencia dois caminhos de áudio distintos através de binários externos de terceiros e de compilação própria:

1. **Opção Nativa (NVDA):** Utiliza as APIs oficiais de controle do leitor de tela NVDA por meio de chamadas dinâmicas a DLLs em C/C++.
2. **Opção de Desenvolvedor (SharpWin):** Utiliza um servidor de áudio standalone em C# compatível com a SAPI (Speech API) do Windows.

---

## 📄 Descrição dos Binários

### 1. `nvdaControllerClient32.dll` & `nvdaControllerClient64.dll`
* **O que são:** São as bibliotecas dinâmicas oficiais (*Dynamic Link Libraries*) fornecidas pelo projeto NV Access para desenvolvedores interagirem com o leitor de telas NVDA em execução no Windows.

* **Função no Projeto:** Permitem que o script compilado `connect_a11y.exe` realize chamadas nativas (via `ctypes` em Python) para as funções exportadas pelo NVDA, tais como:
  * `nvdaController_speakText()`: Envia strings de texto para serem sintetizadas pelo leitor.
  * `nvdaController_cancelSpeech()`: Interrompe imediatamente a fala em curso (comando de silenciamento correspondente à tecla `s` do Emacspeak).
  * `nvdaController_testIfRunning()`: Verifica se o NVDA está ativo na sessão antes de estabelecer o canal de comunicação.

* **Separador de Arquitetura:** O instalador detecta automaticamente se o sistema operacional hospedeiro é de 32 bits ou 64 bits (`sys.maxsize > 2**32`) e injeta condicionalmente a DLL correspondente no diretório de configuração do usuário (`~/.emacs.d/`), evitando falhas de segmento ou incompatibilidade de ponteiros (*DLL Hell*).

### 2. `SharpWin.exe`
* **O que são:** Um servidor de áudio leve desenvolvido em C# voltado para a interface SAPI (Speech API) do Windows.

* **Função no Projeto:** Atua como o servidor de TTS padrão quando o usuário opta pela **"Configuração do Desenvolvedor"**.

* **Por que utilizá-lo:** Diferente do modo nativo (que exige que o usuário tenha o leitor NVDA instalado e rodando em segundo plano), o `SharpWin.exe` utiliza as vozes sintéticas nativas do sistema operacional (como o SAPI ou as vozes locais do Windows SAPI/Desktop) de forma isolada e autônoma. Ele se comunica diretamente com o Emacspeak sem depender de softwares de acessibilidade de terceiros abertos na máquina.