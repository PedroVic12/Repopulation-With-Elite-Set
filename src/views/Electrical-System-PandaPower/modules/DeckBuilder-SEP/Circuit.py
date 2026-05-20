# string_circuit.py
import io
from PySide6.QtGui import QPixmap
import schemdraw
from schemdraw import elements as elm

class StringCircuitGenerator:
    """
    Gera diagramas de circuitos a partir de uma notação em string.
    Atualmente mapeia palavras-chave para cinco circuitos predefinidos:
      - 'RC'          : Circuito RC série
      - 'RLC'         : Circuito RLC série
      - 'RLC paralelo': Circuito RLC paralelo
      - 'CA simples'  : Circuito CA com fonte senoidal, resistor e indutor
      - 'duas malhas' : Circuito com duas malhas acopladas
    Se a string não for reconhecida, retorna o circuito RC série.
    """

    def __init__(self):
        self.drawing = None

    # ----------------------------------------------------------------------
    # Geradores de cada exemplo
    # ----------------------------------------------------------------------
    def _generate_rc_series(self):
        """Circuito RC série (exemplo 1)"""
        d = schemdraw.Drawing()
        d += elm.Resistor().label('R1')
        d += elm.Capacitor().label('C1')
        d += elm.Line().dot()
        return d

    def _generate_rlc_series(self):
        """Circuito RLC série (exemplo 2)"""
        d = schemdraw.Drawing()
        d += elm.Resistor().label('R')
        d += elm.Inductor().label('L')
        d += elm.Capacitor().label('C')
        d += elm.Line().dot()
        return d

    def _generate_rlc_parallel(self):
        """Circuito RLC paralelo (exemplo 3)"""
        d = schemdraw.Drawing()
        # Nó superior
        d += elm.Dot()
        # Ramo R
        d += elm.Resistor().down().label('R')
        d += elm.Dot()
        # Volta ao nó inicial (linha invisível)
        d += elm.Line().up().color('white')
        d += elm.Dot()
        # Ramo L
        d += elm.Inductor().down().label('L')
        d += elm.Dot()
        # Ramo C
        d += elm.Line().up().color('white')
        d += elm.Dot()
        d += elm.Capacitor().down().label('C')
        d += elm.Dot()
        # Fecha o desenho
        d += elm.Line().left()
        return d

    def _generate_ac_simple(self):
        """Circuito CA simples: fonte senoidal + resistor + indutor (exemplo 4)"""
        d = schemdraw.Drawing()
        # Fonte senoidal (AC)
        d += elm.SourceSin().label('V_{AC}')
        d += elm.Resistor().right().label('R')
        d += elm.Inductor().down().label('L')
        d += elm.Line().left().tox(d.here[0]-4)  # volta ao início
        d += elm.Line().up().toy(d.here[1]+2)
        # Adiciona uma seta de corrente (loop)
        d += elm.Line().right().color('white')  # apenas para posicionar
        d += elm.CurrentLabel(top=False, ofst=0.5).at(d.here).label('I')
        return d

    def _generate_two_mesh(self):
        """Circuito com duas malhas (exemplo 5)"""
        d = schemdraw.Drawing()
        # Malha esquerda
        V = elm.SourceV().label('V1')
        d += V
        d += elm.Resistor().right().label('R1')
        d += elm.Dot()
        R2 = elm.Resistor().down().label('R2')
        d += R2
        d += elm.Line().left().tox(V.start)
        d += elm.Line().up().toy(V.start)
        # Malha direita
        d += elm.Dot().at(R2.end)
        d += elm.Resistor().right().label('R3')
        d += elm.Dot()
        d += elm.Line().down().toy(d.here[1]-2)
        d += elm.Line().left().tox(R2.end)
        # Setas de corrente (loops)
        d += elm.CurrentLabel(top=False, ofst=0.3).at(V).label('I_1')
        d += elm.CurrentLabel(top=False, ofst=0.3).at(R3).label('I_2')
        return d

    # ----------------------------------------------------------------------
    # Mapeamento de strings para os geradores
    # ----------------------------------------------------------------------
    def generate_from_notation(self, notation):
        """
        Retorna um objeto schemdraw.Drawing baseado na string de notação.
        """
        examples = {
            'RC': self._generate_rc_series,
            'RLC': self._generate_rlc_series,
            'RLC paralelo': self._generate_rlc_parallel,
            'CA simples': self._generate_ac_simple,
            'duas malhas': self._generate_two_mesh,
        }
        # Normaliza a string (remove espaços extras, mas mantém a capitalização da chave)
        key = notation.strip()
        if key in examples:
            return examples[key]()
        else:
            # Se não encontrar, retorna o circuito RC série como fallback
            return self._generate_rc_series()

    # ----------------------------------------------------------------------
    # Conversão para QPixmap
    # ----------------------------------------------------------------------
    def draw_to_pixmap(self, notation, width=400, height=300):
        """
        Gera o desenho do circuito e retorna um QPixmap redimensionado.
        """
        drawing = self.generate_from_notation(notation)
        # Salva em buffer de memória como PNG
        img_buffer = io.BytesIO()
        drawing.save(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)

        # Converte para QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(img_buffer.getvalue(), 'PNG')
        return pixmap.scaled(width, height)