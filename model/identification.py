"""
model/identification.py
Identificação do modelo FOPDT pelos Métodos de Smith e Sundaresan.

Modelo FOPDT:
    G(s) = K * exp(-theta * s) / (tau * s + 1)
"""
import numpy as np
from dataclasses import dataclass

@dataclass
class FOPDTModel:
    """Representa os parâmetros identificados do modelo FOPDT."""
    K: float
    tau: float
    theta: float
    eqm: float = 0.0
    method: str = ""

    def __str__(self):
        return (
            f"[{self.method}] K={self.K:.4f}  τ={self.tau:.4f}s  "
            f"θ={self.theta:.4f}s  EQM={self.eqm:.6f}"
        )

class _BaseIdentification:
    """Classe base com utilitários compartilhados entre os métodos."""

    def _compute_gain(self, output, step_amplitude, y0=None):
        if y0 is None:
            y0 = float(output[0])
        y_ss = float(np.mean(output[-10:]))
        delta_y = y_ss - y0
        if abs(delta_y) < 1e-10:
            raise ValueError("Variação de saída muito pequena. Verifique o dataset.")
        return float(output[0]), y_ss, delta_y, delta_y / step_amplitude

    def _time_at_fraction(self, time, y_norm, fraction):
        """Retorna o instante (com interpolação linear) em que y_norm >= fraction."""
        indices = np.where(y_norm >= fraction)[0]
        if len(indices) == 0:
            return None
        idx = indices[0]
        if idx > 0:
            y_prev, y_curr = y_norm[idx - 1], y_norm[idx]
            t_prev, t_curr = time[idx - 1],   time[idx]
            if y_curr != y_prev:
                return t_prev + (fraction - y_prev) * (t_curr - t_prev) / (y_curr - y_prev)
        return float(time[idx])

    def _simulate_fopdt(self, time, K, tau, theta, step_amplitude, y0):
        """Simula a resposta ao degrau do modelo FOPDT."""
        y = np.full_like(time, y0, dtype=float)
        mask = time >= theta
        y[mask] = y0 + K * step_amplitude * (1.0 - np.exp(-(time[mask] - theta) / tau))
        return y

    def get_model_response(self, time, model: FOPDTModel, step_amplitude=1.0, y0=0.0):
        """Gera a curva do modelo identificado para plotagem."""
        return self._simulate_fopdt(
            time, model.K, model.tau, model.theta, step_amplitude, y0
        )

class SmithIdentification(_BaseIdentification):
    """
    Método de Smith para identificação de sistemas FOPDT.

    Usa os instantes em que a saída normalizada atinge 28.3% e 63.2%:
        tau   = 1.5 * (t2 - t1)
        theta = t1 - 0.5 * tau

    Referência: Smith, C. L. (1972). Digital Computer Process Control.
    """

    def identify(self, time, output, step_amplitude=1.0) -> FOPDTModel:
        y0, y_ss, delta_y, K = self._compute_gain(output, step_amplitude)
        y_norm = (output - y0) / delta_y

        t1 = self._time_at_fraction(time, y_norm, 0.283)
        t2 = self._time_at_fraction(time, y_norm, 0.632)

        if t1 is None or t2 is None:
            raise ValueError(
                "Não foi possível encontrar os pontos 28.3% e 63.2%.\n"
                "Verifique se o sistema atingiu o regime permanente."
            )

        tau   = 1.5 * (t2 - t1)
        theta = t1 - 0.5 * tau
        tau   = max(tau,   1e-6)
        theta = max(theta, 0.0)

        y_model = self._simulate_fopdt(time, K, tau, theta, step_amplitude, y0)
        eqm     = float(np.mean((output - y_model) ** 2))

        return FOPDTModel(K=K, tau=tau, theta=theta, eqm=eqm, method="Smith")

class SundaresanIdentification(_BaseIdentification):
    """
    Método de Sundaresan & Krishnaswamy para identificação de sistemas FOPDT.

    Usa os instantes em que a saída normalizada atinge 35.3% e 85.3%:
        tau   = 0.67 * (t2 - t1)
        theta = 1.3*t1 - 0.29*t2

    Referência:
        Sundaresan & Krishnaswamy (1978). Estimation of time delay parameters
        in linear systems. Ind. Eng. Chem. Process Des. Dev.
    """

    def identify(self, time, output, step_amplitude=1.0) -> FOPDTModel:
        y0, y_ss, delta_y, K = self._compute_gain(output, step_amplitude)
        y_norm = (output - y0) / delta_y

        t1 = self._time_at_fraction(time, y_norm, 0.353)
        t2 = self._time_at_fraction(time, y_norm, 0.853)

        if t1 is None or t2 is None:
            raise ValueError(
                "Não foi possível encontrar os pontos 35.3% e 85.3%.\n"
                "Verifique se o sistema atingiu o regime permanente."
            )

        tau   = 0.67  * (t2 - t1)
        theta = 1.3*t1 - 0.29*t2
        tau   = max(tau,   1e-6)
        theta = max(theta, 0.0)

        y_model = self._simulate_fopdt(time, K, tau, theta, step_amplitude, y0)
        eqm     = float(np.mean((output - y_model) ** 2))

        return FOPDTModel(K=K, tau=tau, theta=theta, eqm=eqm, method="Sundaresan")