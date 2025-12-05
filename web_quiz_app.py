import streamlit as st
import json
import random
import requests # 這是用來讀取網路資料的套件
from datetime import datetime

# 設定 Streamlit 頁面基礎配置
st.set_page_config(page_title="雲端題庫測驗系統", layout="centered")

# ==========================================
#              1. 雲端題庫設定
# ==========================================

# 【請在此處填入您 GitHub 上各個 JSON 檔案的 "Raw" 網址】
# 格式為： "顯示名稱": "https://raw.githubusercontent.com/..."
QUIZ_SOURCES = {
    "職業衛生管理學科 (22100)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/22100_%E8%81%B7%E6%A5%AD%E8%A1%9B%E7%94%9F%E7%AE%A1%E7%90%86%E5%AD%B8%E7%A7%91.json",
    "職業安全衛生共同科目 (90006)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/90006_-%E8%81%B7%E6%A5%AD%E5%AE%89%E5%85%A8%E8%A1%9B%E7%94%9F%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "工作倫理與職業道德 (90007)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/90007_-%E5%B7%A5%E4%BD%9C%E5%80%AB%E7%90%86%E8%88%87%E8%81%B7%E6%A5%AD%E9%81%93%E5%BE%B7%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "環境保護共同科目 (90008)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/90008_-%E7%92%B0%E5%A2%83%E4%BF%9D%E8%AD%B7%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "節能減碳共同科目 (90009)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/90009_-%E7%AF%80%E8%83%BD%E6%B8%9B%E7%A2%B3%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "職業衛生管理師_全部題目 (總題庫)": "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/refs/heads/main/%E8%81%B7%E6%A5%AD%E8%A1%9B%E7%94%9F%E7%AE%A1%E7%90%86%E5%B8%AB_%E5%85%A8%E9%83%A8%E9%A1%8C%E7%9B%AE.json",
}

# ==========================================
#              2. 核心邏輯函數
# ==========================================

@st.cache_data(ttl=3600)  # 設定快取 1 小時，避免每次按按鈕都重新下載
def fetch_quiz_data(url):
    """從 GitHub 或其他網址讀取 JSON 資料"""
    try:
        if "your-username" in url or "您的帳號" in url:
            return None # 尚未設定網址
            
        response = requests.get(url)
        response.raise_for_status()  # 檢查連線是否成功 (200 OK)
        
        # 嘗試解析 JSON
        data = response.json()
        
        # 簡單驗證資料格式是否為列表 (List)
        if isinstance(data, list):
            return data
        else:
            st.error(f"資料格式錯誤：預期為 List，但讀取到 {type(data)}")
            return []
            
    except Exception as e:
        st.error(f"讀取題庫失敗：{e}")
        return []

def init_session_state():
    """初始化狀態變數"""
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {} 
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_finished' not in st.session_state:
        st.session_state.quiz_finished = False
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 20
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'current_subject' not in st.session_state:
        st.session_state.current_subject = ""

init_session_state()

def start_quiz(url, subject_name, num_single, num_multi):
    """下載資料並開始測驗"""
    
    # 1. 下載資料
    with st.spinner(f"正在從雲端載入【{subject_name}】題庫，請稍候..."):
        all_qs = fetch_quiz_data(url)
    
    if not all_qs:
        st.error("無法載入題庫，請檢查 GitHub 網址是否正確 (需為 Raw 連結)。")
        return

    # 2. 篩選題型
    try:
        num_single = int(num_single)
        num_multi = int(num_multi)
    except ValueError:
        st.error("題數請輸入數字")
        return

    single_qs = [q for q in all_qs if q.get('type') == 'single']
    multi_qs = [q for q in all_qs if q.get('type') == 'multi']

    # 3. 檢查題數是否足夠
    if num_single > len(single_qs):
        st.warning(f"單選題庫存不足 (共 {len(single_qs)} 題)，已自動調整為最大值。")
        num_single = len(single_qs)
        
    if num_multi > len(multi_qs):
        st.warning(f"多選題庫存不足 (共 {len(multi_qs)} 題)，已自動調整為最大值。")
        num_multi = len(multi_qs)

    if num_single + num_multi == 0:
        st.error("總題數為 0，無法開始測驗。")
        return

    # 4. 抽題與亂序
    selected_questions = random.sample(single_qs, num_single) + random.sample(multi_qs, num_multi)
    random.shuffle(selected_questions)

    # 5. 選項亂序處理
    for q in selected_questions:
        original_options = q["options"]
        original_answers = q["answer"]  # 1-based list

        # 綁定索引並打亂
        option_with_index = list(enumerate(original_options)) # 0-based index
        random.shuffle(option_with_index)

        shuffled_options = []
        new_answer_indices = []

        for new_index, (old_index, opt_text) in enumerate(option_with_index):
            shuffled_options.append(opt_text)
            # 如果舊的正確答案包含這個選項 (old_index + 1)
            if (old_index + 1) in original_answers:  
                new_answer_indices.append(new_index + 1) # 轉換為新的 1-based index

        q["options"] = shuffled_options
        q["answer"] = sorted(new_answer_indices)

    # 6. 更新狀態
    st.session_state.questions = selected_questions
    st.session_state.answers = {}
    st.session_state.current_index = 0
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.current_subject = subject_name
    st.rerun()

def save_current_answer():
    """保存當前題目答案"""
    if not st.session_state.questions: return

    q_index = st.session_state.current_index
    q = st.session_state.questions[q_index]
    selected_indices = []
    
    if q['type'] == 'single':
        component_key = f'q_answer_{q_index}'
        current_answer = st.session_state.get(component_key)
        if isinstance(current_answer, str):
            try:
                # 提取 (1) 中的數字
                index_str = current_answer.split(')')[0].strip('(')
                index = int(index_str) 
                selected_indices = [index]
            except ValueError: pass
        
    elif q['type'] == 'multi':
        num_options = len(q['options'])
        for i in range(num_options):
            checkbox_key = f'q_{q_index}_opt_{i}'
            if st.session_state.get(checkbox_key) is True:
                selected_indices.append(i + 1)
        
    st.session_state.answers[q_index] = sorted(selected_indices)

def navigate_question(direction):
    save_current_answer()
    if direction == "prev" and st.session_state.current_index > 0:
        st.session_state.current_index -= 1
    elif direction == "next" and st.session_state.current_index < len(st.session_state.questions) - 1:
        st.session_state.current_index += 1
    elif direction == "finish":
        finish_quiz()

def finish_quiz():
    save_current_answer()
    score = 0
    total = len(st.session_state.questions)
    st.session_state.errors = []
    
    for i, q in enumerate(st.session_state.questions):
        correct = sorted(q['answer'])
        selected = st.session_state.answers.get(i, [])
        if correct == selected:
            score += 1
        else:
            q_copy = q.copy()
            q_copy['selected'] = selected
            st.session_state.errors.append(q_copy)

    st.session_state.score = score
    st.session_state.total = total
    st.session_state.percent = round(score / total * 100, 2)
    st.session_state.quiz_finished = True
    st.session_state.quiz_started = False

def reset_quiz():
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.answers = {}
    st.session_state.quiz_started = False
    st.session_state.quiz_finished = False
    st.session_state.errors = []
    st.rerun()

# ==========================================
#              3. 頁面顯示
# ==========================================

def show_settings_page():
    st.header("☁️ 雲端題庫測驗系統")
    st.caption("直接從 GitHub 讀取最新題庫，無需上傳檔案")

    # 1. 選擇科目
    subjects = list(QUIZ_SOURCES.keys())
    selected_subject = st.selectbox("請選擇測驗科目：", subjects)
    target_url = QUIZ_SOURCES[selected_subject]

    # 檢查是否已設定網址
    if "your-username" in target_url or "您的帳號" in target_url:
        st.warning("⚠️ 尚未設定 GitHub 網址。請修改程式碼中的 `QUIZ_SOURCES` 變數。")
        st.code(f"目前的網址: {target_url}", language="python")
    
    st.markdown("---")

    # 2. 設定題數
    st.subheader("抽題設定")
    col1, col2 = st.columns(2)
    with col1:
        num_single = st.text_input("單選題數:", value="20")
    with col2:
        num_multi = st.text_input("多選題數:", value="5")

    # 3. 字體設定
    st.subheader("顯示設定")
    new_font_size = st.slider("字體大小", 14, 32, st.session_state.font_size)
    st.session_state.font_size = new_font_size

    # CSS
    st.markdown(
        f"""
        <style>
        .stButton>button, .stTextInput>div>div>input, .stSelectbox>div, .stRadio>div, .stCheckbox>label {{
            font-size: {st.session_state.font_size}px;
        }}
        .stMarkdown h3, .stMarkdown h2, .stMarkdown p, .stMarkdown strong {{
            font-size: {st.session_state.font_size + 2}px;
        }}
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown("---")
    if st.button("🚀 下載題庫並開始測驗", type="primary", use_container_width=True):
        start_quiz(target_url, selected_subject, num_single, num_multi)

def show_quiz_page():
    q_index = st.session_state.current_index
    q = st.session_state.questions[q_index]
    total_q = len(st.session_state.questions)
    
    # CSS
    st.markdown(f"<style>.stRadio>div, .stCheckbox>label, p {{ font-size: {st.session_state.font_size}px !important; }}</style>", unsafe_allow_html=True)

    st.caption(f"當前科目：{st.session_state.current_subject}")
    q_type_text = "【單選】" if q['type'] == 'single' else "【多選】"
    st.subheader(f"第 {q_index + 1}/{total_q} 題 {q_type_text}")
    st.markdown(f"**{q['question']}**")

    prev_selected = st.session_state.answers.get(q_index, [])
    option_labels = [f"({i+1}) {opt}" for i, opt in enumerate(q['options'])]

    if q['type'] == 'single':
        default_idx = prev_selected[0] - 1 if prev_selected else None
        st.radio("選擇答案：", options=option_labels, index=default_idx, key=f'q_answer_{q_index}', label_visibility="collapsed")
    else:
        st.markdown("選擇答案 (可複選)：")
        for i, label in enumerate(option_labels):
            checked = (i + 1) in prev_selected
            st.checkbox(label, value=checked, key=f'q_{q_index}_opt_{i}')

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if q_index > 0:
            st.button("⬅️ 上一題", on_click=navigate_question, args=("prev",), use_container_width=True)
        else:
            st.button("🚫 上一題", disabled=True, use_container_width=True)
    with c2:
        st.markdown(f"<div style='text-align:center; padding-top:10px;'><b>{q_index + 1} / {total_q}</b></div>", unsafe_allow_html=True)
    with c3:
        if q_index < total_q - 1:
            st.button("下一題 ➡️", on_click=navigate_question, args=("next",), type="secondary", use_container_width=True)
        else:
            st.button("✅ 交卷", on_click=navigate_question, args=("finish",), type="primary", use_container_width=True)

def show_result_page():
    if st.session_state.percent >= 80: st.balloons()
    st.header("🎉 測驗結果")
    st.metric("成績", f"{st.session_state.percent} 分", f"答對 {st.session_state.score} / {st.session_state.total} 題")

    if st.session_state.errors:
        st.subheader("📚 錯題檢討")
        
        # 準備下載資料
        export_data = []
        for err in st.session_state.errors:
            item = err.copy()
            # 轉回文字選項方便閱讀
            item['your_answer_text'] = [item['options'][i-1] for i in item.get('selected', []) if 0 < i <= len(item['options'])]
            item['correct_answer_text'] = [item['options'][i-1] for i in item.get('answer', []) if 0 < i <= len(item['options'])]
            export_data.append(item)
            
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button("⬇️ 下載錯題 JSON", json_str, file_name="error_report.json", mime="application/json")

        for i, err in enumerate(st.session_state.errors):
            with st.expander(f"❌ 第 {i+1} 題：{err['question']}"):
                for j, opt in enumerate(err['options']):
                    prefix = ""
                    if (j+1) in err['answer']: prefix += "✅ (正解) "
                    if (j+1) in err['selected']: prefix += "🫵 (你選的) "
                    st.text(f"{prefix}({j+1}) {opt}")

    st.markdown("---")
    if st.button("🔄 回首頁再測一次", type="primary", use_container_width=True):
        reset_quiz()

# ==========================================
#              4. 主程式入口
# ==========================================

if st.session_state.quiz_started:
    show_quiz_page()
elif st.session_state.quiz_finished:
    show_result_page()
else:
    show_settings_page()





