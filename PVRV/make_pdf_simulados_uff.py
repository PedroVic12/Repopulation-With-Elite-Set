from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from sympy import symbols, Eq, solve, simplify, expand, factor, latex
from sympy.parsing.sympy_parser import parse_expr
import math

#pip install reportlab sympy

class FormulaManager:
    """Classe para gerenciar fórmulas matemáticas usando SymPy"""
    
    def __init__(self):
        # Definir símbolos comuns
        self.F, self.k, self.q1, self.q2, self.r = symbols('F k q1 q2 r')
        self.E, self.Q = symbols('E Q')
        self.V = symbols('V')
        self.phi, self.epsilon_0 = symbols('phi epsilon_0')
        self.B, self.v, self.mu_0, self.I = symbols('B v mu_0 I')
        self.L, self.N = symbols('L N')
        self.t, self.dt = symbols('t dt')
        
        # Símbolos para circuitos digitais
        self.A, self.B = symbols('A B')
        self.tpd, self.tpd1, self.tpd2, self.tpdn = symbols('tpd tpd1 tpd2 tpdn')
        self.IOL, self.IIL = symbols('IOL IIL')
        self.VOH, self.VIH = symbols('VOH VIH')
        self.tsetup, self.tclk, self.tcomb, self.tskew = symbols('tsetup tclk tcomb tskew')
        self.thold = symbols('thold')
        
        self.setup_formulas()
    
    def setup_formulas(self):
        """Configurar todas as fórmulas"""
        self.formulas_em = {
            "Lei de Coulomb": {
                "formula": Eq(self.F, self.k * self.q1 * self.q2 / (self.r**2)),
                "descricao": "Força entre duas cargas pontuais",
                "unidades": "F (N), k (N⋅m²/C²), q (C), r (m)"
            },
            "Campo Elétrico": {
                "formula": Eq(self.E, self.k * self.Q / (self.r**2)),
                "descricao": "Campo elétrico de uma carga pontual",
                "unidades": "E (N/C), k (N⋅m²/C²), Q (C), r (m)"
            },
            "Potencial Elétrico": {
                "formula": Eq(self.V, self.k * self.Q / self.r),
                "descricao": "Potencial elétrico de uma carga pontual",
                "unidades": "V (V), k (N⋅m²/C²), Q (C), r (m)"
            },
            "Lei de Gauss": {
                "formula": Eq(self.phi, self.Q / self.epsilon_0),
                "descricao": "Fluxo elétrico através de superfície fechada",
                "unidades": "Φ (N⋅m²/C), Q (C), ε₀ (C²/N⋅m²)"
            },
            "Força de Lorentz": {
                "formula": Eq(self.F, self.q1 * (self.E + self.v * self.B)),
                "descricao": "Força em carga em movimento em campo E e B",
                "unidades": "F (N), q (C), E (N/C), v (m/s), B (T)"
            },
            "Lei de Ampère": {
                "formula": Eq(self.B * 2 * math.pi * self.r, self.mu_0 * self.I),
                "descricao": "Campo magnético de corrente em fio reto",
                "unidades": "B (T), μ₀ (T⋅m/A), I (A), r (m)"
            },
            "Lei de Faraday": {
                "formula": Eq(self.V, -self.phi.diff(self.t)),
                "descricao": "Tensão induzida por variação de fluxo magnético",
                "unidades": "V (V), Φ (Wb), t (s)"
            },
            "Indutância": {
                "formula": Eq(self.L, self.N * self.phi / self.I),
                "descricao": "Indutância de um solenoide",
                "unidades": "L (H), N (espiras), Φ (Wb), I (A)"
            }
        }
        
        self.formulas_cd = {
            "Álgebra Booleana": {
                "formula": [Eq(self.A + self.A, self.A), Eq(self.A * self.A, self.A)],
                "descricao": "Leis de idempotência",
                "regras": ["A + A = A", "A · A = A"]
            },
            "Leis de De Morgan": {
                "formula": ["¬(A + B) = ¬A · ¬B", "¬(A · B) = ¬A + ¬B"],
                "descricao": "Negação de expressões booleanas",
                "regras": ["¬(A + B) = ¬A · ¬B", "¬(A · B) = ¬A + ¬B"]
            },
            "Propagação de Delay": {
                "formula": "tpd = max(tpd1, tpd2, ..., tpdn)",
                "descricao": "Tempo de propagação em cascata",
                "unidades": "tpd (s)"
            },
            "Fan-out": {
                "formula": Eq(self.F, self.IOL / self.IIL),
                "descricao": "Capacidade de acionar outras portas",
                "unidades": "Fan-out (adimensional)"
            },
            "Margem de Ruído": {
                "formula": Eq(self.F, self.VOH - self.VIH),
                "descricao": "Margem de imunidade a ruído",
                "unidades": "NM (V)"
            },
            "Tempo de Setup": {
                "formula": Eq(self.tsetup, self.tclk - self.tcomb - self.tskew),
                "descricao": "Tempo mínimo antes do clock",
                "unidades": "tsetup (s)"
            },
            "Tempo de Hold": {
                "formula": Eq(self.thold, self.tcomb + self.tskew),
                "descricao": "Tempo mínimo após o clock",
                "unidades": "thold (s)"
            }
        }
    
    def get_formula_latex(self, formula_dict):
        """Converter fórmula para LaTeX"""
        if isinstance(formula_dict["formula"], list):
            formulas = []
            for f in formula_dict["formula"]:
                if isinstance(f, str):
                    formulas.append(f)
                else:
                    formulas.append(f"${latex(f.lhs)} = {latex(f.rhs)}$")
            return formulas
        else:
            if isinstance(formula_dict["formula"], str):
                return formula_dict["formula"]
            else:
                return f"${latex(formula_dict['formula'].lhs)} = {latex(formula_dict['formula'].rhs)}$"
    
    def get_formula_text(self, formula_dict):
        """Converter fórmula para texto legível"""
        if isinstance(formula_dict["formula"], list):
            formulas = []
            for f in formula_dict["formula"]:
                if isinstance(f, str):
                    formulas.append(f)
                else:
                    formulas.append(f"${latex(f.lhs)} = {latex(f.rhs)}$")
            return formulas
        else:
            if isinstance(formula_dict["formula"], str):
                return formula_dict["formula"]
            else:
                return f"${latex(formula_dict['formula'].lhs)} = {latex(formula_dict['formula'].rhs)}$"
    
    def calculate_example(self, formula_name, values):
        """Calcular exemplo numérico"""
        if formula_name in self.formulas_em:
            formula = self.formulas_em[formula_name]["formula"]
            # Substituir valores e calcular
            result = formula.subs(values)
            return f"Exemplo: {result}"
        return "Exemplo não disponível"

class PDFGenerator:
    """Classe para gerar PDF com fórmulas"""
    
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.width, self.height = A4
        self.formula_manager = FormulaManager()
    
    def draw_section(self, title, content, y_start):
        """Desenhar seção no PDF"""
        self.c.setFont("Helvetica", 14)
        self.c.drawString(40, y_start, title)
        self.c.setFont("Helvetica", 11)
        y = y_start - 20
        
        if isinstance(content, dict):
            for key, value in content.items():
                # Título da fórmula
                self.c.setFont("Helvetica", 12)
                self.c.drawString(40, y, key)
                y -= 15
                
                # Fórmula
                self.c.setFont("Helvetica", 10)
                if isinstance(value, dict):
                    formula_text = self.formula_manager.get_formula_text(value)
                    if isinstance(formula_text, list):
                        for f in formula_text:
                            self.c.drawString(50, y, f)
                            y -= 12
                    else:
                        self.c.drawString(50, y, formula_text)
                        y -= 12
                    
                    # Descrição
                    if "descricao" in value:
                        self.c.setFont("Helvetica", 9)
                        self.c.drawString(50, y, f"Descrição: {value['descricao']}")
                        y -= 12
                    
                    # Unidades ou regras
                    if "unidades" in value:
                        self.c.setFont("Helvetica", 9)
                        self.c.drawString(50, y, f"Unidades: {value['unidades']}")
                        y -= 12
                    elif "regras" in value:
                        self.c.setFont("Helvetica", 9)
                        for rule in value["regras"]:
                            self.c.drawString(50, y, f"• {rule}")
                            y -= 12
                
                y -= 5  # Espaço entre fórmulas
                
                if y < 40:
                    self.c.showPage()
                    y = self.height - 40
                    self.c.setFont("Helvetica", 11)
        
        elif isinstance(content, str):
            lines = content.split('\n')
            for line in lines:
                if len(line) > 80:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            self.c.drawString(40, y, current_line.strip())
                            y -= 15
                            current_line = word + " "
                            if y < 40:
                                self.c.showPage()
                                y = self.height - 40
                                self.c.setFont("Helvetica", 11)
                    if current_line:
                        self.c.drawString(40, y, current_line.strip())
                        y -= 15
                else:
                    self.c.drawString(40, y, line)
                    y -= 15
                
                if y < 40:
                    self.c.showPage()
                    y = self.height - 40
                    self.c.setFont("Helvetica", 11)

        return y - 20

    def generate_pdf(self):
        """Gerar o PDF completo"""
        y = self.height - 50
        
        # Fórmulas de Eletromagnetismo
        y = self.draw_section("Fórmulas de Eletromagnetismo", self.formula_manager.formulas_em, y)
        
        # Fórmulas de Circuitos Digitais
        y = self.draw_section("Fórmulas de Circuitos Digitais", self.formula_manager.formulas_cd, y)
        
        # Frase de poder
        frase_poder = """10h – 11h
Foco absoluto. Repetir frase de poder:
'Eu sou Pedro Victor. Eu vejo o campo invisível. Eu domino o circuito lógico. Eu passo.'

Estratégias de concentração:
- Respiração 4-7-8
- Técnica Pomodoro: 25min foco, 5min pausa
- Eliminar distrações
- Visualizar o sucesso"""
        
        y = self.draw_section("Frase de Poder", frase_poder, y)
        
        # Plano de estudo final
        plano_final = {
            "Dia 1 - Eletromagnetismo": "Revisar leis fundamentais, resolver 10 exercícios",
            "Dia 2 - Circuitos Digitais": "Álgebra booleana, portas lógicas, 15 exercícios",
            "Dia 3 - Simulados": "2 simulados completos, análise de erros",
            "Dia 4 - Revisão Final": "Fórmulas principais, pontos fracos, 1 simulado",
            "Dia 5 - Prova": "Descanso mental, revisão rápida, confiança"
        }
        
        y = self.draw_section("Plano de Estudo Final", plano_final, y)
        
        self.c.save()
        print(f"PDF criado com sucesso: {os.path.abspath(self.filename)}")

# Gerar o PDF
if __name__ == "__main__":
    pdf_gen = PDFGenerator("Plano_Final_Pedro_Victor_Prova_15-07.pdf")
    pdf_gen.generate_pdf()

