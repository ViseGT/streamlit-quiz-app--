import streamlit as st
import json
import random
import requests 
from datetime import datetime

# 設定 Streamlit 頁面基礎配置
st.set_page_config(page_title="雲端題庫測驗系統", layout="centered")

# ==========================================
#              1. 雲端題庫設定
# ==========================================

BASE_URL = "https://raw.githubusercontent.com/ViseGT/streamlit-quiz-app--/main/"
FIXED_SUBJECT_NAME = "職業衛生管理師-測驗"

QUIZ_SOURCES = {
    FIXED_SUBJECT_NAME: BASE_URL + "%E8%81%B7%E6%A5%AD%E8%A1%9B%E7%94%9F%E7%AE%A1%E7%90%86%E5%B8%AB_%E5%85%A8%E9%83%A8%E9%A1%8C%E7%9B%AE.json",
    
    "1. 職業衛生管理學科 (22100)": BASE_URL + "22100_%E8%81%B7%E6%A5%AD%E8%A1%9B%E7%94%9F%E7%AE%A1%E7%90%86%E5%AD%B8%E7%A7%91.json",
    "2. 職業安全衛生共同科目 (90006)": BASE_URL + "90006_-%E8%81%B7%E6%A5%AD%E5%AE%89%E5%85%A8%E8%A1%9B%E7%94%9F%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "3. 工作倫理與職業道德 (90007)": BASE_URL + "90007_-%E5%B7%A5%E4%BD%9C%E5%80%AB%E7%90%86%E8%88%87%E8%81%B7%E6%A5%AD%E9%81%93%E5%BE%B7%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "4. 環境保護共同科目 (90008)": BASE_URL + "90008_-%E7%92%B0%E5%A2%83%E4%BF%9D%E8%AD%B7%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
    "5. 節能減碳共同科目 (90009)": BASE_URL + "90009_-%E7%AF%80%E8%83%BD%E6%B8%9B%E7%A2%B3%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE.json",
}

# 設定固定題數和預設題數
FIXED_SINGLE = "60"
FIXED_MULTI = "20"
DEFAULT_SINGLE = "20"
DEFAULT_MULTI = "5"

# ==========================================
#              2. 核心邏輯函數
# ==========================================

@st.cache_data(ttl=3600) 
def fetch_quiz_data(url):
    """從 GitHub 或其他網址讀取 JSON 資料"""
    try:
        response = requests.get(url)
        response.raise_for_status() 
        
        data = response.json()
        
        if isinstance(data, list):
            return data
        else:
            st.error(f"資料格式錯誤：預期為 List，但讀取到 {type(data)}")
            return []
            
    except json.JSONDecodeError as e:
        st.error(f"**讀取題庫失敗！ JSON 格式錯誤！**")
        st.caption(f"錯誤訊息：{e}")
        st.caption(f"請仔細檢查檔案中的 **Line {e.lineno} (大約 {e.pos} 字元處)** 是否缺少逗號 (`,`) 或有其他不合法的字元。")
        return []

    except Exception as e:
        st.error(f"**讀取題庫失敗！** 請檢查 GitHub 連結是否為 Raw 連結。錯誤訊息: {e}")
        return []

def init_session_state():
    """初始化狀態變數"""
    if 'questions' not in st.session_state: st.session_state.questions = []
    if 'current_index' not in st.session_state: st.session_state.current_index = 0
    if 'answers' not in st.session_state: st.session_state.answers = {} 
    if 'quiz_started' not in st.session_state: st.session_state.quiz_started = False
    if 'quiz_finished' not in st.session_state: st.session_state.quiz_finished = False
    if 'font_size' not in st.session_state: st.session_state.font_size = 20
    if 'errors' not in st.session_state: st.session_state.errors = []
    if 'current_subject' not in st.session_state: st.session_state.current_subject = ""
    # 初始化題數輸入的 Session State Key
    if 'quiz_num_single' not in st.session_state: st.session_state.quiz_num_single = DEFAULT_SINGLE
    if 'quiz_num_multi' not in st.session_state: st.session_state.quiz_num_multi = DEFAULT_MULTI

init_session_state()

def start_quiz(url, subject_name, num_single, num_multi):
    """下載資料並開始測驗"""
    
    with st.spinner(f"正在從雲端載入【{subject_name}】題庫，請稍候..."):
        all_qs = fetch_quiz_data(url)
    
    if not all_qs: return

    try:
        num_single = int(num_single)
        num_multi = int(num_multi)
    except ValueError:
        st.error("題數請輸入數字")
        return

    single_qs = [q for q in all_qs if q.get('type') == 'single']
    multi_qs = [q for q in all_qs if q.get('type') == 'multi']

    # 檢查題數是否足夠，並自動調整
    if num_single > len(single_qs): 
        st.warning(f"單選題庫存不足 (共 {len(single_qs)} 題)，已自動調整為最大值。")
        num_single = len(single_qs)
    if num_multi > len(multi_qs): 
        st.warning(f"多選題庫存不足 (共 {len(multi_qs)} 題)，已自動調整為最大值。")
        num_multi = len(multi_qs)

    if num_single + num_multi == 0:
        st.error("總題數為 0，無法開始測驗。")
        return

    # 抽題與亂序
    selected_questions = random.sample(single_qs, num_single) + random.sample(multi_qs, num_multi)
    random.shuffle(selected_questions)

    # 選項亂序處理 (保持原樣，不影響功能)
    for q in selected_questions:
        original_options = q["options"]
        original_answers = q["answer"]
        option_with_index = list(enumerate(original_options))
        random.shuffle(option_with_index)

        shuffled_options = []
        new_answer_indices = []
        for new_index, (old_index, opt_text) in enumerate(option_with_index):
            shuffled_options.append(opt_text)
            if (old_index + 1) in original_answers:  
                new_answer_indices.append(new_index + 1)

        q["options"] = shuffled_options
        q["answer"] = sorted(new_answer_indices)

    # 更新狀態
    st.session_state.questions = selected_questions
    st.session_state.answers = {}
    st.session_state.current_index = 0
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.current_subject = subject_name
    st.rerun()

# (其他函數如 save_current_answer, navigate_question, finish_quiz, reset_quiz 保持不變，省略以保持程式碼簡潔)

def save_current_answer():
    if not st.session_state.questions: return
    q_index = st.session_state.current_index
    q = st.session_state.questions[q_index]
    selected_indices = []
    
    if q['type'] == 'single':
        component_key = f'q_answer_{q_index}'
        current_answer = st.session_state.get(component_key)
        if isinstance(current_answer, str):
            try:
                index = int(current_answer.split(')')[0].strip('(')) 
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

def show_quiz_page():
    q_index = st.session_state.current_index
    q = st.session_state.questions[q_index]
    total_q = len(st.session_state.questions)
    
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
        
        export_data = []
        for err in st.session_state.errors:
            item = err.copy()
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
#              3. 頁面顯示 (修正題數邏輯)
# ==========================================

def show_settings_page():
    st.header("☁️ 雲端題庫測驗系統")
    st.caption("直接從 GitHub 讀取最新題庫，無需上傳檔案")

    # 1. 選擇科目
    subjects = list(QUIZ_SOURCES.keys())
    selected_subject = st.selectbox("請選擇測驗科目：", subjects)
    target_url = QUIZ_SOURCES[selected_subject]
    
    st.markdown("---")

    # 2. 設定題數 (修正邏輯: 強制覆寫 Session State)
    is_fixed_quiz = selected_subject == FIXED_SUBJECT_NAME

    st.subheader("抽題設定")
    
    if is_fixed_quiz:
        # 1. 鎖定並強制設定為 60/20，覆蓋 Session State
        st.session_state.quiz_num_single = FIXED_SINGLE
        st.session_state.quiz_num_multi = FIXED_MULTI
        disabled_state = True
        st.info(f"👉 選擇【{FIXED_SUBJECT_NAME}】，題數已自動設定為：單選 {FIXED_SINGLE} 題，多選 {FIXED_MULTI} 題 (共 {int(FIXED_SINGLE) + int(FIXED_MULTI)} 題)。")
    else:
        # 2. 切換到非固定科目時，檢查是否需重設回預設值
        if st.session_state.quiz_num_single == FIXED_SINGLE and st.session_state.quiz_num_multi == FIXED_MULTI:
             st.session_state.quiz_num_single = DEFAULT_SINGLE
             st.session_state.quiz_num_multi = DEFAULT_MULTI
        
        disabled_state = False
        
    # 3. 渲染輸入框 (會使用 Session State 中最新的值)
    col1, col2 = st.columns(2)
    with col1:
        # 由於 key 已經將 input 綁定到 Session State，這裡不需要 value 參數
        st.text_input("單選題數:", disabled=disabled_state, key="quiz_num_single")
    with col2:
        st.text_input("多選題數:", disabled=disabled_state, key="quiz_num_multi")


    # 4. 字體設定
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
        # 從 Session State 取得最終的題數 (不論是鎖定的 60/20 或是使用者輸入的)
        final_num_single = st.session_state.quiz_num_single
        final_num_multi = st.session_state.quiz_num_multi
        
        start_quiz(target_url, selected_subject, final_num_single, final_num_multi)

# ==========================================
#              4. 主程式入口
# ==========================================

if st.session_state.quiz_started:
    show_quiz_page()
elif st.session_state.quiz_finished:
    show_result_page()
else:
    show_settings_page()


