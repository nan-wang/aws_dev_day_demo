import streamlit as st
from docarray import DocumentArray

from utils import Status, get_prompt
import os

if 'status' not in st.session_state.keys():
    st.session_state['status'] = Status.PROMPT

def load_data():
    if 'fav_docs' in st.session_state.keys():
        print('fav_docs is there, skip loading')
        return
    if os.path.exists('data.bin'):
        st.session_state['fav_docs'] = DocumentArray.load_binary('data.bin')
        print(f'st.session_state.fav_docs: {len(st.session_state.fav_docs)}')


def main():
    load_data()
    get_prompt()


main()
