# 🤖 Diretório `.github/workflows` (Teste do Ambiente Automotizado)

Contém a definição base da infraestrutura como código (IaC) rodando no GitHub Actions. Este pipeline assegura que as novas implementações não corrompam a arquitetura e validam se a compilação ocorre corretamente nas máquinas host da Microsoft.

## 📄 Detalhamento do arquivo

* **`e2e-tests.yml` (Testes de Ambiente)**:
  * O teste ***e2e-tests.yml*** é acionado automaticamente em eventos de *push*, *pull request* ou gatilhos manuais (`workflow_dispatch`) e é executado em instâncias `windows-latest`.
  * **Trabalho `benchmark-performance`**: Realiza o clone do repositório, configura o Python 3.11, baixa dependências C# externas pré-compiladas via requisições REST (ex: `SharpWin.exe`), gera o *build* dinâmico e executa a telemetria do projeto localmente.
  * **Trabalho `test-windows-installation`**: Possui uma estrutura em `matrix` (com os identificadores 1 e 2), forçando o ambiente a testar as duas ramificações lógicas do *software* (Nativo e Desenvolvimento) de forma paralela.
  * Para invocar o instalador em modo estritamente assíncrono e sem interface (Headless), o pipeline popula as variáveis de ambiente `CI_AUTO_INSTALL` e `CI_MOCK_NVDA` antes de rodar o `.exe` recém-gerado.
  * Finaliza rodando um bloco de comandos PowerShell nativos (`Test-Path`) que verificam diretamente o *filesystem* do Windows, assegurando matematicamente que as chaves lógicas (arquivos `.el`, `.dll` e `.exe`) foram alocadas de forma correta na pasta `%USERPROFILE%\.emacs.d`.