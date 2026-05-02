from model.data_loader import DataLoader
from model.identification import SmithIdentification

loader = DataLoader()
loader.load("data/Dataset_Grupo2_c213.mat")

t = loader.time
u = loader.input_signal
y = loader.output_signal

#  IMPORTANTE: usar amplitude real
step = loader.get_step_amplitude()

smith = SmithIdentification()
model = smith.identify(t, y, step)

print("Parâmetros identificados:")
print(model)