"""
model/pid_tuning.py
Métodos de sintonia PID para Sistemas de Controle.
"""

from dataclasses import dataclass
from enum import Enum

class TuningMethod(Enum):
    ZIEGLER_NICHOLS = "Ziegler-Nichols"
    ITAE            = "ITAE"
    CHR             = "CHR (0% Sobressinal)"
    CHR_OVERSHOOT   = "CHR (20% Sobressinal)"
    IMC             = "IMC"
    CC              = "Cohen-Coon"
    MANUAL          = "Manual"

@dataclass
class PIDParameters:
    Kp: float
    Ti: float
    Td: float
    method: str = ""

    @property
    def Ki(self) -> float: return self.Kp / self.Ti if self.Ti > 0 else 0.0

    @property
    def Kd(self) -> float: return self.Kp * self.Td

class ZieglerNicholsTuning:
    def tune(self, K: float, tau: float, theta: float) -> PIDParameters:
        Kp = 1.2 * tau / (K * theta)
        return PIDParameters(Kp=Kp, Ti=2.0 * theta, Td=0.5 * theta, method="Ziegler-Nichols")

class ITAETuning:
    def tune(self, K: float, tau: float, theta: float) -> PIDParameters:
        phi = theta / tau
        Kp = (0.965 / K) * (phi ** -0.855)
        Ti = max(tau / (0.796 - 0.1465 * phi), 1e-6)
        Td = max(0.308 * tau * (phi ** 0.929), 0.0)
        return PIDParameters(Kp=Kp, Ti=Ti, Td=Td, method="ITAE")

class CHRTuning:
    def tune(self, K: float, tau: float, theta: float, overshoot: bool = False) -> PIDParameters:
        if overshoot:
            return PIDParameters(Kp=(0.95 * tau) / (K * theta), Ti=1.35 * tau, Td=0.47 * theta, method="CHR (20% Sobressinal)")
        return PIDParameters(Kp=(0.6 * tau) / (K * theta), Ti=1.0 * tau, Td=0.5 * theta, method="CHR (0% Sobressinal)")

class IMCTuning:
    def tune(self, K: float, tau: float, theta: float, lambda_imc: float) -> PIDParameters:
        if lambda_imc <= 0: lambda_imc = max(0.1 * tau, 0.8 * theta)
        Kp = (tau + 0.5 * theta) / (K * (lambda_imc + 0.5 * theta))
        Ti = tau + 0.5 * theta
        Td = (tau * theta) / (2 * tau + theta)
        return PIDParameters(Kp=Kp, Ti=Ti, Td=Td, method=f"IMC (λ={lambda_imc:.2f})")

class CohenCoonTuning:
    def tune(self, K: float, tau: float, theta: float) -> PIDParameters:
        phi = theta / tau
        Kp = (1.35 / K) * ((1 / phi) + 0.185)
        Ti = theta * ((2.5 + 3.1 * phi) / (1 + 1.03 * phi))
        Td = (0.37 * theta) / (1 + 0.19 * phi)
        return PIDParameters(Kp=Kp, Ti=Ti, Td=Td, method="Cohen-Coon")

class PIDTuner:
    def __init__(self):
        self._zn = ZieglerNicholsTuning()
        self._itae = ITAETuning()
        self._chr = CHRTuning()
        self._imc = IMCTuning()
        self._cc = CohenCoonTuning()

    def tune(self, method: TuningMethod, K: float, tau: float, theta: float, 
             Kp_manual: float = 1.0, Ti_manual: float = 1.0, Td_manual: float = 0.0, lambda_imc: float = 1.0) -> PIDParameters:
        
        if method == TuningMethod.ZIEGLER_NICHOLS: return self._zn.tune(K, tau, theta)
        elif method == TuningMethod.ITAE: return self._itae.tune(K, tau, theta)
        elif method == TuningMethod.CHR: return self._chr.tune(K, tau, theta, overshoot=False)
        elif method == TuningMethod.CHR_OVERSHOOT: return self._chr.tune(K, tau, theta, overshoot=True)
        elif method == TuningMethod.IMC: return self._imc.tune(K, tau, theta, lambda_imc=lambda_imc)
        elif method == TuningMethod.CC: return self._cc.tune(K, tau, theta)
        elif method == TuningMethod.MANUAL: return PIDParameters(Kp=Kp_manual, Ti=Ti_manual, Td=Td_manual, method="Manual")
        raise ValueError(f"Método desconhecido: {method}")

    def available_methods(self) -> list:
        return list(TuningMethod)