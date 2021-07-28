import streamlit as st
from tools import process 

code = ''
if st.button('Comenzar procesamiento'):
    code = process()
if code == 'error':
    st.danger('hubo errores')
elif code == 'notifications':
    st.info('se corrigieron automaticamente algunos errores')
elif code != '':
    st.success('procesado correctamente')
