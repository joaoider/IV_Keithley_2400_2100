# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 15:35:22 2020

@author: LAB MAt
"""

""" 
Programa dividido em 2
A1:
Programa para controlar temperatura do termopar frio

A2: 
Fazer curva IV
"""

""" A2 """

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # BIBLIOTECAS

import nidaqmx
import numpy as np
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
    k2400 = rm.open_resource('GPIB1::24::INSTR') # definindo Keithley2400
    k2400.write(":SOUR:FUNC VOLT")          # Select voltage source.
    k2400.write(":SOUR:VOLT:MODE FIXED")    # Fixed voltage source mode.
    k2400.write(":SOUR:VOLT:LEV %f" %voltage)        # Source output = 1V.
    k2400.write(":SENS:CURR:PROT 10E-1")    # 10mA compliance.
    k2400.write(":SENS:FUNC 'CURR'")        # Current measure function.
    k2400.write(":SENS:CURR:RANG 30E-3")     # 100mA measure range.
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


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
         # DEFININDO PARÂMETROS DA MEDIDA 

tensao_inicial = -4.0
tensao_final = 0.0 # K2100() + 0.2 # calculada pela tensão de circuito aberto + um pequeno incremento
passo = 0.05  # passo da tensão indo pra tensão inicial até tensão final
n_passos = int((tensao_final - tensao_inicial) / passo+1) # calcula o número de passos necessários pra chegar da tensão inical até a final, dado o passo
print("Número de passos: %.2f" % n_passos)
n_medidas = 1   # número de medidas feitas em cada ponto para se tomar a média (Filtro da tensão)


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
       # DEFININDO VARIÁVEIS

# valores de corrente do módulo gerador peltier
I = []

# valores de tensão do módulo gerador peltier
v = []

# faixa de tensão aplicada
t = np.linspace(tensao_inicial, tensao_final, n_passos) 


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        # PROGRAMA 
        
# aplica curva IV
for i in range(0, len(t)): # varia tensão de tensao_inicial ate tensao_final com n_passos
    I.append(K2400(t[i])) # utiliza a funcao que aplica tensao e retorna o valor de corrente, acrescido na lista de I
    v.append(K2100()) # medindo tensão pela Keithley 2100
    #v.append(t[i]) # anotando tensão aplicada pela Keithley 2400
    time.sleep(1)
    
# transforma as listas em vetores
v =- np.array(v) 
I = np.array(I)
I = I.T[0]

print(v)
print(I)

#salva os dados em um arquivo txt
salvar = np.zeros((len(v), 2))
salvar[0:len(v),0] = v
salvar[0:len(v),1] = I
nome = 'azul'
np.savetxt(nome + '.txt', salvar, header='V I')

# Plotando gráfico de corrente por tensão no módulo gerador
plt.plot(v, -I, 'k*')
plt.ylabel("I")
plt.xlabel("V (V)")
plt.title('IV Curve')
plt.show()