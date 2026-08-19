;; init-a11y.el --- Voz e Acessibilidade ---

;; --- Configurações Básicas de Áudio e Feedback ---
(setq emacspeak-play-program nil)
(setq emacspeak-use-auditory-icons nil)
(setq emacspeak-line-echo t)
(setq echo-keystrokes 0.1)
(setq ring-bell-function #'ignore)

(defgroup my-accessibility nil
  "Configurações de acessibilidade do usuário."
  :group 'applications)

;; --- Hooks de Sistema e Limpeza de Processos ---
(defun my-speak-saved ()
  "Anuncia que o arquivo foi salvo."
  (message "Arquivo salvo.")
  (when (fboundp 'emacspeak-speak-line)
    (emacspeak-speak-line)))
(add-hook 'after-save-hook #'my-speak-saved)

(defun my/emacspeak-process-p (proc)
  "Retorna t se PROC parecer ser um processo do Emacspeak."
  (let ((name (process-name proc))
        (buf  (process-buffer proc)))
    (or (eq proc (and (boundp 'dtk-speaker-process) dtk-speaker-process))
        (and name (string-match-p "speaker\\|dtk\\|tts\\|sharpwin" name))
        (and buf
             (buffer-live-p buf)
             (string-match-p "speaker\\|dtk\\|tts\\|sharpwin"
                             (buffer-name buf))))))

(defun my/emacspeak-disable-exit-query ()
  "Desativa a pergunta de saída para processos do Emacspeak."
  (dolist (proc (process-list))
    (when (and (process-live-p proc)
               (my/emacspeak-process-p proc))
      (set-process-query-on-exit-flag proc nil))))

(defun my/emacspeak-cleanup ()
  "Desativa query-on-exit e encerra processos do Emacspeak ao fechar."
  (my/emacspeak-disable-exit-query)
  (dolist (proc (process-list))
    (when (and (process-live-p proc)
               (my/emacspeak-process-p proc))
      (ignore-errors
        (delete-process proc)))))

;; --- Configuração de Idioma ---
(defun my/emacspeak-apply-language ()
  "Aplica português do Brasil forçando o nome exato da voz no SAPI."
  (interactive)
  (ignore-errors (dtk-set-language "pt-br"))
  (ignore-errors (dtk-set-voice "Microsoft Maria Desktop"))
  (setq dtk-speech-rate 180))

(add-hook 'emacs-startup-hook
          (lambda ()
            (run-with-idle-timer 1 nil #'my/emacspeak-disable-exit-query)
            (run-with-idle-timer 2 nil #'my/emacspeak-apply-language)))

(add-hook 'kill-emacs-hook #'my/emacspeak-cleanup)

;; --- Alternância Dinâmica de Idiomas (Atalho) ---
(defvar my/emacspeak-current-language "pt-br"
  "Idioma atual do Emacspeak controlado pelo usuário.")

(defun my/emacspeak-toggle-language ()
  "Alterna rapidamente entre português do Brasil (Maria) e inglês (Zira)."
  (interactive)
  (when (fboundp 'dtk-stop)
    (dtk-stop))
  
  (if (string= my/emacspeak-current-language "pt-br")
      (progn
        (ignore-errors (dtk-set-language "en"))
        (ignore-errors (dtk-set-voice "Microsoft Zira Desktop"))
        (setq my/emacspeak-current-language "en")
        (run-with-timer
         0.2 nil
         (lambda ()
           (when (fboundp 'dtk-speak)
             (dtk-speak "English mode")))))
    (progn
      (ignore-errors (dtk-set-language "pt-br"))
      (ignore-errors (dtk-set-voice "Microsoft Maria Desktop"))
      (setq my/emacspeak-current-language "pt-br")
      (run-with-timer
       0.2 nil
       (lambda ()
         (when (fboundp 'dtk-speak)
           (dtk-speak "Modo português")))))))

(global-set-key (kbd "C-c t") #'my/emacspeak-toggle-language)

(provide 'init-accessibility)