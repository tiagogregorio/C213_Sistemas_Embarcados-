"""
view/main_window.py
Janela principal da aplicação com sistema de abas.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QStatusBar, QLabel,
    QAction, QFileDialog, QMessageBox  # <-- QAction adicionado
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from view.tab_identification import TabIdentification
from view.tab_pid_control import TabPIDControl
from utils.report_generator import ReportGenerator  # seu módulo PDF


class MainWindow(QMainWindow):
    """Janela principal com abas e barra de ferramentas para relatório."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._setup_window()
        self._setup_tabs()
        self._setup_statusbar()
        self._setup_toolbar()      # <-- nova barra de ferramentas

    def _setup_window(self):
        self.setWindowTitle("C213 — Identificação e Controle PID | Grupo 2")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        # Estilo geral da aplicação (igual ao original)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #1e1e2e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #181825;
                color: #cdd6f4;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #313244;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                min-width: 160px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e2e;
                color: #89b4fa;
                border-bottom: 2px solid #89b4fa;
            }
            QTabBar::tab:hover:!selected {
                background-color: #313244;
                color: #cdd6f4;
            }
            QGroupBox {
                color: #89b4fa;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #313244;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #89b4fa; }
            QLabel { color: #cdd6f4; font-size: 12px; }
            QStatusBar {
                background-color: #181825;
                color: #a6adc8;
                font-size: 11px;
            }
        """)

    def _setup_tabs(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Aba 1 — Identificação
        self.tab_id = TabIdentification(self.controller, self)
        self.tabs.addTab(self.tab_id, "🔍  Identificação")

        # Aba 2 — Controle PID
        self.tab_pid = TabPIDControl(self.controller, self)
        self.tabs.addTab(self.tab_pid, "⚙️  Controle PID")
        self.tabs.setTabEnabled(1, False)  # Bloqueada até identificar

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("Pronto. Carregue um dataset para começar.")
        self.status.addWidget(self.status_label)

    def _setup_toolbar(self):
        """Adiciona barra de ferramentas com ação para gerar relatório PDF."""
        toolbar = self.addToolBar("Ferramentas")
        toolbar.setStyleSheet("QToolBar { background-color: #181825; border: none; }")

        # Ação de gerar PDF
        self.action_pdf = QAction("📄  Gerar Relatório PDF", self)
        self.action_pdf.triggered.connect(self._on_generate_report)
        toolbar.addAction(self.action_pdf)

        # Opcional: desabilitar a ação até que haja identificação? (você decide)
        self.action_pdf.setEnabled(False)  # inicialmente desabilitado
        # Você pode habilitar após identificar (ver unlock_pid_tab)

    def _on_generate_report(self):
        """Slot chamado ao clicar no botão de relatório PDF."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório PDF", "relatorio_C213.pdf", "PDF (*.pdf)"
        )
        if not filepath:
            return

        # Cria o gerador e exporta
        gen = ReportGenerator(self.controller)
        success = gen.generate(filepath)

        if success:
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{filepath}")
            self.set_status(f"Relatório PDF exportado: {filepath}")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao gerar o relatório. Verifique se já existe uma simulação realizada.")

    def unlock_pid_tab(self):
        """Chamado pela aba de identificação após sucesso."""
        self.tabs.setTabEnabled(1, True)
        self.tab_pid.refresh_model_fields()
        self.status_label.setText("✅ Identificação concluída. Aba de Controle PID liberada.")
        # Habilita o botão de relatório PDF também
        self.action_pdf.setEnabled(True)

    def set_status(self, message: str):
        self.status_label.setText(message)