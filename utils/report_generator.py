"""
utils/report_generator.py
Geração de Laudo Técnico Profissional focado em Engenharia de Controle Clássico.
"""
import os
from fpdf import FPDF
from google import genai
from dotenv import load_dotenv

load_dotenv()

class ReportGenerator(FPDF):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.api_key = os.getenv("GEMINI_API_KEY")

    def header(self):
        self.set_fill_color(30, 70, 110)
        self.rect(0, 0, 210, 25, 'F')
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, 'LAUDO TECNICO DE ENGENHARIA - CONTROLE PID', ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Disciplina C213 - Sistemas Embarcados - Inatel 2026', ln=True, align='C')
        self.ln(15)

    def _escrever_fundamentacao_teorica(self):
        """Secção educativa sobre Kp, Ti e Td."""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '3. Fundamentacao Teorica da Aplicacao', ln=True)
        self.set_font('Arial', '', 10)
        texto = (
            "O sistema opera em malha fechada utilizando o erro (SP-PV) para correcao. "
            "A Acao Proporcional (Kp) reduz o erro e acelera a subida, mas aumenta o sobressinal. "
            "A Acao Integral (Ti) elimina o erro estacionario, mas pode instabilizar se for excessiva. "
            "A Acao Derivativa (Td) amortece as oscilacoes, atuando como um freio preditivo."
        )
        self.multi_cell(0, 5, texto)
        self.ln(5)

    def _escrever_nota_tecnica_local(self):
        """Exibe a lógica do sistema especialista (Apenas no Relatório Local)."""
        self.ln(10)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, 'Apendice: Logica de Diagnostico do Relatorio Local', ln=True)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        
        regras = (
            "* Regra de Sobressinal (Mp): Alerta de agressividade se Mp > 20%; Moderado entre 0.5% e 20%; Conservador se ~0%.\n"
            "* Regra de Estabilidade (ts): Se o tempo de acomodacao for nulo (N/A), o sistema e diagnosticado como instavel.\n"
            "* Regra de Erro Estatico (ess): Se ess > 0.05, indica que a acao integral (Ti) foi ineficaz para anular o desvio."
        )
        self.multi_cell(0, 4, regras)

    def _gerar_analise_estatica(self, historico):
        """Analise baseada no sistema de regras local robusto (Suporta instabilidade)."""
        if not historico:
            return "Nenhuma simulacao foi realizada para analise transitoria."
            
        txt = ""
        for nome, dados in historico.items():
            met = dados['metrics']
            txt += f"[{nome}]: "
            
            # Avaliação de Sobressinal com proteção contra 'None'
            if met.overshoot is not None:
                if met.overshoot > 20: txt += f"Comportamento agressivo (Mp={met.overshoot:.1f}%). "
                elif met.overshoot > 0.5: txt += f"Resposta moderada (Mp={met.overshoot:.1f}%). "
                else: txt += "Resposta conservadora/suave. "
            else:
                txt += "Sistema instavel. "
            
            # Avaliação de Tempo de Acomodação
            if met.settling_time is not None: txt += f"Estabiliza em {met.settling_time:.1f}s. "
            else: txt += "Nao estabilizou no tempo limite. "
            
            # Avaliação de Erro de Regime
            if met.steady_state_error is not None and met.steady_state_error > 0.05: 
                txt += "Acao integral ineficaz."
                
            txt += "\n\n"
        return txt

    def obter_analise_ia(self, simulacoes, K, tau, theta):
        """Analise profunda via Google Gemini API."""
        if not self.api_key: return self._gerar_analise_estatica(simulacoes)
        try:
            resumo = ""
            for nome, dados in simulacoes.items():
                m = dados['metrics']
                os_str = f"{m.overshoot:.1f}%" if m.overshoot is not None else "Instavel"
                ts_str = f"{m.settling_time:.1f}s" if m.settling_time is not None else "Nao estabilizou"
                err_str = f"{m.steady_state_error:.3f}" if m.steady_state_error is not None else "N/A"
                resumo += f"[{nome}]: Mp={os_str}, ts={ts_str}, ess={err_str}. "

            client = genai.Client(api_key=self.api_key)
            prompt = (
                "Escreva um parecer tecnico formal e impessoal em um unico paragrafo. "
                "NAO use saudacoes ou apresentacoes em hipotese alguma. Fale de polos, zeros e estabilidade. "
                f"Planta: K={K:.2f}, tau={tau:.2f}, atraso={theta:.2f}. "
                f"Analise detalhadamente estas simulacoes de PID: {resumo}. "
                "Conclua rigorosamente qual metodo e mais seguro para instalacoes industriais baseando-se na reducao de oscilacao."
            )
            # Modelo corrigido para evitar o erro 404
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            texto_limpo = response.text.replace("Olá", "").replace("equipe", "").strip()
            return texto_limpo
        except Exception as e:
            return f"ERRO NA COMUNICACAO COM API: {str(e)}\n\n" + self._gerar_analise_estatica(simulacoes)

    def generate(self, output_path, use_ai=True):
        self.add_page()
        self.set_text_color(0, 0, 0)
        
        melhor_id = "Sundaresan" if self.controller.dados_identificacao['Sundaresan']['eqm'] < self.controller.dados_identificacao['Smith']['eqm'] else "Smith"
        K = self.controller.dados_identificacao[melhor_id]['K']
        tau = self.controller.dados_identificacao[melhor_id]['tau']
        theta = self.controller.dados_identificacao[melhor_id]['theta']

        # 1. Função de Transferência FOPDT
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '1. Funcao de Transferencia Identificada (FOPDT)', ln=True)
        self.set_font('Arial', '', 11)
        self.cell(0, 6, f"O modelo com menor Erro Quadratico foi o '{melhor_id}':", ln=True)
        self.set_font('Courier', 'B', 11)
        self.cell(0, 8, f"          {K:.4f} * e^(-{theta:.2f}s)", ln=True)
        self.cell(0, 8, f"  G(s) = --------------------", ln=True)
        self.cell(0, 8, f"             {tau:.2f}s + 1", ln=True)

        # 2. Tabela Consolidada de Sintonia e Desempenho
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '2. Tabela de Sintonia e Desempenho Transitorio', ln=True)
        self.set_font('Courier', 'B', 8)
        self.cell(0, 6, f"{'Metodo Utilizado':25} | {'Kp':7} | {'Ti':7} | {'Td':7} || {'tr(s)':8} | {'ts(s)':8} | {'Mp(%)':8}", ln=True)
        self.cell(0, 2, "-"*88, ln=True)
        
        self.set_font('Courier', '', 8)
        for nome, dados in self.controller.historico_simulacoes.items():
            pid = dados['pid']
            met = dados['metrics']
            tr = f"{met.rise_time:.2f}" if met.rise_time is not None else "N/A"
            ts = f"{met.settling_time:.2f}" if met.settling_time is not None else "N/A"
            mp = f"{met.overshoot:.2f}" if met.overshoot is not None else "N/A"
            
            self.cell(0, 6, f"{nome:25} | {pid.Kp:7.3f} | {pid.Ti:7.3f} | {pid.Td:7.3f} || {tr:8} | {ts:8} | {mp:8}", ln=True)

        # 3. Fundamentação Teórica
        self.ln(5)
        self._escrever_fundamentacao_teorica()

        # 4. Avaliação Analítica (IA ou Local)
        self.set_font('Arial', 'B', 12)
        mode = "IA Generativa" if use_ai else "Base de Conhecimento Local"
        self.cell(0, 10, f'4. Avaliacao Analitica ({mode})', ln=True)
        self.set_font('Arial', '', 10)
        
        analise = self.obter_analise_ia(self.controller.historico_simulacoes, K, tau, theta) if use_ai else self._gerar_analise_estatica(self.controller.historico_simulacoes)
        self.multi_cell(0, 5, analise)

        # 5. Apêndice com Regras Matemáticas (EXCLUSIVO para o Relatório Padrão/Local)
        if not use_ai:
            self._escrever_nota_tecnica_local()
        
        self.output(output_path)
        return True