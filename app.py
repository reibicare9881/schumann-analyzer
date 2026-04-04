import streamlit as st
import os
import base64
import re
import fitz  # PyMuPDF 套件
from PIL import Image
from dotenv import load_dotenv

from parser_module import parse_schumann_report
from ai_analyzer_module import generate_ai_explanation
from pdf_generator_module import create_full_report_pdf 

# ==========================================
# 0. 環境設定與樣式注入
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def format_ai_text(text):
    if not isinstance(text, str):
        return text
    
    # 1. ⚠️【關鍵修正】移除之前建議的 .replace(" ", "")，這會殺死表格！
    # 我們改為只針對標題與表格的連接處做處理
    
    # 2. 強制在表格開始符號「|」前面加上兩個換行符號
    # 這是為了確保 Markdown 引擎能識別這是一個新的表格區塊
    text = text.replace("】：|", "】\n\n|").replace("】 ： |", "】\n\n|")
    
    # 3. 清理 Markdown 殘留符號
    text = text.replace("###", "").replace("**", "").strip()
    
    # 4. 標題美化 (將 【標題】 轉換為綠色大標題)
    # 使用正則表達式，確保標題前後有足夠的換行
    html_title_style = r'<div style="font-size: 1.25rem; font-weight: 800; color: #2A5A3B; margin-top: 24px; margin-bottom: 12px;">\1</div>'
    formatted_text = re.sub(r'(【.*?】)', html_title_style, text)
    
    return formatted_text

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
logo_base64 = get_base64_image("reibi_logo.jpg")
    
st.set_page_config(page_title="舒曼共振 AI 解說平台", layout="wide", page_icon="reibi_logo.jpg")

st.markdown("""
    <style>
    /* 1. 全局字體與背景柔化 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }
    .main {
        background-color: #F7F9F8;
    }

    /* 2. 數據看板 (Metrics) 的輕盈感 */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        border: 1px solid #F0F2F5;
        transition: transform 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
    }

    /* 3. AI 解說報告卡的閱讀體驗優化 */
    .report-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 16px;
        border-left: 6px solid #4F8A65;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
        line-height: 1.8;
        color: #333333;
        font-size: 1.05rem;
    }

    /* 4. 標題層次感 */
    .section-title {
        color: #2A5A3B;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
        letter-spacing: 0.5px;
    }

    /* 5. 漸層按鈕與立體互動 */
    .stButton>button {
        width: 100%;
        border-radius: 30px;
        height: 3.2em;
        background: linear-gradient(135deg, #4F8A65 0%, #3A7D44 100%);
        color: white;
        font-weight: 600;
        letter-spacing: 1px;
        border: none;
        box-shadow: 0 4px 10px rgba(79, 138, 101, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 15px rgba(79, 138, 101, 0.4);
        transform: translateY(-2px);
    }

    /* 📱 6. 手機版專屬響應式優化 (Responsive) */
    @media (max-width: 768px) {
        /* Header 切換為上下垂直排列 */
        .header-container {
            flex-direction: column !important;
            text-align: center !important;
            align-items: center !important;
        }
        .header-logo {
            margin-right: 0 !important;
            margin-bottom: 15px !important;
            width: 65px !important; /* 手機版 Logo 縮小一點 */
        }
        .header-title {
            font-size: 1.6rem !important; /* 標題字體縮小 */
        }
        .header-subtitle {
            font-size: 0.95rem !important;
        }
        
        /* 報告卡片在手機版縮減間距，增加閱讀空間 */
        .report-card {
            padding: 20px !important;
            font-size: 1rem !important;
        }

        /* 防止表格撐破版面，允許橫向滑動 */
        div[data-testid="stTable"] {
            overflow-x: auto;
        }
    }
    </style>
    """, unsafe_allow_html=True)

KEY_MAPPING = {
    "Name": "姓名", "Gender": "體驗者性別", "Age": "年齡", "Occupation": "職業",
    "Experience_Date": "體驗日期", "Music": "播放音樂", "Subjective_Conditions": "主觀壓力與身體狀況",
    "Experience_Time_Sec": "體驗總秒數", "Unity_Index": "天人合一指數", "Balance_Count": "平衡次數",
    "HR_Pre": "體驗前心率", "HR_Post": "體驗後心率", "HR_Lowest": "過程中最低心率", "HR_Conclusion": "心率官方判定",
    "SDNN_Pre": "體驗前SDNN", "SDNN_Post": "體驗後SDNN","SDNN_Lowest_Trend": "SDNN波形最低點觀察", "SDNN_Conclusion": "SDNN官方判定",
    "LF_HF_Value": "LF-HF數值", "LF_HF_Conclusion": "LF/HF官方判定", "LF_HF_Trend": "LF/HF平衡狀態",
    "Yin_Yang": "陰陽比例", "Flower_of_Life_Colors": "生命之花：主要顏色",
    "Flower_of_Life_Brightness_Detail": "各色明暗程度",
    "Flower_of_Life_Brightness": "整體的明暗調性",
    "Flower_of_Life_Shape": "生命之花：花形結構",
    "Flower_of_Life_Extent": "生命之花：空間佔比",
    "Scatter_Plot_Analysis":"40分鐘象限分布圖"
}

def reset_app_state():
    for key in ["analysis_done", "display_data", "sections", "pdf_bytes"]:
        if key in st.session_state:
            del st.session_state[key]

# ==========================================
# 1. 側邊欄 (Sidebar) - 配置與上傳
# ==========================================
with st.sidebar:
    st.title("請上傳您的報告")
    
    if not api_key:
        st.error("⚠️ 未偵測到 API Key")
        st.stop()

    uploaded_file = st.file_uploader(
        "請選擇報告檔案", 
        type=["pdf", "png", "jpg", "jpeg"],
        on_change=reset_app_state
    )
    
    if uploaded_file:
        st.success("檔案已就緒")
        analyze_btn = st.button(" 啟動 AI 深度分析")
    
    st.markdown("---")
    st.caption("v2.5 Professional Edition")

# ==========================================
# 2. 主畫面渲染
# ==========================================
logo_base64 = get_base64_image("reibi_logo.jpg")

# 🌟 加上 class 讓 CSS 可以控制手機版排版
if logo_base64:
    st.markdown(
        f"""
        <div class="header-container" style="display: flex; align-items: center; margin-bottom: 25px;">
            <img src="data:image/jpeg;base64,{logo_base64}" class="header-logo" width="80" style="margin-right: 25px;">
            <div>
                <h1 class="header-title" style="margin: 0; color: #2A5A3B; line-height: 1.2;">舒曼共振身心靈 AI 解說報告</h1>
                <h5 class="header-subtitle" style="margin: 0; color: #666; font-weight: 400;">透過量子共振數據，探索您內在的能量風景</h5>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # 如果 Logo 讀取失敗，顯示原本的文字標題作為備案
    st.markdown("# 🌿 舒曼共振身心靈 AI 解說報告")
    st.markdown("##### 透過量子共振數據，探索您內在的能量風景")

if uploaded_file is None:
    st.info("請從左側上傳您的分析報告開始。")
    # 展示一張範例圖或說明文字...
else:
    # 預覽區域
    with st.expander("🔍 檢視原始上傳文件"):
    # 判斷如果是 PDF 檔案
        if uploaded_file.name.lower().endswith('.pdf'):
            try:
                # 使用 PyMuPDF 將 PDF 轉成圖片顯示，絕對防封鎖！
                doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150) # 設定 dpi=150 讓畫面保持清晰
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, caption=f"第 {page_num + 1} 頁", use_container_width=True)
            except Exception as e:
                st.error(f"預覽 PDF 時發生錯誤: {e}")
    
        # 如果是普通的圖片檔案 (png, jpg 等)
        else:
            st.image(uploaded_file, use_container_width=True)

    # 運算邏輯
    if 'analyze_btn' in locals() and analyze_btn:
        try:
            with st.status(" 正在分析報告...", expanded=True) as status:
                st.write(" 視覺辨識萃取中...")
                parsed_data = parse_schumann_report(uploaded_file, api_key)
                
                st.write(" AI 邏輯撰寫中...")
                analysis_result = generate_ai_explanation(parsed_data, api_key)
                
                st.write(" 報告排版中...")
                sections = [
                    ("心率變化分析", analysis_result.get("section_1", "")),
                    ("心律變異(SDNN)分析", analysis_result.get("section_2", "")),
                    ("自律神經平衡狀態", analysis_result.get("section_3", "")),
                    ("自律神經動態象限解析", analysis_result.get("section_4", "")),
                    ("體內陰陽能量比例", analysis_result.get("section_5", "")),
                    ("天人合一指數", analysis_result.get("section_6", "")),
                    ("生命之花圖譜分析", analysis_result.get("section_7", "")),
                    ("整體修復建議", analysis_result.get("section_8", ""))
                ]
                uploaded_file.seek(0)
                pdf_bytes, _ = create_full_report_pdf(sections, uploaded_file)
                
                status.update(label=" 分析完成！", state="complete", expanded=False)

            st.session_state["analysis_done"] = True
            st.session_state["display_data"] = {KEY_MAPPING.get(k, k): v for k, v in parsed_data.items()}
            st.session_state["sections"] = sections
            st.session_state["pdf_bytes"] = pdf_bytes
            st.toast("報告已生成！", icon="🌿")

        except Exception as e:
            st.error(f"發生意外錯誤: {e}")

    # ==========================================
    # 3. 顯示結果 (Dashboard 模式)
    # ==========================================
    if st.session_state.get("analysis_done"):
        user_data = st.session_state["display_data"]
        
        # 🌟 加回這裡：讓開發者與使用者可以隨時點開檢查 AI 萃取的原始 JSON 數據
        with st.expander(" 查看 AI 萃取的原始數據 (開發與檢查專用)"):
            st.json(user_data)
        
        # --- 🌟 日期格式化處理 (將 MM-DD-YYYY 轉換為 YYYY-MM-DD) ---
        raw_date = user_data.get("體驗日期", "未提供")
        formatted_date = "未提供"
        
        if raw_date != "未提供":
            try:
                # 原始報告日期格式通常為 07-30-2019
                parts = raw_date.split('-')
                if len(parts) == 3:
                    # 重新排列為 2019-07-30
                    formatted_date = f"{parts[2]}-{parts[0]}-{parts[1]}"
                else:
                    formatted_date = raw_date
            except:
                formatted_date = raw_date

        # --- 第一層：數據看板 (Metrics Dashboard) ---
        # 這裡移除了「體驗總秒數」與「播放音樂」，並將資訊整合為一排
        st.markdown("<h3 class='section-title'>👤 體驗者能量看板</h3>", unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("姓名", user_data.get("姓名", "未提供"))
        with m_col2:
            st.metric("性別", user_data.get("體驗者性別", "未提供"))
        with m_col3:
            age_val = user_data.get("年齡", "未提供")
            st.metric("年齡", f"{age_val} 歲" if str(age_val).isdigit() else age_val)
        with m_col4:
            st.metric("體驗日期", formatted_date)

        # 顯示主觀狀態
        st.info(f"** 主觀狀態：** {user_data.get('主觀壓力與身體狀況', '無特別勾選')}")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- 第二層：分頁顯示解說報告 (Tabs) ---
        # (此部分保持不變)
        st.markdown("<h3 class='section-title'>📈 深度 AI 能量解讀</h3>", unsafe_allow_html=True)
        
        tab_titles = [s[0] for s in st.session_state["sections"]]
        tabs = st.tabs(tab_titles)

        for i, tab in enumerate(tabs):
            with tab:
                # 1. 取出 AI 寫好的原始內容
                content = st.session_state["sections"][i][1]
                
                # 2. 🌟 呼叫我們在最上方寫好的「文字濾水器」，強迫變成綠色大標題
                formatted_content = format_ai_text(content)
                
                # 3. 丟進具備高級陰影與圓角的 report-card 容器中渲染
                st.markdown(f"<div class='report-card'>{formatted_content}</div>", unsafe_allow_html=True)

        # 下載按鈕與底部文獻保持不變...

        # 下載按鈕
        st.download_button(
            label="下載完整分析報告 (PDF)",
            data=st.session_state["pdf_bytes"],
            file_name=f"舒曼共振報告_{user_data.get('姓名')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        # --- 第四層：科學文獻與分析依據 (更新後的完整 5 篇) ---
        st.markdown("---")
        st.markdown("### 科學文獻與分析依據")
        st.markdown("""
        本報告之**心率變異度 (HRV)、SDNN (心跳變異標準差) 與 LF/HF (自律神經頻譜分析)** 等核心生理指標，其運算邏輯與臨床意義係基於以下國際公認之學術文獻與量測標準：

        1. **國際 HRV 量測黃金標準指南** 👉 [Heart rate variability: standards of measurement...](https://pubmed.ncbi.nlm.nih.gov/8598068/)
        2. **SDNN 與自律神經指標的現代臨床應用與常模解析** 👉 [An Overview of Heart Rate Variability Metrics and Norms.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/)
        3. **極低頻電磁場 (ELF) 對人體腦波與心率變異度之共振影響研究** 👉 [Schumann Resonances, a plausible biophysical mechanism...](https://pubmed.ncbi.nlm.nih.gov/11826883/)
        4. **HRV 作為壓力與健康生物標記之最新回顧與應用研究** 👉 [Heart Rate Variability as a Biomarker for Stress and Health...](https://www.mdpi.com/2076-3417/15/1/449)
        5. **HRV 與心理韌性、情緒能力及身體健康之相關性研究** 👉 [Heart Rate Variability as a Biomarker for Psychological Resilience...](https://doaj.org/article/e5c4600c4dc240709248dfbad75fcd13)
        
        > 💡 **系統宣告與免責聲明：** 上述文獻為本平台硬體擷取「心率、SDNN、LF/HF」之科學基礎。報告中之**「陰陽比例」、「天人合一指數」及「生命之花圖譜」**，為本系統結合東方經絡理療與能量醫學開發之專利視覺化演算法。本報告為輔助健康管理之用，不可替代專業醫療人員之診斷與治療。
        """)