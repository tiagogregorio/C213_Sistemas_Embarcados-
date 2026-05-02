"""
main.py - Ponto de entrada da aplicação com tela de login.
"""
import sys
from PyQt5.QtWidgets import QApplication, QDialog  # <-- IMPORTE O QDialog
from view.main_window import MainWindow
from controller.app_controller import AppController
from view.login_dialog import LoginDialog

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("C213 - Controle PID | Grupo 2")

    # Tela de login (modal)
    login = LoginDialog()
    if login.exec_() != QDialog.Accepted:
        # Usuário cancelou ou falhou autenticação -> encerra o programa
        sys.exit(0)

    # Login bem-sucedido: cria o controller e a janela principal
    controller = AppController()
    window = MainWindow(controller)  # <-- corrigido: passa o controller
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()