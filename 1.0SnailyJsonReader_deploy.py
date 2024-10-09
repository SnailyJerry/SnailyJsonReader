import streamlit as st
import json
import deepl
import pandas as pd
import io

# DeepL API Key (从 st.secrets 中获取密钥)
translator = deepl.Translator(st.secrets["DEEPL_API_KEYS"])

# 加载 JSONL 文件
def load_file():
    uploaded_file = st.sidebar.file_uploader("Load JSONL File", type=["jsonl"], key="file_uploader")
    if uploaded_file is not None:
        json_data = []
        for line in uploaded_file:
            try:
                json_obj = json.loads(line.decode("utf-8"))
                json_data.append(json_obj)
            except json.JSONDecodeError:
                st.error("Error decoding JSON line.")
        return json_data
    return None

# 显示数据并筛选
def display_data(json_data):
    filtered_data = []
    search_query = st.sidebar.text_input("Search", "", key="search_input")
    
    if search_query:
        filtered_data = [item for item in json_data if search_query.lower() in json.dumps(item).lower()]
    else:
        filtered_data = json_data

    # 使用 Pandas DataFrame 来展示数据
    data_df = pd.DataFrame([{
        'custom_id': item.get('custom_id', 'N/A'),
        'is_checked': item.get('is_checked', False)
    } for item in filtered_data])
    
    # 定义格式化行
    def format_row(i):
        check_mark = "✅ " if filtered_data[i].get('is_checked', False) else ""
        return f"{check_mark}{filtered_data[i].get('custom_id', 'N/A')}"
    
    # 提取 custom_id 列表
    custom_id_list = [item.get('custom_id', 'N/A') for item in filtered_data]
    
    if len(custom_id_list) > 0:
        selected_custom_id = st.sidebar.selectbox(
            "Select Custom ID",
            custom_id_list,  # 使用 custom_id 作为选项
            key="select_custom_id"
        )
        
        # 获取选中的 custom_id 对应的索引
        selected_index = custom_id_list.index(selected_custom_id)
        
        st.sidebar.dataframe(data_df[['custom_id', 'is_checked']])
        
        return filtered_data, selected_index
    else:
        st.sidebar.info("No data to display.")
        return None, None

# 显示详细信息
def show_details(json_obj):
    content = json_obj.get('response', {}).get('body', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
    st.text_area("Details", value=content, height=200, key="details_text")
    return content

# 翻译内容
def translate_content(content):
    try:
        if content:
            translated = translator.translate_text(content, target_lang="ZH")
            st.text_area("Translated Content", value=translated.text, height=200, key="translated_text")
        else:
            st.info("No content to translate.")
    except Exception as e:
        st.error(f"Failed to translate content: {e}")

# 保存更改
def save_changes(json_data, selected_index):
    if st.button("Save Changes", key="save_changes"):
        updated_content = st.session_state.details_text
        if 'response' in json_data[selected_index] and 'body' in json_data[selected_index]['response']:
            json_data[selected_index]['response']['body']['choices'][0]['message']['content'] = updated_content
            st.success("Changes saved successfully!")
        else:
            st.error("Failed to save changes: Invalid JSON structure.")
        return json_data
    return None

# 标记为已确认
def mark_as_checked(json_data, selected_index):
    if st.button("Check (Confirm)", key="check_confirm"):
        json_data[selected_index]['is_checked'] = True
        st.success("Marked as checked!")
        st.session_state.json_data = json_data
        # 修改 session_state 变量以触发页面刷新
        st.session_state["checked"] = not st.session_state.get("checked", False)
    return json_data

# 导出修改后的 JSONL 文件
def export_jsonl(json_data):
    jsonl_str = "\n".join([json.dumps(record) for record in json_data])
    b = io.BytesIO(jsonl_str.encode('utf-8'))
    b.seek(0)
    return b

# Streamlit App 主界面
st.title("😜蜗牛代码浏览器V1.5")

# 初始化会话状态
if 'json_data' not in st.session_state or st.session_state.json_data is None:
    st.session_state.json_data = load_file()

# 检查文件是否上传成功并正确加载
if st.session_state.json_data is not None:
    filtered_data, selected_index = display_data(st.session_state.json_data)
    
    if filtered_data and selected_index is not None:
        json_obj = filtered_data[selected_index]
        
        # 显示详细内容
        content = show_details(json_obj)
        
        # 翻译内容
        translate_content(content)
        
        # 显示保存和标记的按钮
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.json_data = save_changes(st.session_state.json_data, selected_index) or st.session_state.json_data
        with col2:
            st.session_state.json_data = mark_as_checked(st.session_state.json_data, selected_index)

    # 添加导出按钮，导出修改后的文件
    st.sidebar.header("Ready to export?")
    
    modified_file = export_jsonl(st.session_state.json_data)
    
    st.sidebar.download_button(
        label="💾 Download Modified JSONL",
        data=modified_file,
        file_name="modified_data.jsonl",
        mime="application/jsonl",
        key="download_button",
        help="Click to download the modified file."
    )
else:
    st.info("Please upload a JSONL file to begin.")

