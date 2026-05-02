"""
view/tab_pid_control.py
Aba de Controle PID completa com layout estável e gráfico zoom.
"""
import numpy as np
import os
import pyqtgraph.exporters
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QSizePolicy,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from model.pid_tuning import TuningMethod

class TabPIDControl(QWidget):
    def __init__(self, controller, main_window):
        super().__init__()
        self.controller  = controller
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.addWidget(self._build_left_panel(), stretch=1)
        layout.addWidget(self._build_right_panel(), stretch=3)

    def _build_left_panel(self):
        panel = QWidget()
        vlay  = QVBoxLayout(panel)

        grp_plant = QGroupBox("1. Planta Identificada")
        grid_plant = QGridLayout(grp_plant)
        self._model_fields = {}
        for i, key in enumerate(["K", "tau", "theta", "eqm"]):
            grid_plant.addWidget(QLabel(f"{key}:"), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background-color:#11111b; color:#a6e3a1; font-weight:bold;")
            grid_plant.addWidget(f, i, 1)
            self._model_fields[key] = f
        vlay.addWidget(grp_plant)

        grp_tune = QGroupBox("2. Sintonia PID")
        vlay_tune = QVBoxLayout(grp_tune)
        
        self._rb_method = QRadioButton("Método Automático")
        self._rb_manual = QRadioButton("Manual")
        self._rb_method.setChecked(True)
        self._rb_method.toggled.connect(self._on_mode_changed)
        
        bg = QButtonGroup(self)
        bg.addButton(self._rb_method)
        bg.addButton(self._rb_manual)
        
        vlay_tune.addWidget(self._rb_method)
        self._combo_method = QComboBox()
        from model.pid_tuning import PIDTuner
        for method in PIDTuner().available_methods():
            if method.name != "MANUAL": self._combo_method.addItem(method.value, method)
        vlay_tune.addWidget(self._combo_method)
        
        self.lbl_lambda = QLabel("λ (Apenas IMC):")
        self.spin_lambda = QDoubleSpinBox()
        self.spin_lambda.setRange(0.01, 9999.0)
        self.spin_lambda.setValue(20.0)
        self.lbl_lambda.setVisible(False)
        self.spin_lambda.setVisible(False)
        self._combo_method.currentIndexChanged.connect(self._check_imc)
        vlay_tune.addWidget(self.lbl_lambda)
        vlay_tune.addWidget(self.spin_lambda)

        vlay_tune.addWidget(self._rb_manual)
        
        self._pid_fields = {}
        pid_grid = QGridLayout()
        for i, key in enumerate(["Kp", "Ti", "Td"]):
            pid_grid.addWidget(QLabel(f"{key}:"), i, 0)
            sp = QDoubleSpinBox()
            sp.setDecimals(4)
            sp.setRange(0.0, 99999.0)
            pid_grid.addWidget(sp, i, 1)
            self._pid_fields[key] = sp
        vlay_tune.addLayout(pid_grid)
        vlay.addWidget(grp_tune)

        grp_sp = QGroupBox("3. SetPoint")
        grid_sp = QGridLayout(grp_sp)
        self._spin_sp = QDoubleSpinBox()
        self._spin_sp.setRange(-9999.0, 9999.0)
        self._spin_sp.setValue(1.0)
        grid_sp.addWidget(QLabel("SetPoint:"), 0, 0)
        grid_sp.addWidget(self._spin_sp, 0, 1)
        self._spin_tend = QDoubleSpinBox()
        self._spin_tend.setRange(10.0, 9999.0)
        self._spin_tend.setValue(300.0)
        grid_sp.addWidget(QLabel("t final (s):"), 1, 0)
        grid_sp.addWidget(self._spin_tend, 1, 1)
        vlay.addWidget(grp_sp)

        grp_metrics = QGroupBox("4. Métricas")
        grid_metrics = QGridLayout(grp_metrics)
        labels = [("tr (subida):", "tr"), ("ts (acomod.):", "ts"), ("Mp (overshoot):", "Mp"), ("ess (regime):", "ess")]
        self._metric_fields = {}
        for i, (lbl, key) in enumerate(labels):
            grid_metrics.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background-color:#11111b; color:#89dceb; font-weight:bold;")
            grid_metrics.addWidget(f, i, 1)
            self._metric_fields[key] = f
        vlay.addWidget(grp_metrics)

        self._set_manual_mode(False)
        return panel

    def _build_right_panel(self):
        panel = QWidget()
        vlay  = QVBoxLayout(panel)

        self._plot = pg.PlotWidget(title="Resposta ao Degrau — Malha Fechada")
        self._plot.addLegend()
        self._plot.showGrid(x=True, y=True, alpha=0.15) 
        self._plot.getViewBox().setMouseMode(pg.ViewBox.RectMode)
        
        dica = QLabel("💡 Dica: Arraste com o botão esquerdo para Zoom | Botão Direito > View All para resetar")
        dica.setStyleSheet("color: #a6adc8; font-size: 10px;")
        vlay.addWidget(dica)
        vlay.addWidget(self._plot, stretch=4)

        botoes = QHBoxLayout()
        self.btn_simular = QPushButton("▶ Simular Curva")
        self.btn_simular.setStyleSheet("background-color:#00529b; color:white; font-weight:bold; padding: 8px;")
        self.btn_simular.clicked.connect(self._on_simulate)
        
        self.btn_limpar = QPushButton("🧹 Limpar")
        self.btn_limpar.setStyleSheet("background-color:#585b70; color:white; padding: 8px;")
        self.btn_limpar.clicked.connect(self._on_limpar)

        self.btn_exportar = QPushButton("💾 Salvar Grafico Local")
        self.btn_exportar.setStyleSheet("background-color:#179299; color:white; padding: 8px;")
        self.btn_exportar.clicked.connect(self._on_export)

        self.btn_rep_std = QPushButton("📄 Relatório Teórico")
        self.btn_rep_std.setStyleSheet("background-color:#2c3e50; color:white; padding: 8px;")
        self.btn_rep_std.clicked.connect(lambda: self.controller.gerar_relatorio_final(usar_ia=False))

        self.btn_rep_ia = QPushButton("✨ Relatório IA")
        self.btn_rep_ia.setStyleSheet("background-color:#6c2b91; color:white; font-weight:bold; padding: 8px;")
        self.btn_rep_ia.clicked.connect(lambda: self.controller.gerar_relatorio_final(usar_ia=True))

        botoes.addWidget(self.btn_simular)
        botoes.addWidget(self.btn_limpar)
        botoes.addWidget(self.btn_exportar)
        botoes.addWidget(self.btn_rep_std)
        botoes.addWidget(self.btn_rep_ia)
        vlay.addLayout(botoes)
        return panel

    def _check_imc(self):
        method = self._combo_method.currentData()
        self.spin_lambda.setVisible(method and method.name == "IMC" and self._rb_method.isChecked())
        self.lbl_lambda.setVisible(method and method.name == "IMC" and self._rb_method.isChecked())

    def _on_mode_changed(self):
        self._set_manual_mode(self._rb_manual.isChecked())

    def _set_manual_mode(self, manual: bool):
        self._combo_method.setEnabled(not manual)
        for sp in self._pid_fields.values(): 
            sp.setReadOnly(not manual)
            sp.setStyleSheet("" if manual else "background-color:#11111b; color:#a6e3a1;")
        self._check_imc()

    def _on_simulate(self):
        try:
            sp = self._spin_sp.value()
            if self._rb_manual.isChecked():
                method = TuningMethod.MANUAL
                kp = self._pid_fields["Kp"].value()
                ti = self._pid_fields["Ti"].value()
                td = self._pid_fields["Td"].value()
                l_imc = 0.0
                nome_curva = f"Manual (Kp={kp:.1f})"
            else:
                method = self._combo_method.currentData()
                kp, ti, td = 1.0, 1.0, 0.0
                l_imc = self.spin_lambda.value()
                nome_curva = method.value if hasattr(method, 'value') else str(method)

            pid = self.controller.tune_pid(method, kp, ti, td, l_imc)
            
            if not self._rb_manual.isChecked():
                self._pid_fields["Kp"].setValue(pid.Kp)
                self._pid_fields["Ti"].setValue(pid.Ti)
                self._pid_fields["Td"].setValue(pid.Td)

            t, y, metrics = self.controller.simulate_closed_loop(sp, self._spin_tend.value())
            self.controller.simular_e_comparar(nome_curva, t, y, sp, pid, metrics)
            self._atualizar_grafico()
            
            self._metric_fields["tr"].setText(f"{metrics.rise_time:.3f} s" if metrics.rise_time else "—")
            self._metric_fields["ts"].setText(f"{metrics.settling_time:.3f} s" if metrics.settling_time else "—")
            self._metric_fields["Mp"].setText(f"{metrics.overshoot:.2f} %" if metrics.overshoot else "—")
            self._metric_fields["ess"].setText(f"{metrics.steady_state_error:.4f}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _on_limpar(self):
        self.controller.limpar_grafico(self._spin_sp.value())
        self._atualizar_grafico()

    def _atualizar_grafico(self):
        self._plot.clear()
        sp = self._spin_sp.value()
        
        sp_line = pg.InfiniteLine(pos=sp, angle=0, pen=pg.mkPen("#fab387", width=1.5, style=Qt.DashLine))
        self._plot.addItem(sp_line)
        
        cores = ['#a6e3a1', '#f38ba8', '#89b4fa', '#f9e2af', '#cba6f7', '#94e2d5']
        
        for i, (nome, dados) in enumerate(self.controller.historico_simulacoes.items()):
            cor = cores[i % len(cores)]
            t = dados['t']
            y = dados['y']
            met = dados['metrics']

            self._plot.plot(t, y, pen=pg.mkPen(cor, width=2), name=nome)

            if met.overshoot > 0.5 and met.peak_time is not None:
                self._add_marker(met.peak_time, met.peak_value, f"Mp={met.overshoot:.1f}%", cor)
            if met.settling_time is not None:
                y_ts = float(np.interp(met.settling_time, t, y))
                self._add_marker(met.settling_time, y_ts, f"ts={met.settling_time:.1f}s", cor)

    def _add_marker(self, t, y, label, color):
        scatter = pg.ScatterPlotItem(x=[t], y=[y], symbol="o", size=8, pen=pg.mkPen(color), brush=pg.mkBrush(color))
        text = pg.TextItem(label, color=color, anchor=(0, 1))
        text.setPos(t, y)
        self._plot.addItem(scatter)
        self._plot.addItem(text)

    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Gráfico", "grafico_pid.png", "PNG (*.png)")
        if filepath:
            QtWidgets.QApplication.processEvents()
            exporter = pg.exporters.ImageExporter(self._plot.plotItem)
            exporter.export(filepath)

    def refresh_model_fields(self):
        m = self.controller.fopdt_model
        if not m: return
        self._model_fields["K"].setText(f"{m.K:.4f}")
        self._model_fields["tau"].setText(f"{m.tau:.4f}")
        self._model_fields["theta"].setText(f"{m.theta:.4f}")
        self._model_fields["eqm"].setText(f"{m.eqm:.6f}")
        if self.controller.output_data is not None:
            self._spin_sp.setValue(round(float(self.controller.output_data[-1]), 2))