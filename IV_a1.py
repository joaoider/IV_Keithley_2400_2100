# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 15:05:03 2020

@author: LAB MAt
"""

""" 
Programa dividido em 2
A1:
Programa para controlar temperatura do termopar frio

A2: 
Fazer curva IV
"""

""" A1 """

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # BIBLIOTECAS

from simple_pid import PID
# import nidaqmx
import numpy as np
from pyfirmata import Arduino
import matplotlib.pyplot as plt
import time

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
      # DEFININDO FUNÇÕES
      
"""
# define função que irá ler a temperatura através da placa daq e termopares
def temperature(caminho):  
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_thrmcpl_chan(caminho)
        data = task.read()
    return np.array(data)
"""

# Definindo parâmetros Arduino Mega2560
board = Arduino("COM7") # Define a porta do Arduino no PC
pin = board.get_pin('d:10:p') # define a porta de saída do Arduino (digital:10:pwm)


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
         # DEFININDO PARÂMETROS DA MEDIDA 
         
# chama a funcao pid (proporcional, integral, derivada, valor a ser alcançado)
pid = PID(0.02, 0.04, 2.5, setpoint = 10) # peltier frio


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # DEFININDO VARIÁVEIS

starttime = time.time()
t = []

# valor de tensão a ser aplicado no peltier frio
control = []

# Lê as temperaturas através placa daq e termopares
T_cold = temperature("Dev2/ai9") # temperatura peltier frio
T_hot = temperature("Dev2/ai11") # temperatura em cima do microcontrolar

# listas para salvar valores de temperatura
T_cold1 = []
T_hot1 = []

# Listas para salvar os valores das tensões aplicadas
tensao = [] # lista de valores da tensão aplicada no peltier frio



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
    
    t.append(time.time()- starttime)
    T_cold1.append(temperature("Dev2/ai9"))
    T_hot1.append(temperature("Dev2/ai11"))
    
# Salvando dados de tensão aplicada no peltier,  temperatura e tempo
with open ("IV_T_modulos.txt", 'w') as temp:
    for t in range(len(T_cold1)):
        temp.write(str(T_cold1[t])+ " " + str(T_hot1[t]) + '\n')
    temp.close()
    
# Plotando gráfico de corrente por tensão no módulo gerador
plt.plot(np.array(t), np.array(T_cold1), 'r',label='Frio') 
plt.plot(np.array(t), np.array(T_hot1), 'k',label='Meio') 
plt.show() # mostra o gráfico

board.exit()