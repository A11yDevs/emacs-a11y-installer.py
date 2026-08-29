import tkinter as tk
from tkinter import scrolledtext, messagebox
import re

def clean_rich_tags(text):
    """Remove as tags do rich para o leitor de telas ler apenas o texto limpo."""
    return re.sub(r'\[.*?\]', '', text)

class InstallerGUI:
    def __init__(self, root, callback_iniciar):
        self.root = root
        self.callback_iniciar = callback_iniciar # Função externa que é chamada ao clicar no botão de opção.
        
        self.root.title("Instalador - A11yDevs")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        self.lbl_instrucoes = tk.Label(
            root, text="Instalador A11yDevs.\nNavegue com 'TAB' e pressione 'Enter' para escolher.",
            font=("Arial", 12, "bold")
        )
        self.lbl_instrucoes.pack(pady=15)

        # Primeira escolha do usuário -> Configuração de desenvolvedor.
        self.btn_dev = tk.Button(
            root, text="1. Configuração do Desenvolvedor", font=("Arial", 11),
            command=lambda: self.preparar_instalacao(use_native=False)
        )
        self.btn_dev.pack(fill=tk.X, padx=40, pady=5)
        self.btn_dev.bind("<Return>", lambda e: self.btn_dev.invoke())

        # Segunda escolha do usuário -> Configuração de usuário.
        self.btn_native = tk.Button(
            root, text="2. Leitor de Telas Nativo (NVDA/eSpeak)", font=("Arial", 11),
            command=lambda: self.preparar_instalacao(use_native=True)
        )
        self.btn_native.pack(fill=tk.X, padx=40, pady=5)
        self.btn_native.bind("<Return>", lambda e: self.btn_native.invoke())

        self.log_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, height=12, font=("Arial", 10), state=tk.DISABLED
        )
        self.log_area.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)
        self.btn_dev.focus_set()

    def safe_log(self, text):
        """Método seguro para receber textos de outras threads."""
        clean_msg = clean_rich_tags(text)
        self.root.after(0, self._append_log, clean_msg)

    def _append_log(self, text):
        """Atualiza a caixa de texto na interface."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.title(f"Instalador - A11yDevs | Status: {text[:30]}...")

    def preparar_instalacao(self, use_native):
        """Confirma a escolha do usuário, trava os botões e avisa o instalador (backend) para começar."""
        
        # Confirmação interativa de segurança das escolhas do usuário.
        tipo_escolha = "Leitor de Telas Nativo (NVDA/eSpeak)" if use_native else "Configuração do Desenvolvedor"
        confirma = messagebox.askyesno(
            "Confirmação de Ambiente",
            f"Você selecionou a opção:\n[{tipo_escolha}]\n\nDeseja confirmar e prosseguir com a instalação?"
        )
        
        if not confirma:
            return # Cancela a operação e mantém os botões ativos.
            
        self.btn_dev.config(state=tk.DISABLED)
        self.btn_native.config(state=tk.DISABLED)
        self.safe_log("Iniciando instalação...")
        # Chama a função que foi passada na criação da classe.
        self.callback_iniciar(use_native)

    def finalizar_sucesso(self):
        self.root.title("Instalador - A11yDevs | Concluído")
        messagebox.showinfo("Sucesso", "Ambiente pronto para uso.")
        self.root.quit()

    def finalizar_erro(self, erro_msg):
        self.root.title("Instalador - A11yDevs | Falha")
        messagebox.showerror("Erro Crítico", f"A instalação foi interrompida:\n\n{erro_msg}")
        self.btn_dev.config(state=tk.NORMAL)
        self.btn_native.config(state=tk.NORMAL)
        self.btn_dev.focus_set()