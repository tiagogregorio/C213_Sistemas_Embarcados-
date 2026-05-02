"""
model/simulator.py
Simula a resposta do sistema em malha fechada com controlador PID
e calcula as métricas de desempenho (tr, ts, Mp, ess).
"""
import numpy as np
import control
from dataclasses import dataclass
from typing import Optional

from model.pid_tuning import PIDParameters
from model.identification import FOPDTModel

@dataclass
class ResponseMetrics:
    """Métricas de desempenho da resposta ao degrau em malha fechada."""
    rise_time: Optional[float]       # tr  — tempo de subida (10% → 90%)
    settling_time: Optional[float]   # ts  — tempo de acomodação (±2%)
    overshoot: Optional[float]       # Mp  — sobressinal (%)
    steady_state_error: float        # ess — erro em regime permanente
    peak_value: float                # valor de pico da resposta
    peak_time: Optional[float]       # instante do pico

    def __str__(self):
        tr  = f"{self.rise_time:.3f}s"   if self.rise_time   is not None else "—"
        ts  = f"{self.settling_time:.3f}s" if self.settling_time is not None else "—"
        Mp  = f"{self.overshoot:.2f}%"  if self.overshoot   is not None else "—"
        return (
            f"tr={tr}  ts={ts}  Mp={Mp}  ess={self.steady_state_error:.4f}"
        )


class ClosedLoopSimulator:
    """
    Simula a resposta ao degrau de um sistema FOPDT em malha fechada
    com controlador PID usando a biblioteca python-control.

    Estrutura de controle:
        R(s) ──►[C(s)]──►[G(s)]──► Y(s)
                   ▲__________________|
                         feedback unitário
    """

    def simulate(
        self,
        model: FOPDTModel,
        pid: PIDParameters,
        setpoint: float = 1.0,
        t_end: float = None,
        n_points: int = 1000,
    ) -> tuple:
        """
        Executa a simulação em malha fechada.

        Parâmetros
        ----------
        model    : parâmetros FOPDT identificados (K, tau, theta)
        pid      : parâmetros do controlador PID (Kp, Ti, Td)
        setpoint : amplitude do degrau de referência
        t_end    : tempo final (estimado automaticamente se None)
        n_points : número de pontos de tempo

        Retorna
        -------
        (time, output) — vetores numpy
        """
        if t_end is None:
            # Tempo suficiente para ver pelo menos 5 constantes de tempo
            t_end = max(10 * (model.tau + model.theta), 60.0)

        time = np.linspace(0, t_end, n_points)

        # Planta FOPDT com aproximação de Padé para o atraso
        G = self._build_plant(model)

        # Controlador PID em forma paralela
        C = self._build_pid(pid)

        # Malha fechada com realimentação unitária: Y/R = C*G / (1 + C*G)
        open_loop   = C * G
        closed_loop = control.feedback(open_loop, 1)

        # Resposta ao degrau (setpoint * sistema)
        t_out, y_out = control.step_response(setpoint * closed_loop, T=time)

        return t_out, y_out

    # ── Construtores de funções de transferência ──────────────────────────

    def _build_plant(self, model: FOPDTModel):
        """
        Constrói G(s) = K / (tau*s + 1) com atraso e^(-theta*s)
        aproximado por Padé de 2ª ordem.
        """
        G = control.tf([model.K], [model.tau, 1.0])

        if model.theta > 1e-6:
            pade_num, pade_den = control.pade(model.theta, n=2)
            G = G * control.tf(pade_num, pade_den)

        return G

    def _build_pid(self, pid: PIDParameters):
        """
        Constrói o controlador PID como função de transferência:

            C(s) = Kp * (1 + 1/(Ti*s) + Td*s)
                 = Kp * (Ti*Td*s² + Ti*s + 1) / (Ti*s)

        Numerador : [Kp*Ti*Td,  Kp*Ti,  Kp]
        Denominador: [Ti,  0]
        """
        Kp, Ti, Td = pid.Kp, pid.Ti, pid.Td

        # Protege contra Ti muito pequeno (evita divisão por zero)
        Ti = max(Ti, 1e-6)

        num = [Kp * Ti * Td,  Kp * Ti,  Kp]
        den = [Ti, 0.0]

        return control.tf(num, den)

    # ── Cálculo de métricas ───────────────────────────────────────────────

    def compute_metrics(
        self,
        time: np.ndarray,
        output: np.ndarray,
        setpoint: float = 1.0,
        tolerance: float = 0.02,
    ) -> ResponseMetrics:
        """
        Calcula as métricas de desempenho da resposta ao degrau.

        Parâmetros
        ----------
        time      : vetor de tempo da simulação
        output    : vetor de saída simulada
        setpoint  : valor de referência (amplitude do degrau)
        tolerance : faixa de acomodação em fração (padrão = 0.02 → ±2%)

        Retorna
        -------
        ResponseMetrics com tr, ts, Mp, ess, peak_value, peak_time
        """
        y_ref = float(setpoint)
        band  = tolerance * abs(y_ref)

        # ── Tempo de subida (10% → 90%) ───────────────────────────────────
        t10 = self._first_crossing(time, output, 0.10 * y_ref)
        t90 = self._first_crossing(time, output, 0.90 * y_ref)
        rise_time = (t90 - t10) if (t10 is not None and t90 is not None) else None

        # ── Sobressinal (overshoot) ────────────────────────────────────────
        peak_idx   = int(np.argmax(output))
        peak_value = float(output[peak_idx])
        peak_time  = float(time[peak_idx])
        overshoot  = max(0.0, (peak_value - y_ref) / abs(y_ref) * 100.0)

        # ── Tempo de acomodação (último instante fora da banda ±2%) ───────
        outside = np.where(np.abs(output - y_ref) > band)[0]
        if len(outside) > 0:
            last_out = int(outside[-1])
            settling_time = float(time[last_out + 1]) if last_out + 1 < len(time) else None
        else:
            # Nunca saiu da banda → acomodação imediata (sem sobressinal)
            inside = np.where(np.abs(output - y_ref) <= band)[0]
            settling_time = float(time[inside[0]]) if len(inside) > 0 else None

        # ── Erro em regime permanente (média dos últimos 5% de pontos) ────
        n_tail = max(10, len(output) // 20)
        y_ss   = float(np.mean(output[-n_tail:]))
        ess    = abs(y_ref - y_ss)

        return ResponseMetrics(
            rise_time=rise_time,
            settling_time=settling_time,
            overshoot=overshoot,
            steady_state_error=ess,
            peak_value=peak_value,
            peak_time=peak_time,
        )

    def _first_crossing(
        self,
        time: np.ndarray,
        output: np.ndarray,
        level: float,
    ) -> Optional[float]:
        """Retorna o instante em que output cruza 'level' pela primeira vez."""
        idx_arr = np.where(output >= level)[0]
        if len(idx_arr) == 0:
            return None

        i = int(idx_arr[0])
        if i > 0:
            y0, y1 = float(output[i - 1]), float(output[i])
            t0, t1 = float(time[i - 1]),   float(time[i])
            if y1 != y0:
                return t0 + (level - y0) * (t1 - t0) / (y1 - y0)

        return float(time[i])