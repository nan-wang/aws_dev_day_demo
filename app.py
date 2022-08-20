import streamlit as st

from utils import Status, get_prompt, load_data

if 'status' not in st.session_state.keys():
    st.session_state['status'] = Status.PROMPT


def main():
    load_data()
    get_prompt()


main()
