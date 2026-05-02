from scipy.io import loadmat
import matplotlib.pyplot as plt
from model.identification import SmithIdentification

# 🔥 Carregar direto (sem DataLoader)
data = loadmat("data/Dataset_Grupo2_c213.mat")

t = data["tiempo"].flatten()
u = data["entrada"].flatten()
y = data["salida"].flatten()

print("y0:", y[0])
print("y final:", y[-1])

plt.plot(t, y, label="Saída")
plt.plot(t, u, label="Entrada")
plt.legend()
plt.grid()
plt.show()

# 🔥 Identificação
step = max(u) - min(u)

smith = SmithIdentification()
model = smith.identify(t, y, step)

print("\nModelo identificado:")
print(model)