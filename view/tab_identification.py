"""
view/tab_identification.py
Aba de Identificação de Sistemas — Smith e Sundaresan com comparação de EQM.
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFileDialog, QGridLayout, QLineEdit,
    QSizePolicy, QMessageBox, QComboBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class TabIdentification(QWidget):
    """
    Aba 1: Carrega dataset .mat, executa Smith e Sundaresan,
    compara EQM e permite ao usuário escolher o modelo para sintonia.
    """

    def __init__(self, controller, main_window):
        super().__init__()
        self.controller  = controller
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self._build_left_panel(), stretch=1)
        layout.addWidget(self._build_right_panel(), stretch=3)

    # ── Painel esquerdo com scroll ────────────────────────────────────────

    def _build_left_panel(self):
        # ScrollArea para o painel não ficar cortado em telas pequenas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(12)
        layout.setContentsMargins(4, 4, 8, 4)

        layout.addWidget(self._build_dataset_group())
        layout.addWidget(self._build_info_group())
        layout.addWidget(self._build_smith_group())
        layout.addWidget(self._build_sundar_group())
        layout.addWidget(self._build_comparison_group())
        layout.addWidget(self._build_export_btn())
        layout.addStretch()

        scroll.setWidget(inner)
        return scroll

    def _build_dataset_group(self):
        grp    = QGroupBox("Dataset")
        layout = QVBoxLayout(grp)

        self.lbl_file = QLabel("Nenhum arquivo carregado.")
        self.lbl_file.setWordWrap(True)
        self.lbl_file.setStyleSheet("color:#a6adc8; font-size:11px;")

        btn_load = QPushButton("📂  Carregar .mat")
        btn_load.clicked.connect(self._on_load)

        layout.addWidget(btn_load)
        layout.addWidget(self.lbl_file)
        return grp

    def _build_info_group(self):
        grp    = QGroupBox("Informações do Dataset")
        g      = QGridLayout(grp)
        g.setSpacing(5)

        rows = [("Amostras:", "n_amostras"), ("t inicial (s):", "t_inicial"),
                ("t final (s):", "t_final"), ("y mín:", "y_min"),
                ("y máx:", "y_max"), ("Degrau:", "amplitude_degrau")]
        self._info_fields = {}
        for i, (lbl, key) in enumerate(rows):
            g.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background:#11111b; color:#a6adc8;")
            g.addWidget(f, i, 1)
            self._info_fields[key] = f
        return grp

    def _make_result_grid(self, keys):
        """Cria um grid de campos somente-leitura para resultados."""
        fields = {}
        grid   = QGridLayout()
        grid.setSpacing(5)
        labels = {"K": "K (ganho):", "tau": "τ (s):", "theta": "θ (s):", "eqm": "EQM:"}
        for i, key in enumerate(keys):
            grid.addWidget(QLabel(labels[key]), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background:#11111b; color:#a6e3a1; font-weight:bold;")
            grid.addWidget(f, i, 1)
            fields[key] = f
        return grid, fields

    def _build_smith_group(self):
        grp    = QGroupBox("Método de Smith")
        layout = QVBoxLayout(grp)

        self.btn_identify = QPushButton("🔍  Identificar (Smith + Sundaresan)")
        self.btn_identify.setEnabled(False)
        self.btn_identify.clicked.connect(self._on_identify)
        layout.addWidget(self.btn_identify)

        grid, self._smith_fields = self._make_result_grid(["K", "tau", "theta", "eqm"])
        layout.addLayout(grid)
        return grp

    def _build_sundar_group(self):
        grp    = QGroupBox("Método de Sundaresan")
        layout = QVBoxLayout(grp)

        grid, self._sundar_fields = self._make_result_grid(["K", "tau", "theta", "eqm"])
        layout.addLayout(grid)
        return grp

    def _build_comparison_group(self):
        grp    = QGroupBox("Comparação e Seleção")
        layout = QVBoxLayout(grp)
        layout.setSpacing(8)

        # Label indicando o melhor método
        self.lbl_best = QLabel("—")
        self.lbl_best.setAlignment(Qt.AlignCenter)
        self.lbl_best.setStyleSheet(
            "color:#a6e3a1; font-weight:bold; font-size:12px;"
            "background:#11111b; border-radius:4px; padding:4px;"
        )
        layout.addWidget(self.lbl_best)

        # ComboBox para o usuário escolher
        row = QHBoxLayout()
        row.addWidget(QLabel("Usar para sintonia:"))
        self.combo_model = QComboBox()
        self.combo_model.addItem("Smith",       "Smith")
        self.combo_model.addItem("Sundaresan",  "Sundaresan")
        self.combo_model.setEnabled(False)
        self.combo_model.currentIndexChanged.connect(self._on_model_selected)
        row.addWidget(self.combo_model)
        layout.addLayout(row)

        return grp

    def _build_export_btn(self):
        self.btn_export = QPushButton("💾  Exportar Gráfico")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)
        return self.btn_export

    # ── Painel direito (gráfico) ──────────────────────────────────────────

    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        pg.setConfigOption("background", "#11111b")
        pg.setConfigOption("foreground", "#cdd6f4")

        self.plot_widget = pg.PlotWidget(title="Resposta ao Degrau — Malha Aberta")
        self.plot_widget.setLabel("left",   "Saída y(t)")
        self.plot_widget.setLabel("bottom", "Tempo (s)")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.plot_widget)
        return panel

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Dataset", "", "MATLAB Files (*.mat)"
        )
        if not filepath:
            return
        try:
            summary = self.controller.load_dataset(filepath)
            self._update_info(summary, filepath)
            self._plot_raw_data()
            self.btn_identify.setEnabled(True)
            name = filepath.replace("\\", "/").split("/")[-1]
            self.main_window.set_status(f"Dataset carregado: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar", str(e))

    def _on_identify(self):
        try:
            smith, sundar = self.controller.run_identification()

            # Preenche campos Smith
            self._fill_fields(self._smith_fields, smith)

            # Preenche campos Sundaresan
            self._fill_fields(self._sundar_fields, sundar)

            # Indica o melhor método
            best = "Smith" if smith.eqm <= sundar.eqm else "Sundaresan"
            self.lbl_best.setText(f"✅ Menor EQM: {best}")

            # Seleciona o melhor no combobox
            self.combo_model.setCurrentText(best)
            self.combo_model.setEnabled(True)

            # Plota as duas curvas
            self._plot_models(smith, sundar)

            self.btn_export.setEnabled(True)
            self.main_window.unlock_pid_tab()

        except Exception as e:
            QMessageBox.critical(self, "Erro na Identificação", str(e))

    def _on_model_selected(self):
        """Atualiza o modelo ativo no controller quando o usuário troca o combo."""
        method = self.combo_model.currentData()
        if method and self.controller.is_identified():
            self.controller.select_model(method)
            self.main_window.set_status(f"Modelo ativo: {method}")
            # Atualiza a aba PID com o novo modelo
            self.main_window.tab_pid.refresh_model_fields()

    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Gráfico", "identificacao.png", "PNG (*.png)"
        )
        if filepath:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(filepath)
            self.main_window.set_status(f"Gráfico exportado: {filepath}")

    # ── Helpers ───────────────────────────────────────────────────────────

    def _plot_raw_data(self):
        self.plot_widget.clear()
        self.plot_widget.plot(
            self.controller.time_data,
            self.controller.output_data,
            pen=pg.mkPen("#89b4fa", width=2),
            name="Dados Reais",
        )

    def _plot_models(self, smith, sundar):
        """Plota dados reais + curva Smith + curva Sundaresan."""
        self.plot_widget.clear()

        # Dados reais
        self.plot_widget.plot(
            self.controller.time_data,
            self.controller.output_data,
            pen=pg.mkPen("#89b4fa", width=2),
            name="Dados Reais",
        )

        # Curva Smith
        t_s, y_s = self.controller.get_model_curve("Smith")
        self.plot_widget.plot(
            t_s, y_s,
            pen=pg.mkPen("#f38ba8", width=2, style=Qt.DashLine),
            name=f"Smith  (EQM={smith.eqm:.4f})",
        )

        # Curva Sundaresan
        t_u, y_u = self.controller.get_model_curve("Sundaresan")
        self.plot_widget.plot(
            t_u, y_u,
            pen=pg.mkPen("#a6e3a1", width=2, style=Qt.DotLine),
            name=f"Sundaresan  (EQM={sundar.eqm:.4f})",
        )

    def _fill_fields(self, fields, model):
        fields["K"].setText(f"{model.K:.4f}")
        fields["tau"].setText(f"{model.tau:.4f}")
        fields["theta"].setText(f"{model.theta:.4f}")
        fields["eqm"].setText(f"{model.eqm:.6f}")

    def _update_info(self, summary, filepath):
        name = filepath.replace("\\", "/").split("/")[-1]
        self.lbl_file.setText(name)
        mapping = {
            "n_amostras":       str(summary.get("n_amostras", "—")),
            "t_inicial":        f"{summary.get('t_inicial', 0):.3f}",
            "t_final":          f"{summary.get('t_final',   0):.3f}",
            "y_min":            f"{summary.get('y_min',     0):.4f}",
            "y_max":            f"{summary.get('y_max',     0):.4f}",
            "amplitude_degrau": f"{summary.get('amplitude_degrau', 1):.4f}",
        }
        for key, val in mapping.items():
            if key in self._info_fields:
                self._info_fields[key].setText(val)