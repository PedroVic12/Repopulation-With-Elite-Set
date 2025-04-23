import streamlit as st
import schemdraw
import schemdraw.elements as elm
from PIL import Image
import io

if 'componentes' not in st.session_state:
    st.session_state.componentes = []
if 'ultima_pos' not in st.session_state:
    st.session_state.ultima_pos = (0, 0)
if 'direcao_atual' not in st.session_state:
    st.session_state.direcao_atual = 'right'

direcoes = {
    'right': (1, 0),
    'left': (-1, 0),
    'up': (0, 1),
    'down': (0, -1)
}

def adicionar_componente(tipo, valor=""):
    x, y = st.session_state.ultima_pos
    dx, dy = direcoes[st.session_state.direcao_atual]
    nova_pos = (x + dx, y + dy)
    
    # Adiciona um deslocamento adicional para os componentes que estão abaixo
    if st.session_state.direcao_atual == 'down':
        nova_pos = (nova_pos[0], nova_pos[1] - 1)
    
    st.session_state.componentes.append({
        "tipo": tipo,
        "valor": valor,
        "xy": nova_pos,
        "orientacao": st.session_state.direcao_atual
    })
    st.session_state.ultima_pos = nova_pos

def desenhar_circuito(componentes):
    with schemdraw.Drawing() as d:
        for i, comp in enumerate(componentes):
            tipo = comp.get("tipo")
            valor = comp.get("valor", "")
            orientacao = comp.get("orientacao", "right").lower()
            xy = comp.get("xy", (0, 0))
            anchor = comp.get("anchor", "start")

            if tipo == "resistor":
                base = elm.Resistor().label(valor)
            elif tipo == "capacitor":
                base = elm.Capacitor().label(valor)
            elif tipo == "fonte":
                base = elm.SourceV().label(valor)
            elif tipo == "indutor":
                base = elm.Inductor().label(valor)
            elif tipo == "terra":
                base = elm.Ground()
            elif tipo == "fio":
                base = elm.Line()
            else:
                continue

            dx, dy = direcoes[orientacao]
            xy = (xy[0] + i * dx, xy[1] + i * dy)

            d += base.at(xy).anchor(anchor)

        if componentes:
            d += elm.Line().at(componentes[-1]["xy"]).to(componentes[0]["xy"])

        buf = io.BytesIO()
        d.draw()
        d.save(buf)
        buf.seek(0)
        return Image.open(buf)

st.title("🧠 Jedi Circuit Builder - Engenharia Eletrica UFF")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Escolha o componente:")
    tipo = st.selectbox("Tipo", ["resistor", "capacitor", "fonte", "terra", "fio"])
    valor = st.text_input("Valor", "10Ω" if tipo == "resistor" else "")
    if st.button("Adicionar Componente"):
        adicionar_componente(tipo, valor)

with col2:
    st.subheader("Direção do próximo:")
    if st.button("⬆️ Cima"):
        st.session_state.direcao_atual = "up"
    if st.button("⬇️ Baixo"):
        st.session_state.direcao_atual = "down"
    if st.button("⬅️ Esquerda"):
        st.session_state.direcao_atual = "left"
    if st.button("➡️ Direita"):
        st.session_state.direcao_atual = "right"

st.subheader("Circuito Atual:")
if st.session_state.componentes:
    imagem = desenhar_circuito(st.session_state.componentes)
    st.image(imagem)
else:
    st.info("Adicione um componente para começar.")

if st.button("🔄 Resetar Circuito"):
    st.session_state.componentes = []
    st.session_state.ultima_pos = (0, 0)
    st.session_state.direcao_atual = 'right'
