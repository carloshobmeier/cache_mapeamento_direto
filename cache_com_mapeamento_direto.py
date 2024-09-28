
from colorama import Fore, Style, init
init(autoreset=True)


################################################################
# PARTE PROFESSOR (sem alterações)

import math

class IO:
    def output(self, s):
        print(s, end='')

    def input(self, prompt):
        return input(prompt)


# Exceção (erro)
class EnderecoInvalido(Exception):
    def __init__(self, ender):
        self.ender = ender

class Memoria:
    def __init__(self, tam):
        self.tamanho = tam

    def capacidade(self):
        return self.tamanho

    def verifica_endereco(self, ender):
        if (ender < 0) or (ender >= self.tamanho):
            raise EnderecoInvalido(ender)


class RAM(Memoria):
    def __init__(self, k):
        Memoria.__init__(self, 2**k)
        self.memoria = [0] * self.tamanho

    def read(self, ender):
        self.verifica_endereco(ender)
        return self.memoria[ender]

    def write(self, ender, val):
        self.verifica_endereco(ender)
        self.memoria[ender] = val


class CPU:
    def __init__(self, mem, io):
        self.mem = mem
        self.io = io
        self.PC = 0                    # program counter
        self.A = self.B = self.C = 0   # registradores auxiliares

    def run(self, ender):
        self.PC = ender
        # lê "instrução" no endereço PC
        self.A = self.mem.read(self.PC)
        self.PC += 1
        self.B = self.mem.read(self.PC)
        self.PC += 1

        self.C = 1
        while self.A <= self.B:
            self.mem.write(self.A, self.C)
            self.io.output(f"{self.A} -> {self.C}\n")
            self.C += 1
            self.A += 1


class CacheSimples(Memoria):
    def __init__(self, kc, ram):
        Memoria.__init__(self, ram.capacidade())
        self.ram = ram
        self.cache_sz = 2**kc
        self.dados = [0] * self.cache_sz
        self.bloco = -1
        self.modif = False

    def read(self, ender):
        if self.cache_hit(ender):
            print("cache hit:", ender)
        else:
            print("cache miss:", ender)
            bloco_ender = int(ender/self.cache_sz)
            if self.modif:
                # update ram
                for i in range(self.cache_sz):
                    self.ram.write(bloco_ender * self.cache_sz + i, self.dados[i])
            # update cache
            for i in range(self.cache_sz):
                self.dados[i] = self.ram.read(bloco_ender * self.cache_sz + i)
            self.bloco = bloco_ender
            self.modif = False
        return self.dados[ender % self.cache_sz]

    def write(self, ender, val):
        if self.cache_hit(ender):
            print("cache hit:", ender)
        else:
            print("cache miss:", ender)

            # complete!
            # ...

        self.dados[ender % self.cache_sz] = val
        self.modif = True

    def cache_hit(self, ender):
        bloco_ender = int(ender/self.cache_sz)
        return bloco_ender == self.bloco

###########################################################################



# MINHA PARTE (cache com mapeamento direto)

class Cache:
    def __init__(self, tam_cache, tam_cacheline, ram):
        self.ram = ram

        self.tam_cache = 2 ** tam_cache
        self.tam_cacheline = 2 ** tam_cacheline
        self.qtd_cachelines = int(self.tam_cache / self.tam_cacheline)

        self.cachelines = [{'tag': None, 'dados': [0] * self.tam_cacheline, 'modificada': False} for _ in range(self.qtd_cachelines)]
 
        self.bits_indexar_colunas = tam_cacheline
        self.bits_indexar_linhas = int(math.log(self.qtd_cachelines, 2))


    # Isolando os componentes
    def mascara_para_bitwise(self, num_bits):
        return (1 << num_bits) - 1

    def obter_w(self, endereco):
        return endereco & self.mascara_para_bitwise(self.bits_indexar_colunas)

    def obter_r(self, endereco):
        return (endereco >> self.bits_indexar_colunas) & self.mascara_para_bitwise(self.bits_indexar_linhas)

    def obter_t(self, endereco):
        return endereco >> (self.bits_indexar_colunas + self.bits_indexar_linhas)

    def obter_s(self, endereco):
        return endereco >> self.bits_indexar_colunas


    # Lógica atualização das memórias
    def trazer_da_ram(self, s, r):
        cacheline = self.cachelines[r]
        comeco_linhas = s * self.tam_cacheline
        for i in range(self.tam_cacheline):
            cacheline['dados'][i] = self.ram.read(comeco_linhas + i)

    def atualizar_modificação_na_ram(self, s, r):
        cacheline = self.cachelines[r]
        comeco_linhas = s * self.tam_cacheline
        for i in range(self.tam_cacheline):
            self.ram.write(comeco_linhas + i, cacheline['dados'][i])

    
    # Lógica das operações com a RAM
    def read(self, endereco):
        w = self.obter_w(endereco)
        r = self.obter_r(endereco)
        t = self.obter_t(endereco)
        s = self.obter_s(endereco)
        
        cacheline = self.cachelines[r]
        if cacheline['tag'] == t:
            print(f"{Fore.GREEN}\nCache HIT: {endereco}")
        else:
            print(f"{Fore.RED}\nCache MISS: {endereco}")
            if cacheline['modificada']:
                self.atualizar_modificação_na_ram(s, r)
            self.trazer_da_ram(s, r)
            cacheline['tag'] = t
            cacheline['modificada'] = False
        return cacheline['dados'][w]

    def write(self, endereco, valor):
        w = self.obter_w(endereco)
        r = self.obter_r(endereco)
        t = self.obter_t(endereco)
        s = self.obter_s(endereco)
        
        cacheline = self.cachelines[r]
        if cacheline['tag'] == t:
            print(f"{Fore.GREEN}\nCache HIT: {endereco}")
        else:
            print(f"{Fore.RED}\nCache MISS: {endereco}")
            if cacheline['modificada']:
                self.atualizar_modificação_na_ram(s, r)
            self.trazer_da_ram(s, r)
            cacheline['tag'] = t
            cacheline['modificada'] = False
        cacheline['dados'][w] = valor
        cacheline['modificada'] = True


######################################################################


# PROGRAMA PRINCIPAL

try:
    io = IO()
    ram = RAM(12)   # 4K de RAM (2**12)
    cache = Cache(7, 4, ram) # total cache = 128 (2**7), cacheline = 16 (2**4)
    cpu = CPU(cache, io)

    inicio = 0
    ram.write(inicio, 110)
    ram.write(inicio+1, 130)
    cpu.run(inicio)
except EnderecoInvalido as e:
    print("Endereco inválido:", e.ender)
