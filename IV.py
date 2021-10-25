# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 12:14:23 2020

@author: LAB MAt
"""

"""
Programa para fazer curva IV do módulo peltier, gerador termoelétrico
manter temperatura quente utilizando 'Microcomputer temperature controller' UY-D220V
manter temperatura fria através do controle pid de um outro peltier acima ligado na água
"""

""" Ligar controlador de temperatura quente manualmente e fixar temperatura """

""" fazer comando para medir temperatura quente através de um termopar """

"""controlar temperatura fria com pid"""


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # BIBLIOTECAS

from simple_pid import PID
import nidaqmx
import numpy as np
from pyfirmata import Arduino
import matplotlib.pyplot as plt
import time
import pyvisa as visa

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
      # DEFININDO FUNÇÕES

# Definida função que usará Keithley 2100 usada para medir tensão
def K2100():
    rm = visa.ResourceManager()
    k2100 = rm.open_resource('USB0::0x05E6::0x2100::1194579::INSTR')
    k2100.write('*CLS')
    voltage = float(k2100.query('MEASure:VOLTage:DC?'))
    print(voltage)
    return voltage

# define função que irá ler a temperatura através da placa daq e termopares
def temperature(caminho):  
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_thrmcpl_chan(caminho)
        data = task.read()
    return np.array(data)

# Definida função que usará Keithley 2400 usada para aplicar tensão nos dois pontos externos, de onde se lerá a corrente
def K2400(voltage):
    rm = visa.ResourceManager()
    rm.list_resources()
    k2400 = rm.open_resource('GPIB0::24::INSTR') # definindo Keithley2400
    k2400.write(":SOUR:FUNC VOLT")          # Select voltage source.
    k2400.write(":SOUR:VOLT:MODE FIXED")    # Fixed voltage source mode.
    k2400.write(":SOUR:VOLT:LEV %f" %voltage)        # Source output = 1V.
    k2400.write(":SENS:CURR:PROT 10E-1")    # 10mA compliance.
    k2400.write(":SENS:FUNC 'CURR'")        # Current measure function.
    k2400.write(":SENS:CURR:RANG 10E-2")     # 10mA measure range.
    k2400.write(":FORM:ELEM CURR")          # Current reading only.
    k2400.write(":OUTP ON")                 # Output on before measuring.
    k2400.query(":READ?")                   #coletar informação da fonte
    current = k2400.query_ascii_values(":FETC?")
    print(current)
    return current

# Define função para reiniciar Keithley 2400, passo necessário
def reset2400():
    rm = visa.ResourceManager()
    rm.list_resources()
    k2400 = rm.open_resource('GPIB0::24::INSTR') # definindo Keithley2400
    k2400.write("*RST") # reseta Keithley2400  # Restore GPIB defaults.

# Definindo parâmetros Arduino
board = Arduino("COM11") # Define a porta do Arduino no PC
pin = board.get_pin('d:10:p') # define a porta de saída do Arduino (digital:10:pwm)

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
         # DEFININDO PARÂMETROS DA MEDIDA 

tensao_inicial = -1.
tensao_final = K2100() + 0.1 # calculada pela tensão de circuito aberto + um pequeno incremento
passo = 0.5  # passo da tensão indo pra tensão inicial até tensão final
n_passos = int((tensao_final - tensao_inicial) / passo+1) # calcula o número de passos necessários pra chegar da tensão inical até a final, dado o passo
print("Número de passos: %.2f" % n_passos)
n_medidas = 1   # número de medidas feitas em cada ponto para se tomar a média (Filtro da tensão)

# chama a funcao pid (proporcional, integral, derivada, valor a ser alcançado)
pid = PID(0.02, 0.04, 2.5, setpoint = 10) # peltier frio


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # DEFININDO VARIÁVEIS

# valor de tensão a ser aplicado no peltier frio
control = []

# Lê as temperaturas através placa daq e termopares
T_cold = temperature("Dev2/ai9") # temperatura peltier frio
T_hot = temperature("Dev2/ai11") # temperatura em cima do microcontrolar

# listas para salvar valores de temperatura
T_cold1 = []
T_hot1 = []

# valores de corrente do módulo gerador peltier
I = []

# valores de tensão do módulo gerador peltier
v = []

# Listas para salvar os valores das tensões aplicadas
tensao = [] # lista de valores da tensão aplicada no peltier frio

# faixa de tensão aplicada
t = np.linspace(tensao_inicial, tensao_final, n_passos)   

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        # PROGRAMA
     
# roda pid
while True:
    control = - pid(T_cold) # lê a tensão que se deve aplicar calculado pela biblioteca pid para esfriar (por isso sinal negativo)
    tensao.append(control) # adiciona o valor de tensão aplicada no peltier quente a uma lista
    # transforma o valor de tensão de saída para o valor que irá ser aplicado pelo arduino
    control1 =  7*10**(-6)*(control)**5 - 0.0001*(control)**4 + 0.001*(control)**3 - 0.0018*(control)**2 + 0.0178*(control)
    # se der valor negativo é pq está acima (hot) ou abaixo (cold) do desejado, como arduino não solta valores negativos, zeramos
    if control1 < 0:
        control1 = 0
    if control1 > 10:
        control1 = 10
        
    pin.write(control1) # aplica tensão no pino quente, arduino
    board.pass_time(1) # aguarda para fazer proxima aplicação. comando necessário para não zerar a saída do arduino a cada aplicação
    
    T_cold1.append(temperature("Dev2/ai9"))
    T_hot1.append(temperature("Dev2/ai11"))
    
# Salvando dados de tensão aplicada no peltier,  temperatura e tempo
with open ("IV_T_modulos.txt", 'w') as temp:
    for t in range(len(T_cold1)):
        temp.write(str(T_cold1[t])+ " " + str(T_hot1[t]) + '\n')
    temp.close()

# aplica curva IV
for i in range(0, len(t)): # varia tensão de tensao_inicial ate tensao_final com n_passos
    I.append(K2400(t[i])) # utiliza a funcao que aplica tensao e retorna o valor de corrente, acrescido na lista de I
    v.append(t[i])
    time.sleep(1)
    
# transforma as listas em vetores
v = np.array(v) 
I = np.array(I)

print(v)
print(I)

#salva os dados em um arquivo txt
salvar = np.zeros((len(v), 2))
salvar[0:len(v),0] = v
salvar[0:len(I),1] = I
nome = 'IV_modulos'
np.savetxt(nome + '.txt', salvar, header='V I')

# Plotando gráfico de corrente por tensão no módulo gerador
plt.plot(v, I, 'k*')
plt.ylabel("I")
plt.xlabel("V (V)")
plt.title('IV Curve')
plt.show()

board.exit()