"""
model/data_loader.py
Responsável por carregar e validar arquivos .mat com dados experimentais.
"""
import numpy as np
import scipy.io as sio

class DataLoader:
    """
    Carrega datasets no formato .mat e extrai os vetores de tempo,
    entrada (u) e saída (y) do processo.
    """

    def __init__(self):
        self.time = None
        self.input_signal = None
        self.output_signal = None
        self.metadata = {}
        self.filepath = None

    def load(self, filepath: str) -> bool:
        """
        Carrega o arquivo .mat e identifica automaticamente as variáveis.
        Retorna True se bem-sucedido. Lança exceção em caso de falha.
        """
        try:
            raw = sio.loadmat(filepath)
            data = {k: v for k, v in raw.items() if not k.startswith("__")}

            self.filepath = filepath
            self._parse_variables(data)
            self._extract_metadata(data)
            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        except Exception as e:
            raise ValueError(f"Erro ao carregar .mat: {str(e)}")

    def _parse_variables(self, data: dict):
        """
        Estratégia de parsing em duas etapas:

        1) Tenta encontrar variáveis individuais de tempo, entrada e saída
           pelos nomes mais comuns (tiempo, entrada, salida, t, u, y...).

        2) Se alguma variável vier como matriz Nx2 (coluna 0 = tempo,
           coluna 1 = sinal), extrai corretamente cada coluna.
           ATENÇÃO: col[:,0] é o TEMPO, col[:,1] é o SINAL — não confundir.
        """
        keys = list(data.keys())

        # ── Prioridade 1: variáveis individuais vetoriais ──────────────────
        # Nomes verificados no Dataset_Grupo2_c213.mat: tiempo, entrada, salida
        time_keys   = ["tiempo", "t", "time", "tempo", "T"]
        input_keys  = ["entrada", "u", "input", "U", "dados_u"]
        output_keys = ["salida", "y", "output", "saida", "Y", "ySP", "dados_y"]

        def find_flat(candidates):
            """Busca chave e retorna vetor 1D. Ignora structs (dtype=object)."""
            for c in candidates:
                if c in data:
                    val = data[c]
                    if val.dtype.names:       # struct MATLAB → ignorar
                        continue
                    if val.dtype == object:   # cell array → ignorar
                        continue
                    return val.flatten()
            return None

        self.time          = find_flat(time_keys)
        self.input_signal  = find_flat(input_keys)
        self.output_signal = find_flat(output_keys)

        # ── Prioridade 2: matrizes Nx2 (col 0 = tempo | col 1 = sinal) ────
        # Ex: dados_saida shape=(401,2) → col 0 = tempo, col 1 = sinal
        if self.output_signal is None:
            for k in ["dados_saida", "dados_output", "data_out"]:
                if k in data:
                    m = data[k]
                    if m.ndim == 2 and m.shape[1] >= 2:
                        if self.time is None:
                            self.time = m[:, 0]        # coluna 0 → tempo
                        self.output_signal = m[:, 1]   # coluna 1 → sinal
                        break

        if self.input_signal is None:
            for k in ["dados_entrada", "dados_input", "data_in"]:
                if k in data:
                    m = data[k]
                    if m.ndim == 2 and m.shape[1] >= 2:
                        self.input_signal = m[:, 1]    # coluna 1 → sinal
                        break

        # ── Prioridade 3: única chave numérica Nx2 ou Nx3 ─────────────────
        if self.time is None or self.output_signal is None:
            numeric_keys = [
                k for k in keys
                if not data[k].dtype.names
                and data[k].dtype != object
                and data[k].ndim == 2
            ]
            if len(numeric_keys) == 1:
                m = data[numeric_keys[0]]
                if m.shape[1] >= 2:
                    self.time          = m[:, 0]
                    self.output_signal = m[:, 1]
                    if m.shape[1] >= 3:
                        self.input_signal = m[:, 2]

        # ── Validação ──────────────────────────────────────────────────────
        if self.time is None or self.output_signal is None:
            raise ValueError(
                "Não foi possível identificar tempo e saída no arquivo.\n"
                f"Chaves encontradas: {keys}\n"
                "Esperado: variáveis individuais (t/tiempo/time) ou matrizes Nx2."
            )

        # Garante mesmo comprimento
        n = min(len(self.time), len(self.output_signal))
        self.time          = self.time[:n]
        self.output_signal = self.output_signal[:n]
        if self.input_signal is not None:
            self.input_signal = self.input_signal[:n]

    def _extract_metadata(self, data: dict):
        """Extrai metadados opcionais (unidades, descrição)."""
        self.metadata = {}
        for key in ["unit_time", "unit_output", "unit_input", "descricao"]:
            if key in data:
                self.metadata[key] = str(data[key])

        # Tenta extrair amplitude do degrau do struct parametros_sistema
        if "parametros_sistema" in data:
            ps = data["parametros_sistema"]
            if ps.dtype.names and "amplitud_escalon" in ps.dtype.names:
                try:
                    self.metadata["amplitud_escalon"] = float(
                        ps["amplitud_escalon"][0, 0][0, 0]
                    )
                except Exception:
                    pass

    def get_step_amplitude(self) -> float:
        """
        Retorna a amplitude do degrau de entrada.
        Prioridade: metadado do struct > max(u)-min(u) > 1.0
        """
        if "amplitud_escalon" in self.metadata:
            return float(self.metadata["amplitud_escalon"])
        if self.input_signal is not None:
            amp = float(np.max(self.input_signal) - np.min(self.input_signal))
            if amp > 1e-6:
                return amp
        return 1.0

    def is_loaded(self) -> bool:
        return self.time is not None and self.output_signal is not None

    def summary(self) -> dict:
        """Retorna resumo dos dados carregados."""
        if not self.is_loaded():
            return {}
        return {
            "n_amostras":       len(self.time),
            "t_inicial":        float(self.time[0]),
            "t_final":          float(self.time[-1]),
            "y_min":            float(np.min(self.output_signal)),
            "y_max":            float(np.max(self.output_signal)),
            "amplitude_degrau": self.get_step_amplitude(),
            "metadata":         self.metadata,
        }