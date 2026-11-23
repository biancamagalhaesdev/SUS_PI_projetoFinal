"""SUS Inteligente — Piauí: ponto de entrada da aplicação (navegação e identidade visual).

Execução:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="SUS Inteligente — Piauí", page_icon="🩺", layout="wide",
                   initial_sidebar_state="collapsed")

from utils.config import PAGINA  # noqa: E402
from utils.ui import configurar_estilo  # noqa: E402

configurar_estilo()
paginas = [
    st.Page(PAGINA["mapa"], title="Mapa", icon=":material/map:", default=True),
    st.Page(PAGINA["municipio"], title="Município", icon=":material/location_city:"),
    st.Page(PAGINA["grupos"], title="Grupos", icon=":material/hub:"),
    st.Page(PAGINA["sobre"], title="Sobre", icon=":material/info:"),
]
st.navigation(paginas, position="top").run()
