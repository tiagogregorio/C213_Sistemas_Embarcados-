"""
controller/app_controller.py
Controlador principal da aplicação (camada C do MVC).
"""
import numpy as np
import os
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from model.data_loader import DataLoader
from model.identification import SmithIdentification, SundaresanIdentification, FOPDTModel
from model.pid_tuning import PIDTuner, PIDParameters, TuningMethod
from model.simulator import ClosedLoopSimulator, ResponseMetrics

class AppController:
    def __init__(self):
        self._loader    = DataLoader()
        self._smith     = SmithIdentification()
        self._sundar    = SundaresanIdentification()
        self._tuner     = PIDTuner()
        self._simulator = ClosedLoopSimulator()

        self.model_smith:    FOPDTModel = None
        self.model_sundar:   FOPDTModel = None
        self.fopdt_model:    FOPDTModel = None
        self.pid_params:     PIDParameters  = None

        self.time_data   = None
        self.output_data = None
        self.input_data  = None

        self.historico_simulacoes = {}
        self.dados_identificacao = {}
        self.dados_pid = {}
        self.view = None

    def load_dataset(self, filepath: str) -> dict:
        self._loader.load(filepath)
        self.time_data   = self._loader.time
        self.output_data = self._loader.output_signal
        self.input_data  = self._loader.input_signal
        return self._loader.summary()

    def run_identification(self) -> tuple:
        if self.time_data is None: raise RuntimeError("Carregue um dataset.")
        step = self._loader.get_step_amplitude()
        self.model_smith  = self._smith.identify(self.time_data, self.output_data, step)
        self.model_sundar = self._sundar.identify(self.time_data, self.output_data, step)

        self.dados_identificacao = {
            'Smith': {'K': self.model_smith.K, 'tau': self.model_smith.tau, 'theta': self.model_smith.theta, 'eqm': self.model_smith.eqm},
            'Sundaresan': {'K': self.model_sundar.K, 'tau': self.model_sundar.tau, 'theta': self.model_sundar.theta, 'eqm': self.model_sundar.eqm}
        }
        self.fopdt_model = self.model_smith if self.model_smith.eqm <= self.model_sundar.eqm else self.model_sundar
        return self.model_smith, self.model_sundar

    def get_model_curve(self, method: str = None):
        model = self.model_smith if method == "Smith" else self.model_sundar
        y0, step = float(self.output_data[0]), self._loader.get_step_amplitude()
        identifier = self._smith if method == "Smith" else self._sundar
        return self.time_data, identifier.get_model_response(self.time_data, model, step, y0)

    def select_model(self, method: str):
        if method == "Smith": self.fopdt_model = self.model_smith
        elif method == "Sundaresan": self.fopdt_model = self.model_sundar

    def tune_pid(self, method: TuningMethod, Kp_manual=1.0, Ti_manual=1.0, Td_manual=0.0, lambda_imc=1.0):
        if self.fopdt_model is None: raise RuntimeError("Identifique antes de sintonizar.")
        self.pid_params = self._tuner.tune(method, self.fopdt_model.K, self.fopdt_model.tau, self.fopdt_model.theta, Kp_manual, Ti_manual, Td_manual, lambda_imc)
        nome = method.value if hasattr(method, 'value') else str(method)
        self.dados_pid[nome] = {'Kp': self.pid_params.Kp, 'Ti': self.pid_params.Ti, 'Td': self.pid_params.Td}
        return self.pid_params

    def simulate_closed_loop(self, setpoint=1.0, t_end=None):
        if self.fopdt_model is None or self.pid_params is None: raise RuntimeError("Sintonia obrigatória.")
        t, y = self._simulator.simulate(self.fopdt_model, self.pid_params, setpoint, t_end)
        return t, y, self._simulator.compute_metrics(t, y, setpoint)

    def simular_e_comparar(self, nome_metodo, tempo, saida, setpoint, pid_params, metrics):
        self.historico_simulacoes[nome_metodo] = {
            't': tempo, 'y': saida, 'pid': pid_params, 'metrics': metrics
        }

    def limpar_grafico(self, setpoint):
        self.historico_simulacoes.clear()

    def gerar_relatorio_final(self, usar_ia=False):
        if not self.is_identified():
            QMessageBox.warning(None, "Atenção", "Identifique a planta primeiro.")
            return
        if len(self.historico_simulacoes) == 0:
            QMessageBox.warning(None, "Atenção", "Simule pelo menos um método antes de gerar o relatório.")
            return

        caminho_escolhido, _ = QFileDialog.getSaveFileName(None, "Salvar PDF", "Relatorio_C213.pdf", "PDF (*.pdf)")
        
        if not caminho_escolhido: return

        try:
            from utils.report_generator import ReportGenerator 
            gerador = ReportGenerator(self)
            
            if gerador.generate(caminho_escolhido, use_ai=usar_ia):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Sucesso")
                msg.setText(f"Relatório gerado com sucesso!\n\nSalvo em:\n{caminho_escolhido}")
                msg.exec_()
        except Exception as e:
            QMessageBox.critical(None, "Erro Crítico", f"Erro no PDF:\n{str(e)}")

    def is_identified(self): return self.fopdt_model is not None
    def is_dataset_loaded(self): return self._loader.is_loaded()
    def is_tuned(self): return self.pid_params is not None