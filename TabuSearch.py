from random import randint
import networkx as nx
import numpy as np

def ler_grafo(filename):
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()

    header = lines.pop(0).strip().split(' ')
    p = int(header[2])
    G = nx.Graph()
    for line in lines:
        edge = line.strip().split( ' ' )
        vi = int(edge[0])-1
        vj = int(edge[1])-1
        custo = int(edge[2])
        edge = (vi,vj)
            
        G.add_edge(*edge, weight=custo)
   
    distancias = nx.floyd_warshall(G)
    file.close()
    return G, p, distancias


class TabuSearch:
    def __init__(self, filename):
        self.G, self.p, self.distancias = ler_grafo(filename)

        self.inicializarVariaveis()

    def inicializarVariaveis(self):
        self.iteracoes_maximas     = max(2*self.G.number_of_nodes(), 100)
        self.iteracoes_estaveis  = round(0.2 * self.iteracoes_maximas)
        self.iteracao          = 0
        self.melhor_solucao      = float('inf')
        self.slack              = 0
        self.adicionar_tempo           = [ float('-inf') for x in self.G.nodes() ]
        self.freq               = [ 0 for x in self.G.nodes() ]
        self.S                  = set()
        self.NS                 = set( [x for x in self.G.nodes()] )
        self.k                  = max(self.distancias)
        self.ultima_melhora   = self.iteracao
        self.tempo_tabu          = randint(1,self.p+1)
    
    def generateStartingSolution(self):
        while len(self.S) < self.p:
            #print('Generating', len(self.S))
            self.melhor_solucao = self.ADD()
            #print(self.melhor_solucao)


    def avaliar(self, v_candidate, m_type):
        if m_type == 'ADD':
            self.S.add(v_candidate)
            self.NS.remove(v_candidate)
        else:
            self.S.remove(v_candidate)
            self.NS.add(v_candidate)

        custo = 0    
        for v_ns in self.NS:
            distancia_minima = float('inf')
            closest_facility = 0
            for v_s in self.S:
                if self.distancias[v_ns][v_s] < distancia_minima:
                    distancia_minima = self.distancias[v_ns][v_s]
                    closest_facility = v_s
            
            if distancia_minima != float('inf'):
                if m_type == 'ADD':
                    custo += self.distancias[v_ns][closest_facility] + self.k * self.freq[v_ns]
                else:
                    custo += self.distancias[v_ns][closest_facility]
                
        if m_type == 'ADD':
            self.S.remove(v_candidate)
            self.NS.add(v_candidate)
        else:
            self.S.add(v_candidate)
            self.NS.remove(v_candidate)
        
        return custo


    def isTabu(self, v):
        if self.adicionar_tempo[v] == float('-inf'):
            return False
    
        return self.adicionar_tempo[v] >= self.iteracao - self.tempo_tabu

    def flip_coin(self):
        return np.random.random() < 0.5
    
    def ADD(self):
        nova_solucao = float('inf')
        best_candidate = -1
        for v in self.NS:
            if self.isTabu(v):
                continue
            valor = self.avaliar(v, 'ADD')
            if valor < nova_solucao:
                nova_solucao = valor
                best_candidate = v
                
        if best_candidate >= 0:
            self.adicionar_tempo[best_candidate] = self.iteracao
            self.S.add(best_candidate)
            self.NS.remove(best_candidate)
            
        return nova_solucao

    def aspirationCriteria(self,v,valor):
        return valor < self.melhor_solucao

    def DROP(self):
        nova_solucao = float('inf')
        best_candidate = -1

        for v in self.S:
            valor = self.avaliar(v, 'DROP')
            if ( not self.isTabu(v) or self.aspirationCriteria(v,valor) ) and valor < nova_solucao:
                nova_solucao = valor
                best_candidate = v
        
        if best_candidate >= 0:
            self.NS.add(best_candidate)
            self.S.remove(best_candidate)

        return nova_solucao

    def chooseMove(self):
        if len(self.S) < self.p - self.slack:
            return self.ADD()
        elif len(self.S) > self.p + self.slack:
            return self.DROP()
        elif self.flip_coin() and len(self.S) > 0:
            return self.DROP()
        else:
            return self.ADD()

    def run(self):
        while self.iteracao < self.iteracoes_maximas:
            nova_solucao = self.chooseMove()
            self.iteracao += 1
            if len(self.S) == self.p and nova_solucao < self.melhor_solucao:
                self.melhor_solucao = nova_solucao
                self.slack = 0
                self.ultima_melhora = self.iteracao
                #print('Improvement!', self.melhor_solucao)
            elif self.iteracao - self.ultima_melhora == self.iteracoes_estaveis * 2:
                self.slack += 1
                #print('Increasing Slack')
            if self.iteracao - self.ultima_melhora == round(self.iteracoes_estaveis / 2):
                self.tempo_tabu = randint(1,self.p+1)
                #print('Changing tempo_tabu')
            if len(self.S) == self.p and self.iteracao - self.ultima_melhora == self.iteracoes_estaveis:
                self.iteracao = self.iteracoes_maximas
            else:
                self.iteracao = self.iteracao + 1

        return self.melhor_solucao, self.S
