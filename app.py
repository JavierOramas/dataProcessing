import streamlit as st
from io import StringIO
from tools import process
from zipfile import ZipFile
import shutil

import base64
import json
import pickle
import uuid
import re
import os
import streamlit as st
import pandas as pd

# from download import download_button

def download_button(download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.

    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.

    Returns:
    -------
    (str): the anchor tag to download object_to_download

    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')

    """
    
    try:

        button_uuid = str(uuid.uuid4()).replace('-', '')
        button_id = re.sub('\d+', '', button_uuid)

        prim_color = st.config.get_option('theme.primaryColor') or '#F43365'
        bg_color = st.config.get_option('theme.backgroundColor') or '#f1f3f6'
        sbg_color = st.config.get_option('theme.secondaryBackgroundColor') or '#f1f3f6'
        txt_color = st.config.get_option('theme.textColor') or '#000000' 
        font = st.config.get_option('theme.font') or 'sans serif'  


        custom_css = f"""
            <style>
                #{button_id} {{
                    background-color: {bg_color};
                    color: {txt_color};
                    padding: 0.25rem 0.75rem;
                    position: relative;
                    line-height: 1.6;
                    border-radius: 0.25rem;
                    border-width: 1px;
                    border-style: solid;
                    border-color: {bg_color};
                    border-image: initial;
                    filter: brightness(105%);
                    justify-content: center;
                    margin: 0px;
                    width: auto;
                    appearance: button;
                    display: inline-flex;
                    family-font: {font};
                    font-weight: 400;
                    letter-spacing: normal;
                    word-spacing: normal;
                    text-align: center;
                    text-rendering: auto;
                    text-transform: none;
                    text-indent: 0px;
                    text-shadow: none;
                    text-decoration: none;
                }}
                #{button_id}:hover {{

                    border-color: {prim_color};
                    color: {prim_color};
                }}
                #{button_id}:active {{
                    box-shadow: none;
                    background-color: {prim_color};
                    color: {sbg_color};
                    }}
            </style> """

        with open('files.zip', "rb") as f:
            bytes = f.read()
            b64 = base64.b64encode(bytes).decode()
        dl_link = custom_css + f'<a download="files.zip" class= "" id="{button_id}" ' \
                               f'href="data:file/zip;base64,{b64}">{button_text}</a><br></br>'
        return dl_link

    except:
        pass

def get_all_file_paths():
    directory = 'done'
    # initializing empty file paths list
    file_paths = []
    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths


code = ''

try:
    shutil.rmtree('done/')
    os.remove('files.zip')
except:
    pass

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

if code != 'errors':
    file_paths = get_all_file_paths()
    if len(file_paths) != 0:
        # writing files to a zipfile
        with ZipFile('files.zip','w') as zip:
            # writing each file one by one
            for file in file_paths:
                zip.write(file)
        st.markdown(download_button('files.zip', 'Descargar archivos'), unsafe_allow_html=True)