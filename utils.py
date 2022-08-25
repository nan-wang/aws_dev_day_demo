import os
from enum import Enum

import streamlit as st
from docarray import Document, DocumentArray
from datetime import datetime


class Status(Enum):
    PROMPT = 1
    OPENAI = 2
    DALLE = 3
    DIFFUSION = 4
    UPSCALE = 5


def get_prompt():
    if st.session_state.status.value != Status.PROMPT.value:
        return
    plot_tile()
    plot_sidebar()
    if 'fav_docs' in st.session_state:
        st.text(f'前情提要：{st.session_state.fav_docs[-1].tags["description"]}')
    # st.subheader('故事接龙：我们开着一辆红色的巴士去...')
    st.text_input('',
                  key='description_raw',
                  # placeholder='举个例子：故宫 / 巴黎 / 麦田 / 野餐 / 看夕阳',
                  max_chars=32,
                  on_change=translate_prompt)


def translate_prompt():
    if st.session_state.description_raw:
        st.session_state.status = Status.OPENAI
        # f'a children book illustration of a red bus and {scenario}, the style of Linh Pham'
        # f'a children book illustration of a red bus and {scenario}, the style of Studio Ghibli'
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY', None)
        if openai.api_key is None:
            st.error('Translation API failed')
        try:
            response = openai.Completion.create(
                model="text-davinci-002",
                prompt=f"Translate this into English:\n{st.session_state.description_raw}",
                temperature=0.3,
                max_tokens=100,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            text_en = response['choices'][0]['text'].strip()
            print(f'text_en: {text_en}')
            response = openai.Completion.create(
                model="text-davinci-002",
                prompt=f"Write a description for a child book illustration. \n\nstory: {st.session_state.description_raw}",
                temperature=0.7,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            st.session_state['prompt_raw'] = text_en
            print(f'st.session_state["prompt_raw"]: {st.session_state["prompt_raw"]}')
            get_from_dalle()
        except Exception as e:
            print(f'translation failed. {e}')
            st.button('再来一次', on_click=reset_status)


def get_from_dalle():
    if st.session_state.prompt_raw:
        # f'a children book illustration of a red bus and {scenario}, the style of Linh Pham'
        # f'a children book illustration of a red bus and {scenario}, the style of Studio Ghibli'
        prompt = f'a whimsical child book illustration in the style charming, childlike, carefree, dreamy, fun and colorful. {st.session_state.prompt_raw}'
        with st.spinner('正在努力构思✍️...'):
            try:
                doc = Document(text=prompt).post(server_url, parameters={'num_images': 5})
            except Exception as e:
                st.error(f'failed to call {server_url}, {e}')
                reset_status()
                return
        st.session_state.status = Status.DALLE
        doc.tags['description'] = f'{st.session_state.description_raw}'
        doc.tags['prompt'] = prompt
        st.session_state['doc'] = doc
    if st.session_state.status.value != Status.DALLE.value:
        return
    plot_tile()
    st.header('选择你满意的初稿❤️')
    st.subheader(f'{st.session_state.doc.tags["description"]}')
    col_list = st.columns(3)
    counter = 0
    for idx, d in enumerate(doc.matches[:9]):
        with col_list[idx % 3]:
            st.image(d.uri, caption=f'画稿 {idx + 1}')
        counter += 1
    st.button('再试一次', on_click=reset_status)
    st.selectbox(
        "你满意的初稿❤️",
        [''] + list([f'画稿 {i + 1}' for i in range(counter)]),
        key='fav_1st_id_str',
        index=0,
        on_change=get_from_diffusion)


def get_from_diffusion():
    if st.session_state.get('fav_1st_id_str', ''):
        fav_id = int(st.session_state.fav_1st_id_str[3:]) - 1
        fav = st.session_state.doc.matches[fav_id]
        st.session_state.doc.tags['fav_id'] = fav_id
        fav.embedding = st.session_state.doc.embedding
        with st.spinner('正在努力绘制精修图片🎨...'):
            doc = fav.post(
                f'{server_url}',
                parameters={'skip_rate': 0.6, 'num_images': 6},
                target_executor='diffusion')
            st.session_state.doc.matches[fav_id].matches = doc.matches
        st.session_state.status = Status.DIFFUSION
    if st.session_state.status.value != Status.DIFFUSION.value:
        return
    plot_tile()
    st.header('选择你满意的精修图片❤️')
    st.subheader(f'{st.session_state.doc.tags["description"]}')
    col_list = st.columns(3)
    counter = 0
    fav_id = st.session_state.doc.tags['fav_id']
    for idx, d in enumerate(st.session_state.doc.matches[fav_id].matches):
        with col_list[idx % 3]:
            st.image(d.uri, caption=f'画稿 {idx + 1}')
        counter += 1
    st.selectbox(
        "你满意的精修稿❤️",
        [''] + list([f'画稿 {i + 1}' for i in range(counter)]),
        index=0,
        key='fav_2nd_id_str',
        on_change=get_from_upscale)


def get_from_upscale():
    if st.session_state.get('fav_2nd_id_str', ''):
        dfav_id = int(st.session_state.fav_2nd_id_str[3:]) - 1
        fav_id = st.session_state.doc.tags['fav_id']
        dfav = st.session_state.doc.matches[fav_id].matches[dfav_id]
        st.session_state.doc.tags['dfav_id'] = dfav_id
        with st.spinner('正在完成最后的修改🎨...'):
            dfav.post(f'{server_url}/upscale')
        st.session_state.status = Status.UPSCALE
    if st.session_state.status.value == Status.UPSCALE.value:
        st.header('大功告成🎉')
        st.image(dfav.uri, caption=f'{st.session_state.doc.tags["description"]}')
        st.button('发布', on_click=get_name)
        st.button('再来一次', on_click=reset_status)


def reset_status():
    st.session_state.status = Status.PROMPT
    with st.spinner('重新准备画布'):
        try:
            st.session_state.fav_docs.push(name='aws_china_dev_day_demo_202208_cn')
        except Exception:
            st.error('同步数据失败🚧')


def get_name():
    st.text_input('你的昵称', key='author', on_change=save_fav, max_chars=32)


def save_fav():
    fav_id = st.session_state.doc.tags['fav_id']
    dfav_id = st.session_state.doc.tags['dfav_id']
    dfav = st.session_state.doc.matches[fav_id].matches[dfav_id]
    dfav.text = st.session_state.doc.tags["description"]
    dfav.tags['author'] = st.session_state.author if st.session_state.author else '无名'
    dfav.tags['ctime'] = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')
    dfav.tags['caption'] = \
        f'{st.session_state.doc.tags["description"]}\nBy {dfav.tags["author"]}, {dfav.tags["ctime"]}'
    dfav.tags['description'] = st.session_state.doc.tags["description"]
    if 'fav_docs' not in st.session_state.keys():
        st.session_state['fav_docs'] = DocumentArray.empty()
    st.session_state.fav_docs.append(dfav)
    st.image(dfav.uri, caption=dfav.tags['caption'])
    st.info('发布成功🎉')
    plot_sidebar()
    st.button('再来一次', on_click=reset_status)


server_url = 'grpcs://dalle-flow.dev.jina.ai'


def plot_tile():
    # st.title('给孩子讲故事')
    st.title('一起接龙讲述一个开巴士🚌去旅行的儿童故事')


@st.cache(allow_output_mutation=True)
def load_data():
    if 'fav_docs' in st.session_state.keys():
        print('fav_docs is there, skip loading')
        return None
    if os.environ.get('JINA_AUTH_TOKEN', None) is not None:
        try:
            da = DocumentArray.pull(name='aws_china_dev_day_demo_202208_cn')
            return da
        except Exception:
            print('加载数据失败')
    return None


def plot_sidebar():
    da = st.session_state.get('fav_docs', DocumentArray.empty())
    with st.sidebar:
        for d in reversed(da):
            st.image(d.uri,
                     caption=f'{d.tags["caption"]}')
