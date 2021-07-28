import streamlit as st
from io import StringIO
from tools import process 

code = ''

st.title("Data Processor")
st.write("""puede añadir un nuevo csv usando el componente siguiente, no obstante si ya el csv se encuentra cargado (de previas ejecuciones o agregado manualmente) puede directamente ejecutar el programa tocando el boton""")

uploaded_file = st.file_uploader(" ")
if uploaded_file is not None:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    string_data = stringio.read()
    with open('data.csv', 'w') as f:
        f.write(string_data)
    
if st.button('Comenzar procesamiento'):
    code = process()
    # print(code)
if code == 'errors':
    st.error('hubo errores, revisar archivo errors.csv')
elif code == 'notifications':
    st.info('se corrigieron automaticamente algunos errores')
elif code != '':
    st.success('procesado correctamente')
