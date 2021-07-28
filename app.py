import streamlit as st
from io import StringIO
from tools import process 

code = ''

uploaded_file = st.file_uploader("Upload csv")
if uploaded_file is not None:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    string_data = stringio.read()
    with open('data.csv', 'w') as f:
        f.write(string_data)
    
if st.button('Comenzar procesamiento'):
    code = process()
if code == 'error':
    st.danger('hubo errores')
elif code == 'notifications':
    st.info('se corrigieron automaticamente algunos errores')
elif code != '':
    st.success('procesado correctamente')
