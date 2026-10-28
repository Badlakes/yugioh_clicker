import json
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "workflows.json"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25


class DuelLinksBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Duel Links Bot — protótipo visual")
        self.root.geometry("650x540")
        self.root.minsize(600, 480)

        self.messages = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self.running = False

        self.gate_var = tk.BooleanVar(value=True)
        self.street_var = tk.BooleanVar(value=False)
        self.event_var = tk.BooleanVar(value=False)
        self.clicks_var = tk.BooleanVar(value=False)  # seguro por padrão
        self.minutes_var = tk.StringVar(value="5")
        self.confidence_var = tk.StringVar(value="0.90")
        self.status_var = tk.StringVar(value="Parado")

        self._build_ui()
        self.root.after(100, self._drain_messages)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Duel Links Bot", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Protótipo: reconhecimento por imagens + fluxos configuráveis.",
            wraplength=600
        ).pack(anchor="w", pady=(2, 12))

        modes = ttk.LabelFrame(outer, text="O que executar", padding=10)
        modes.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(modes, text="Loop do Portão", variable=self.gate_var).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Checkbutton(modes, text="Loop de personagens da rua", variable=self.street_var).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Checkbutton(modes, text="Fluxo do evento (configurável)", variable=self.event_var).grid(row=2, column=0, sticky="w", padx=4, pady=4)

        settings = ttk.LabelFrame(outer, text="Configurações do teste", padding=10)
        settings.pack(fill="x", pady=(0, 10))
        ttk.Label(settings, text="Tempo limite (minutos):").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(settings, textvariable=self.minutes_var, width=8).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(settings, text="Confiança da imagem (0.70–0.99):").grid(row=0, column=2, sticky="w", padx=(18, 4), pady=4)
        ttk.Entry(settings, textvariable=self.confidence_var, width=8).grid(row=0, column=3, sticky="w", padx=4, pady=4)
        ttk.Checkbutton(
            settings,
            text="Ativar cliques reais (desmarcado = apenas simulação/log)",
            variable=self.clicks_var
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=4, pady=8)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 10))
        self.start_button = ttk.Button(actions, text="Iniciar teste", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Parar", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Label(actions, textvariable=self.status_var).pack(side="right")

        log_frame = ttk.LabelFrame(outer, text="Log", padding=6)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(
            outer,
            text="Emergência: mova o mouse para o canto superior esquerdo para acionar o FAILSAFE do PyAutoGUI.",
            wraplength=600
        ).pack(anchor="w", pady=(8, 0))

    def log(self, message):
        self.messages.put(("log", message))

    def _drain_messages(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == "log":
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", value + "\n")
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
                elif kind == "finished":
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.status_var.set("Parado")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_messages)

    def start(self):
        if self.running:
            return

        selected = []
        if self.gate_var.get():
            selected.append("portao")
        if self.street_var.get():
            selected.append("personagens")
        if self.event_var.get():
            selected.append("evento")
        if not selected:
            messagebox.showwarning("Seleção vazia", "Marque pelo menos um fluxo.")
            return

        try:
            minutes = float(self.minutes_var.get().replace(",", "."))
            confidence = float(self.confidence_var.get().replace(",", "."))
            if minutes <= 0:
                raise ValueError
            if not 0.70 <= confidence <= 0.99:
                raise ValueError
        except ValueError:
            messagebox.showerror("Configuração inválida", "Informe minutos > 0 e confiança entre 0.70 e 0.99.")
            return

        try:
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Erro de configuração", f"Não consegui ler workflows.json:\n{exc}")
            return

        self.stop_event.clear()
        self.running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Executando")
        self.worker = threading.Thread(
            target=self._run_worker,
            args=(selected, minutes * 60, confidence, self.clicks_var.get(), config),
            daemon=True
        )
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        self.log("Pedido de parada recebido; aguardando a etapa atual terminar…")
        self.status_var.set("Parando…")

    def _run_worker(self, selected, duration, confidence, real_clicks, config):
        deadline = time.monotonic() + duration
        mode = "CLIQUE REAL ATIVADO" if real_clicks else "SIMULAÇÃO (nenhum clique será feito)"
        self.log(f"Início. Modos: {', '.join(selected)}. {mode}.")
        try:
            while time.monotonic() < deadline and not self.stop_event.is_set():
                did_any_step = False
                for profile in selected:
                    if self.stop_event.is_set() or time.monotonic() >= deadline:
                        break
                    workflow = config.get(profile, [])
                    if not workflow:
                        self.log(f"[{profile}] Nenhuma etapa configurada ainda. Adicione imagens e passos em workflows.json.")
                        continue
                    did_any_step = True
                    self.log(f"[{profile}] Iniciando uma passagem do fluxo.")
                    completed = self._run_workflow(profile, workflow, confidence, real_clicks, deadline)
                    if not completed:
                        self.log(f"[{profile}] Fluxo interrompido ou imagem não reconhecida; não vou clicar às cegas.")
                        self.log(f"[{profile}] Parando este teste para evitar repetir a mesma busca indefinidamente.")
                        self.stop_event.set()
                        break
                    else:
                        self.log(f"[{profile}] Passagem concluída.")
                if not did_any_step:
                    self.log("Nenhum fluxo tem etapas configuradas. Encerrando.")
                    break
                time.sleep(0.5)
        except pyautogui.FailSafeException:
            self.log("FAILSAFE acionado pelo canto superior esquerdo. Execução interrompida.")
        except Exception as exc:
            self.log(f"Erro: {type(exc).__name__}: {exc}")
        finally:
            self.log("Execução encerrada.")
            self.messages.put(("finished", None))

    def _run_workflow(self, profile, workflow, confidence, real_clicks, deadline):
        for step in workflow:
            if self.stop_event.is_set() or time.monotonic() >= deadline:
                return False

            image_names = step.get("images")
            if not image_names:
                image_names = [step.get("image", "")]
            image_paths = [BASE / name for name in image_names if name]
            timeout = float(step.get("timeout_seconds", 12))
            wait_after = float(step.get("wait_after_seconds", 1))
            wait_second_click = float(step.get("wait_second_click", 0))
            label = step.get("label", ", ".join(Path(name).name for name in image_names))

            missing = [path for path in image_paths if not path.is_file()]
            if not image_paths or missing:
                self.log(f"[{profile}] Imagem ausente: {', '.join(str(x) for x in missing) or 'nenhum caminho configurado'}")
                return False

            self.log(f"[{profile}] Procurando: {label}")
            step_deadline = min(time.monotonic() + timeout, deadline)
            position = None
            matched_image = None
            while time.monotonic() < step_deadline and not self.stop_event.is_set():
                for image_path in image_paths:
                    try:
                        position = pyautogui.locateCenterOnScreen(
                            str(image_path), confidence=confidence, grayscale=False
                        )
                    except Exception as exc:
                        # PyAutoGUI/OpenCV versions may raise ImageNotFoundException.
                        if exc.__class__.__name__ == "ImageNotFoundException":
                            position = None
                        else:
                            raise
                    if position:
                        matched_image = image_path
                        break
                if position:
                    break
                time.sleep(0.4)

            if not position:
                self.log(f"[{profile}] Não encontrei nenhuma imagem de '{label}' dentro do prazo.")
                return False

            self.log(f"[{profile}] Encontrado '{matched_image.name}' em x={position.x}, y={position.y}.")
            if real_clicks:
                pyautogui.click(position.x, position.y)
                self.log(f"[{profile}] Clique executado.")
            else:
                self.log(f"[{profile}] Simulação: clicaria nessa posição.")
            if wait_second_click > 0:
                self.log(f"[{profile}] Teste: {wait_second_click} segundos de espera antes do segundo clique.")
                time.sleep(max(0, wait_second_click))
                if real_clicks:
                    pyautogui.click(position.x, position.y)
                    self.log(f"[{profile}] Segundo clique executado.")
                else:
                    self.log(f"[{profile}] Simulação: clicaria nessa posição uma segunda vez.")

            time.sleep(max(0, wait_after))
        return True

    def _on_close(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DuelLinksBotUI(root)
    root.mainloop()
