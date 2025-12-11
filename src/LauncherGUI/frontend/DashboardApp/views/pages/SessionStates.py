import streamlit as st
import pandas as pd

def SesssionsPage():
    st.subheader("Lets explore sessons states and callbacks functions")

    if "number_rows" not in st.session_state:
        st.session_state["number_rows"] = 5

    df = pd.DataFrame(
        {
            "first column": [i for i in range(st.session_state["number_rows"])],
            "second column": [i for i in range(st.session_state["number_rows"])],
        }
    )

    st.dataframe(df)


    increment = st.button("Mostrar mais")
    if increment:
        st.session_state["number_rows"] += 1
        st.rerun()

    decrement = st.button("Mostrar menos")
    if decrement:
        st.session_state["number_rows"] -= 1

    st.table(df.head(st.session_state["number_rows"]))

    st.session_state["type"] = "Categorical"
    types = {
        "Categorical": pd.Categorical,

    }

    column = st.selectbox("Selecione uma coluna", types[st.session_state["type"]].categories)
    
    st.session_state["type"] = st.radio("Qual o tipo de analise", ["Categorical", "Numerical"])

    if st.session_state["type"] == "Categorical":
        data = pd.DataFrame(df[column].value_counts()).head(st.session_state["number_rows"])
        st.bar_chart(data)
    else:
        st.table(df[column].describe())

    
    "session state", st.session_state

    def lbs_to_kg():
        st.session_state.kg = st.session_state.lbs/2.2046

    
    def kg_to_lbs():
        st.session_state.lbs = st.session_state.kg*2.2046



    col1, buff, col2 = st.columns([2,1,2])
    with col1:
        st.number_input("lbs", key="lbs", on_change=lbs_to_kg)
    with col2:
        st.number_input("kg", key="kg", on_change=kg_to_lbs)



