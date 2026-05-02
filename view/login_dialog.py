"""
view/login_dialog.py
Tela de autenticação (login) para acesso ao sistema utilizando variáveis de ambiente.
"""

import os
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

class LoginDialog(QDialog):
    """
    Diálogo de login com autenticação.
    Credenciais são carregadas com segurança do arquivo .env.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso ao Sistema - C213")
        self.setModal(True)
        self.setFixedSize(400, 180) # Tamanho ligeiramente reduzido (sem o rodapé)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🔐 Autenticação Necessária")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Campos de entrada
        form_layout = QVBoxLayout()
        self.edit_user = QLineEdit()
        self.edit_user.setPlaceholderText("Usuário")
        
        self.edit_pass = QLineEdit()
        self.edit_pass.setPlaceholderText("Senha")
        self.edit_pass.setEchoMode(QLineEdit.Password)
        
        form_layout.addWidget(self.edit_user)
        form_layout.addWidget(self.edit_pass)
        layout.addLayout(form_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Entrar")
        self.btn_login.clicked.connect(self._on_login)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
    def _on_login(self):
        user_input = self.edit_user.text().strip()
        password_input = self.edit_pass.text().strip()
        
        if not user_input or not password_input:
            QMessageBox.warning(self, "Campos vazios", "Preencha usuário e senha.")
            return
            
        # Pega as credenciais seguras do sistema operacional / .env
        env_user = os.getenv("APP_USER")
        env_pass = os.getenv("APP_PASS")
        
        # Verifica se o arquivo .env foi criado corretamente
        if not env_user or not env_pass:
            QMessageBox.critical(self, "Erro de Configuração", 
                                 "Variáveis APP_USER ou APP_PASS não encontradas no arquivo .env.")
            return
            
        # Validação simples
        if user_input == env_user and password_input == env_pass:
            self.accept()  # login bem-sucedido
        else:
            QMessageBox.critical(self, "Acesso negado", "Usuário ou senha incorretos.")
            self.edit_pass.clear()