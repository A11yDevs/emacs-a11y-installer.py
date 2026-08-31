# ⚙️ Diretório `scripts` (Trabalhos de teste e analise de desempenho)

Contém os *scripts* vitais para a engenharia de *tests* e análise de *performance* do software. Esta camada automatiza a compilação cruzada e submete os servidores de áudio a testes de carga rigorosos.

## 📄 Detalhamento dos arquivos

* **`build.py` (Teste de Compilação)**:
  * Realiza uma compilação de duplo estágio através de chamadas ao `PyInstaller` pelo módulo `subprocess`.
  * O primeiro estágio gera um binário autônomo do *bridge* IPC (`connect_a11y.py`), que é então movido para a pasta temporária `bin/`.
  * O segundo estágio realiza o empacotamento do orquestrador principal (`installer_a11y.py`), embutindo explicitamente os binários (usando a flag `--add-binary`) e os arquivos Lisp (usando a flag `--add-data`) diretamente no executável final.

* **`benchmark.py` (Teste de Performance)**:
  * Invoca o servidor de TTS em um processo filho (`subprocess.Popen`) e anexa a biblioteca `psutil` ao PID do processo para coletar métricas a nível de kernel.
  * Executa uma fase inicial de *Fuzzing*, enviando payloads com caracteres de escape, emoticons e Unicode massivo no `stdin` para testar vazamentos de memória (Memory Leaks) e falhas no *encoding*.
  * Dispara uma rotina de estresse com inúmeras chamadas sequenciais para gerar um perfil de consumo, onde calcula a latência média (ms), extrai o consumo de CPU via `cpu_percent()` e mapeia o limite superior de RAM medindo a taxa de `memory_info().rss` em intervalos regulares.