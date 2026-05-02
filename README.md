# C213 — Identificação de Sistemas e Controle PID
### Grupo 2 | Disciplina: Sistemas de Controle Automático

> Aplicação desktop para identificação de modelos FOPDT e projeto de controladores PID com interface gráfica interativa.

## Métodos Implementados

### Identificação de Sistemas
| Método | Pontos Utilizados | Descrição |
|--------|-------------------|-----------|
| **Smith** | 28.3% e 63.2% da resposta | Método clássico para sistemas FOPDT |
| **Sundaresan** | 35.3% e 85.3% da resposta | Maior precisão para sistemas com atraso |

O sistema calcula o **EQM (Erro Quadrático Médio)** de ambos e indica automaticamente o de melhor ajuste.

### Sintonia PID
| Método | Característica |
|--------|---------------|
| **Ziegler-Nichols** | Resposta rápida, maior sobressinal |
| **ITAE** | Minimiza erro ponderado no tempo, resposta mais suave |
| **Manual** | Permite ajuste fino dos parâmetros Kp, Ti e Td |

---

## Modelo FOPDT

O modelo identificado é o **First Order Plus Dead Time**:

```
         K · e^(-θs)
G(s) = ─────────────
          τs + 1
```

Onde:
- **K** — Ganho estático do processo
- **τ** — Constante de tempo (s)
- **θ** — Atraso (dead time) (s)

---

## Estrutura do Projeto

```
C213/
│
├── main.py                     # Ponto de entrada da aplicação
├── requirements.txt            # Dependências do projeto
│
├── model/                      # Camada Model (MVC)
│   ├── data_loader.py          # Carregamento de arquivos .mat
│   ├── identification.py       # Métodos Smith e Sundaresan
│   ├── pid_tuning.py           # Métodos de sintonia PID
│   └── simulator.py            # Simulação em malha fechada
│
├── view/                       # Camada View (MVC)
│   ├── main_window.py          # Janela principal com abas
│   ├── tab_identification.py   # Aba de Identificação
│   └── tab_pid_control.py      # Aba de Controle PID
│
├── controller/                 # Camada Controller (MVC)
│   └── app_controller.py       # Orquestra Model e View
│
└── data/
    └── Dataset_Grupo2_c213.mat # Dataset experimental
```

---

## Instalação e Execução

### Pré-requisitos

- Python 3.9 ou superior
- pip

### Passo a passo

**1. Clone o repositório**
```bash
git clone https://github.com/tiagogregorio/C213_Sistemas_Embarcados-.git
cd C213
```

**2. (Recomendado) Crie um ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

**3. Instale as dependências e configurações de segurança**
```bash
pip install -r requirements.txt

Configuração de Variáveis (Segurança)
Para proteger suas credenciais, configure o arquivo de ambiente:
Copie o arquivo .env.example para um novo arquivo chamado .env.
Abra o .env e preencha com suas chaves e dados de acesso.
Atenção: Nunca compartilhe seu arquivo .env!
```

**4. Execute a aplicação**
```bash
python main.py
```

---

## Como Usar

### Aba Identificação

1. Clique em **Carregar .mat** e selecione o dataset experimental
2. Clique em **Identificar** — o sistema roda Smith e Sundaresan automaticamente
3. Compare os resultados e o EQM de cada método na tabela
4. Selecione o modelo desejado no menu suspenso **"Usar para sintonia"**
5. Exporte o gráfico com **Exportar Gráfico** se necessário

### Aba Controle PID

1. Escolha o modo **Método** (automático) ou **Manual**
2. Se automático, selecione **Ziegler-Nichols** ou **ITAE**
3. Defina o **SetPoint** desejado
4. Clique em **Sintonizar** para simular a resposta em malha fechada
5. Analise as métricas: **tr**, **ts**, **Mp** e **ess**
6. Exporte o gráfico com **Exportar Gráfico**

---

## Resultados — Dataset Grupo 2

### Parâmetros Identificados

| Parâmetro | Smith | Sundaresan | Valor Real |
|-----------|-------|------------|------------|
| K | 0.8789 | 0.8789 | 0.88 |
| τ (s) | 30.92 | 30.66 | 31.0 |
| θ (s) | 5.80 | 11.47 | 6.0 |
| **EQM** | **7.788** | **0.047** | — |

> O método de **Sundaresan** apresentou EQM significativamente menor neste dataset.

### Parâmetros PID — Ziegler-Nichols

| Parâmetro | Valor |
|-----------|-------|
| Kp | 7.2737 |
| Ti (s) | 11.6092 |
| Td (s) | 2.9023 |
| **Mp** | **58.6%** |
| **tr** | **7.1 s** |
| **ts** | **34.9 s** |

### Parâmetros PID — ITAE

| Parâmetro | Valor |
|-----------|-------|
| Kp | 4.5894 |
| Ti (s) | 40.2364 |
| Td (s) | 2.0133 |
| **Mp** | **0.0%** |
| **tr** | **11.8 s** |
| **ts** | **47.1 s** |

> O **ITAE** apresenta resposta sem sobressinal, mais adequada para plantas térmicas onde oscilações são indesejadas. O **Ziegler-Nichols** é mais rápido, porém com sobressinal elevado de 58.6%.

---

## Dependências

```
PyQt5>=5.15
pyqtgraph>=0.13
numpy>=1.24
scipy>=1.10
control>=0.9
matplotlib>=3.7
```

---

## Referências

- Smith, C. L. (1972). *Digital Computer Process Control*. Intext Educational Publishers.
- Sundaresan, K. R., Krishnaswamy, P. R. (1978). *Estimation of time delay parameters in linear systems*. Ind. Eng. Chem. Process Des. Dev.
- Ziegler, J. G., Nichols, N. B. (1942). *Optimum settings for automatic controllers*. ASME Transactions.
- Ogata, K. (2010). *Engenharia de Controle Moderno*. 5ª Edição.
- Seborg, D. E., Edgar, T. F., Mellichamp, D. A. (2016). *Dinâmica e Controle de Processos*. 4ª Edição.

---

## Licença

Projeto acadêmico desenvolvido para a disciplina C213 — Sistemas de Controle Automático.  
Instituto Nacional de Telecomunicações — Inatel, 2026.
