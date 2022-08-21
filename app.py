import streamlit as st

from utils import Status, get_prompt, load_data

if 'status' not in st.session_state.keys():
    st.session_state['status'] = Status.PROMPT


def main():
    da = load_data()
    if da is not None:
        print(f'load data successfully. len(da): {len(da)}')
        st.session_state['fav_docs'] = da
    get_prompt()


main()
