import streamlit as st
from docarray import Document


def get_prompt(text):
    scenario = text
    if not text:
        return None
    return f'a whimsical child book illustration of the red bus and {scenario}, the style charming, childlike, carefree, dreamy, fun and colorful'
    # return f'a children book illustration of a red bus and {scenario}, the style of Linh Pham'
    # return f'a children book illustration of a red bus and {scenario}, the style of Studio Ghibli'


@st.cache(allow_output_mutation=True)
def get_from_dalle(prompt):
    doc = Document(text=prompt).post(server_url, parameters={'num_images': 3})
    return doc, doc.matches


@st.cache(allow_output_mutation=True)
def get_from_diffusion(doc):
    return doc.post(f'{server_url}', parameters={'skip_rate': 0.6, 'num_images': 6},
             target_executor='diffusion').matches


@st.cache(allow_output_mutation=True)
def get_from_upscale(doc):
    return doc.post(f'{server_url}/upscale')


server_url = 'grpcs://dalle-flow.dev.jina.ai'
drafts = None
doc = None
fav = None
fav_id = None
dfav = None
dfav_id = None
final_fav = None

st.session_state['fav_id_str'] = ''
st.session_state['dfav_id_str'] = ''

st.title('让我们一起给孩子讲故事')
st.text('一个关于开巴士去旅行的故事🚌')

st.header('第一步：一句话描述你的故事')
st.text_input('We are driving a red bus to ...',
              key='prompt_raw',
              placeholder='a mountain / a flower field / a bridge over the river / take a picnic')

# extract the key entity from st.session_state.prompt_raw
prompt = get_prompt(st.session_state.prompt_raw)


if prompt:
    with st.spinner('正在努力构思✍️...'):
        doc, drafts = get_from_dalle(prompt)


if drafts is not None:
    st.header('第二步：选择你满意的初稿❤️')
    col_list = st.columns(3)
    counter = 0
    for idx, d in enumerate(drafts):
        with col_list[idx%3]:
            st.image(d.uri, caption=f'画稿 {idx+1}')
        counter += 1
    fav_id_str = st.selectbox(
        "你满意的初稿❤️",
        [''] + list([f'画稿 {i+1}' for i in range(counter)]),
        index=0)
    if fav_id_str:
        fav_id = int(fav_id_str[3:]) - 1
        fav = drafts[fav_id]
        fav.embedding = doc.embedding


if fav is not None:
    with st.spinner('正在努力绘制🎨...'):
        diffused = get_from_diffusion(fav)
    st.header('第三步：选择你满意的精修图片❤️')
    col_list = st.columns(3)
    counter = 0
    for idx, d in enumerate(diffused):
        with col_list[idx%3]:
            st.image(d.uri, caption=f'画稿 {idx+1}')
        counter += 1

    dfav_id_str = st.selectbox(
        "你满意的精修稿❤️",
        [''] + list([f'画稿 {i+1}' for i in range(counter)]),
        index=0)
    if dfav_id_str:
        dfav_id = int(dfav_id_str[3:]) - 1
        dfav = diffused[dfav_id]


if dfav is not None:
    with st.spinner('正在完成最后的修改🎨...'):
        final_fav = get_from_upscale(dfav)
    if final_fav is not None:
        st.header('大功告成🎉')
        st.image(final_fav.uri, caption=f'We are driving a red bus to {st.session_state.prompt_raw}')