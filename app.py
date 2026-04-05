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
from huggingface_hub import login

# ==========================================
# 0. 環境設定與樣式注入
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
# api_key = st.secrets["GEMINI_API_KEY"]

# 🌟 擴充版：包含國旗的四國語系字典 (Language Dictionary)
LANG_TEXT = {
    "🇹🇼 繁體中文": {
        "sidebar_title": "請上傳您的報告",
        "upload_label": "請選擇報告檔案",
        "file_ready": "檔案已就緒",
        "analyze_btn": " 啟動 AI 深度分析",
        "main_title": "舒曼共振身心靈 AI 解說報告",
        "subtitle": "透過量子共振數據，探索您內在的能量風景",
        "info_start": "請從左側上傳您的分析報告開始。",
        "expander_view": "🔍 檢視原始上傳文件",
        "pdf_error": "預覽 PDF 時發生錯誤:",
        "status_analyzing": " 正在分析報告...",
        "status_parsing": " 視覺辨識萃取中...",
        "status_writing": " AI 邏輯撰寫中...",
        "status_layout": " 報告排版中...",
        "status_complete": " 分析完成！",
        "toast_success": "報告已生成！",
        "error_prefix": "發生意外錯誤:",
        "expander_raw": " 查看 AI 萃取的原始數據 (檢查專用)",
        "metrics_title": "👤 體驗者能量看板",
        "name": "姓名", "gender": "性別", "age": "年齡", "date": "體驗日期",
        "subjective": "主觀狀態", "no_check": "無特別勾選", "not_provided": "未提供", "age_unit": " 歲",
        "tabs_title": "📈 深度 AI 能量解讀",
        "download_btn": "下載完整分析報告 (PDF)",
        "pdf_filename": "舒曼共振報告",
        "ref_title": "科學文獻與分析依據",
        "sections": ["心率變化分析", "心律變異(SDNN)分析", "自律神經平衡狀態", "自律神經動態象限解析", "體內陰陽能量比例", "天人合一指數", "生命之花圖譜分析", "整體修復建議"],
        "ref_text": """
        本報告之**心率變異度 (HRV)、SDNN (心跳變異標準差) 與 LF/HF (自律神經頻譜分析)** 等核心生理指標，其運算邏輯與臨床意義係基於以下國際公認之學術文獻與量測標準：

        1. **國際 HRV 量測黃金標準指南** 👉 [Heart rate variability: standards of measurement...](https://pubmed.ncbi.nlm.nih.gov/8598068/)
        2. **SDNN 與自律神經指標的現代臨床應用與常模解析** 👉 [An Overview of Heart Rate Variability Metrics and Norms.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/)
        3. **極低頻電磁場 (ELF) 對人體腦波與心率變異度之共振影響研究** 👉 [Schumann Resonances, a plausible biophysical mechanism...](https://pubmed.ncbi.nlm.nih.gov/11826883/)
        4. **HRV 作為壓力與健康生物標記之最新回顧與應用研究** 👉 [Heart Rate Variability as a Biomarker for Stress and Health...](https://www.mdpi.com/2076-3417/15/1/449)
        5. **HRV 與心理韌性、情緒能力及身體健康之相關性研究** 👉 [Heart Rate Variability as a Biomarker for Psychological Resilience...](https://doaj.org/article/e5c4600c4dc240709248dfbad75fcd13)
        
        > 💡 **系統宣告與免責聲明：** 上述文獻為本平台硬體擷取「心率、SDNN、LF/HF」之科學基礎。報告中之**「陰陽比例」、「天人合一指數」及「生命之花圖譜」**，為本系統結合東方經絡理療與能量醫學開發之專利視覺化演算法。本報告為輔助健康管理之用，不可替代專業醫療人員之診斷與治療。
        """
    },
    "🇺🇸 English": {
        "sidebar_title": "Upload Your Report",
        "upload_label": "Choose a report file",
        "file_ready": "File is ready",
        "analyze_btn": " Start AI Deep Analysis",
        "main_title": "Schumann Resonance AI Report",
        "subtitle": "Explore your inner energy landscape through quantum resonance data",
        "info_start": "Please upload your report from the left sidebar to begin.",
        "expander_view": "🔍 View Original Uploaded File",
        "pdf_error": "Error previewing PDF:",
        "status_analyzing": " Analyzing report...",
        "status_parsing": " Extracting visual data...",
        "status_writing": " Generating AI logic...",
        "status_layout": " Formatting report...",
        "status_complete": " Analysis Complete!",
        "toast_success": "Report Generated!",
        "error_prefix": "Unexpected error:",
        "expander_raw": " View Raw AI Extracted Data (For Check)",
        "metrics_title": "👤 Experiencer Energy Dashboard",
        "name": "Name", "gender": "Gender", "age": "Age", "date": "Exp. Date",
        "subjective": "Subjective Status", "no_check": "None checked", "not_provided": "N/A", "age_unit": " y/o",
        "tabs_title": "📈 Deep AI Interpretation",
        "download_btn": "Download Full Analysis Report (PDF)",
        "pdf_filename": "Schumann_Report",
        "ref_title": "Scientific Literature & Analysis Basis",
        "sections": ["Heart Rate Analysis", "HRV (SDNN) Analysis", "ANS Balance State", "ANS Dynamic Quadrant", "Yin-Yang Energy Ratio", "Unity Index", "Flower of Life Analysis", "Overall Healing Suggestions"],
        "ref_text": """
        The core physiological indicators in this report, such as **Heart Rate Variability (HRV), SDNN, and LF/HF**, are based on the following internationally recognized academic literature and measurement standards:

        1. **International HRV Measurement Golden Standard** 👉 [Heart rate variability: standards...](https://pubmed.ncbi.nlm.nih.gov/8598068/)
        2. **Modern Clinical Application and Norms of SDNN and ANS Indicators** 👉 [An Overview of Heart Rate...](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/)
        3. **Resonance Effects of ELF on Human EEG and HRV** 👉 [Schumann Resonances, a plausible...](https://pubmed.ncbi.nlm.nih.gov/11826883/)
        4. **Latest Review of HRV as a Biomarker for Stress and Health** 👉 [Heart Rate Variability...](https://www.mdpi.com/2076-3417/15/1/449)
        5. **Correlation of HRV with Psychological Resilience and Health** 👉 [Heart Rate Variability...](https://doaj.org/article/e5c4600c4dc240709248dfbad75fcd13)
        
        > 💡 **System Declaration & Disclaimer:** The above literature provides the scientific basis for the hardware extraction of "Heart Rate, SDNN, LF/HF". The **"Yin-Yang Ratio," "Unity Index," and "Flower of Life"** are proprietary visual algorithms developed by combining Eastern meridian therapy and energy medicine. This report is intended for health management assistance and cannot replace professional medical diagnosis and treatment.
        """
    },
    "🇨🇳 簡體中文": {
        "sidebar_title": "请上传您的报告",
        "upload_label": "请选择报告文件",
        "file_ready": "文件已就绪",
        "analyze_btn": " 启动 AI 深度分析",
        "main_title": "舒曼共振身心灵 AI 解说报告",
        "subtitle": "透过量子共振数据，探索您内在的能量风景",
        "info_start": "请从左侧上传您的分析报告开始。",
        "expander_view": "🔍 检视原始上传文件",
        "pdf_error": "预览 PDF 时发生错误:",
        "status_analyzing": " 正在分析报告...",
        "status_parsing": " 视觉辨识萃取中...",
        "status_writing": " AI 逻辑撰写中...",
        "status_layout": " 报告排版中...",
        "status_complete": " 分析完成！",
        "toast_success": "报告已生成！",
        "error_prefix": "发生意外错误:",
        "expander_raw": " 查看 AI 萃取的原始数据 (检查专用)",
        "metrics_title": "👤 体验者能量看板",
        "name": "姓名", "gender": "性别", "age": "年龄", "date": "体验日期",
        "subjective": "主观状态", "no_check": "无特别勾选", "not_provided": "未提供", "age_unit": " 岁",
        "tabs_title": "📈 深度 AI 能量解读",
        "download_btn": "下载完整分析报告 (PDF)",
        "pdf_filename": "舒曼共振报告",
        "ref_title": "科学文献与分析依据",
        "sections": ["心率变化分析", "心律变异(SDNN)分析", "自律神经平衡状态", "自律神经动态象限解析", "体内阴阳能量比例", "天人合一指数", "生命之花图谱分析", "整体修复建议"],
        "ref_text": """
        本报告之**心率变异度 (HRV)、SDNN (心跳变异标准差) 与 LF/HF (自律神经频谱分析)** 等核心生理指标，其运算逻辑与临床意义系基于以下国际公认之学术文献与量测标准：

        1. **国际 HRV 量测黄金标准指南** 👉 [Heart rate variability: standards...](https://pubmed.ncbi.nlm.nih.gov/8598068/)
        2. **SDNN 与自律神经指标的现代临床应用与常模解析** 👉 [An Overview of Heart Rate...](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/)
        3. **极低频电磁场 (ELF) 对人体脑波与心率变异度之共振影响研究** 👉 [Schumann Resonances, a plausible...](https://pubmed.ncbi.nlm.nih.gov/11826883/)
        4. **HRV 作为压力与健康生物标记之最新回顾与应用研究** 👉 [Heart Rate Variability...](https://www.mdpi.com/2076-3417/15/1/449)
        5. **HRV 与心理韧性、情绪能力及身体健康之相关性研究** 👉 [Heart Rate Variability...](https://doaj.org/article/e5c4600c4dc240709248dfbad75fcd13)
        
        > 💡 **系统宣告与免责声明：** 上述文献为本平台硬体撷取「心率、SDNN、LF/HF」之科学基础。报告中之**「阴阳比例」、「天人合一指数」及「生命之花图谱」**，为本系统结合东方经络理疗与能量医学开发之专利视觉化演算法。本报告为辅助健康管理之用，不可替代专业医疗人员之诊断与治疗。
        """
    },
    "🇯🇵 日本語": {
        "sidebar_title": "レポートをアップロード",
        "upload_label": "ファイルを選択してください",
        "file_ready": "ファイルの準備が完了しました",
        "analyze_btn": " AIディープ分析を開始",
        "main_title": "シューマン共振 心身AI解説レポート",
        "subtitle": "量子共鳴データを通じて、あなたの内なるエネルギーの風景を探求します",
        "info_start": "左側のサイドバーから分析レポートをアップロードして開始してください。",
        "expander_view": "🔍 アップロードした元ファイルを表示",
        "pdf_error": "PDFプレビューエラー:",
        "status_analyzing": " レポートを分析中...",
        "status_parsing": " 視覚データを抽出中...",
        "status_writing": " AIロジックを構築中...",
        "status_layout": " レポートをフォーマット中...",
        "status_complete": " 分析完了！",
        "toast_success": "レポートが作成されました！",
        "error_prefix": "予期せぬエラーが発生しました:",
        "expander_raw": " AI抽出の生データを確認 (検証用)",
        "metrics_title": "👤 体験者エネルギーダッシュボード",
        "name": "氏名", "gender": "性別", "age": "年齢", "date": "体験日",
        "subjective": "主観的状態", "no_check": "選択なし", "not_provided": "未提供", "age_unit": " 歳",
        "tabs_title": "📈 AI 深層エネルギー解読",
        "download_btn": "完全版分析レポートをダウンロード (PDF)",
        "pdf_filename": "シューマン共振レポート",
        "ref_title": "科学的文献と分析の根拠",
        "sections": ["心拍数変化分析", "心拍変動(SDNN)分析", "自律神経バランス状態", "自律神経動態象限解析", "体内陰陽エネルギー比率", "天人合一指数", "フラワーオブライフ図譜分析", "総合ヒーリングアドバイス"],
        "ref_text": """
        本レポートにおける**心拍変動 (HRV)、SDNN、LF/HF (自律神経スペクトル分析)** などの主要な生理学的指標は、以下の国際的に認められた学術文献および測定基準に基づいています：

        1. **国際HRV測定ゴールデンスタンダード** 👉 [Heart rate variability: standards...](https://pubmed.ncbi.nlm.nih.gov/8598068/)
        2. **SDNNと自律神経指標の現代的臨床応用と基準** 👉 [An Overview of Heart Rate...](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/)
        3. **極低周波電磁界 (ELF) がヒトの脳波およびHRVに与える共鳴効果の研究** 👉 [Schumann Resonances, a plausible...](https://pubmed.ncbi.nlm.nih.gov/11826883/)
        4. **ストレスと健康のバイオマーカーとしてのHRVに関する最新レビュー** 👉 [Heart Rate Variability...](https://www.mdpi.com/2076-3417/15/1/449)
        5. **HRVと心理的レジリエンス、健康の相関関係に関する研究** 👉 [Heart Rate Variability...](https://doaj.org/article/e5c4600c4dc240709248dfbad75fcd13)
        
        > 💡 **システム宣言および免責事項：** 上記の文献は、当システムのハードウェアが抽出する「心拍数、SDNN、LF/HF」の科学的根拠となります。レポート内の**「陰陽比率」「天人合一指数」「フラワーオブライフ」**は、東洋の経絡療法とエネルギー医学を組み合わせた当システム独自の視覚化アルゴリズムです。本レポートは健康管理の補助を目的としており、専門医療従事者による診断および治療に代わるものではありません。
        """
    }
}

def format_ai_text(text):
    if not isinstance(text, str):
        return text
    text = text.replace("】：|", "】\n\n|").replace("】 ： |", "】\n\n|")
    text = text.replace("###", "").replace("**", "").strip()
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
    /* 引入多國語言字體 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        /* 讓瀏覽器依序尋找合適的字體 */
        font-family: 'Noto Sans TC', 'Noto Sans SC', 'Noto Sans JP', sans-serif; 
    }
    .main { background-color: #F7F9F8; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); border: 1px solid #F0F2F5; transition: transform 0.2s ease; }
    .stMetric:hover { transform: translateY(-2px); }
    .report-card { background-color: #ffffff; padding: 30px; border-radius: 16px; border-left: 6px solid #4F8A65; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04); margin-bottom: 24px; line-height: 1.8; color: #333333; font-size: 1.05rem; }
    .section-title { color: #2A5A3B; font-weight: 700; margin-top: 25px; margin-bottom: 15px; letter-spacing: 0.5px; }
    .stButton>button { width: 100%; border-radius: 30px; height: 3.2em; background: linear-gradient(135deg, #4F8A65 0%, #3A7D44 100%); color: white; font-weight: 600; letter-spacing: 1px; border: none; box-shadow: 0 4px 10px rgba(79, 138, 101, 0.3); transition: all 0.3s ease; }
    .stButton>button:hover { box-shadow: 0 6px 15px rgba(79, 138, 101, 0.4); transform: translateY(-2px); }
    @media (max-width: 768px) {
        .header-container { flex-direction: column !important; text-align: center !important; align-items: center !important; }
        .header-logo { margin-right: 0 !important; margin-bottom: 15px !important; width: 65px !important; }
        .header-title { font-size: 1.6rem !important; }
        .header-subtitle { font-size: 0.95rem !important; }
        .report-card { padding: 20px !important; font-size: 1rem !important; }
        div[data-testid="stTable"] { overflow-x: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🌟 新增：手機版桌面 App 圖示 (PWA / Add to Home Screen)
# ==========================================
if logo_base64:
    st.markdown(f"""
        <link rel="apple-touch-icon" href="data:image/jpg;base64,{logo_base64}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="REIBI 舒曼體驗AI 解讀">
        <link rel="icon" type="image/jpg" sizes="192x192" href="data:image/jpg;base64,{logo_base64}">
    """, unsafe_allow_html=True)

def reset_app_state():
    for key in ["analysis_done", "display_data", "sections", "pdf_bytes"]:
        if key in st.session_state:
            del st.session_state[key]

# ==========================================
# 1. 側邊欄 (Sidebar) - 配置與上傳
# ==========================================
with st.sidebar:
    # 🌟 語言選擇器更新：加入國旗與四個選項
    target_lang = st.selectbox(
        "🌐 Language / 語言", 
        ["🇹🇼 繁體中文", "🇨🇳 簡體中文", "🇯🇵 日本語", "🇺🇸 English"], 
        index=0, 
        on_change=reset_app_state
    )
    L = LANG_TEXT[target_lang]

    st.title(L["sidebar_title"])
    
    if not api_key:
        st.error("⚠️ 未偵測到 API Key" if "中文" in target_lang else "⚠️ API Key not detected")
        st.stop()

    uploaded_file = st.file_uploader(
        L["upload_label"], 
        type=["pdf", "png", "jpg", "jpeg"],
        on_change=reset_app_state
    )
    
    if uploaded_file:
        st.success(L["file_ready"])
        analyze_btn = st.button(L["analyze_btn"])
    
    st.markdown("---")
    st.caption("v2.5 Professional Edition")

# ==========================================
# 2. 主畫面渲染
# ==========================================
logo_base64 = get_base64_image("reibi_logo.jpg")

if logo_base64:
    st.markdown(
        f"""
        <div class="header-container" style="display: flex; align-items: center; margin-bottom: 25px;">
            <img src="data:image/jpeg;base64,{logo_base64}" class="header-logo" width="80" style="margin-right: 25px;">
            <div>
                <h1 class="header-title" style="margin: 0; color: #2A5A3B; line-height: 1.2;">{L["main_title"]}</h1>
                <h5 class="header-subtitle" style="margin: 0; color: #666; font-weight: 400;">{L["subtitle"]}</h5>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(f"# 🌿 {L['main_title']}")
    st.markdown(f"##### {L['subtitle']}")

if uploaded_file is None:
    st.info(L["info_start"])
else:
    with st.expander(L["expander_view"]):
        if uploaded_file.name.lower().endswith('.pdf'):
            try:
                doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    # 依據語系決定頁碼顯示
                    page_text = f"Page {page_num + 1}" if target_lang == "🇺🇸 English" else (f"ページ {page_num + 1}" if target_lang == "🇯🇵 日本語" else f"第 {page_num + 1} 頁")
                    st.image(img, caption=page_text, width='stretch')
            except Exception as e:
                st.error(f"{L['pdf_error']} {e}")
        else:
            st.image(uploaded_file, width='stretch')

    # 運算邏輯
    if 'analyze_btn' in locals() and analyze_btn:
        try:
            with st.status(L["status_analyzing"], expanded=True) as status:

                # ==========================================
                # 🌟 新增：從複雜檔名精準擷取體驗者姓名
                # 範例：record_林偉仁_07-08-2019_BL84.pdf
                # ==========================================
                file_name_with_ext = uploaded_file.name
                file_name_only = os.path.splitext(file_name_with_ext)[0] 
                
                extracted_name = None
                
                # 按照底線將檔名切成一塊一塊的清單
                # ['record', '林偉仁', '07-08-2019', 'BL84', ...]
                parts = file_name_only.split('_')
                
                # 檢查：如果切出來的區塊大於兩個，而且第一個區塊是 "record"
                if len(parts) >= 2 and parts[0] == "record":
                    # 抓取清單中的第二個區塊（程式碼索引是從 0 開始，所以 [1] 是第二個）
                    extracted_name = parts[1]
                # ==========================================
                
                st.write(L["status_parsing"])
                parsed_data = parse_schumann_report(uploaded_file, api_key)

                # 🌟 攔截並強制覆寫 AI 的結果
                if extracted_name:
                    parsed_data["Name"] = extracted_name
                
                st.write(L["status_writing"])
                analysis_result = generate_ai_explanation(parsed_data, api_key, language=target_lang)
                
                st.write(L["status_layout"])
                sections = [
                    (L["sections"][0], analysis_result.get("section_1", "")),
                    (L["sections"][1], analysis_result.get("section_2", "")),
                    (L["sections"][2], analysis_result.get("section_3", "")),
                    (L["sections"][3], analysis_result.get("section_4", "")),
                    (L["sections"][4], analysis_result.get("section_5", "")),
                    (L["sections"][5], analysis_result.get("section_6", "")),
                    (L["sections"][6], analysis_result.get("section_7", "")),
                    (L["sections"][7], analysis_result.get("section_8", ""))
                ]
                uploaded_file.seek(0)
                pdf_bytes, _ = create_full_report_pdf(sections, uploaded_file, language=target_lang)
                
                status.update(label=L["status_complete"], state="complete", expanded=False)

            st.session_state["analysis_done"] = True
            st.session_state["display_data"] = parsed_data
            st.session_state["sections"] = sections
            st.session_state["pdf_bytes"] = pdf_bytes
            st.toast(L["toast_success"], icon="🌿")

        except Exception as e:
            error_msg = str(e).lower()
            # 🌟 攔截 Gemini 免費額度爆表的 429 錯誤
            if "429" in error_msg and "quota" in error_msg:
                if "繁體中文" in target_lang:
                    st.error("⚠️ 目前免費額度已滿，請稍後再試或更換 API 金鑰。")
                elif "簡體中文" in target_lang:
                    st.error("⚠️ 目前免费额度已满，请稍后再试或更换 API 密钥。")
                elif "日本語" in target_lang:
                    st.error("⚠️ 現在、無料利用枠の上限に達しています。後でもう一度お試しください。")
                else:
                    st.error("⚠️ The free quota has been exceeded. Please try again later.")
            else:
                # 如果是其他錯誤，就照常印出
                st.error(f"{L['error_prefix']} {e}")

    # ==========================================
    # 3. 顯示結果 (Dashboard 模式)
    # ==========================================
    if st.session_state.get("analysis_done"):
        user_data = st.session_state["display_data"]
        
        with st.expander(L["expander_raw"]):
            st.json(user_data)
        
        raw_date = user_data.get("Experience_Date", L["not_provided"])
        formatted_date = L["not_provided"]
        
        if raw_date != L["not_provided"]:
            try:
                parts = raw_date.split('-')
                if len(parts) == 3:
                    formatted_date = f"{parts[2]}-{parts[0]}-{parts[1]}"
                else:
                    formatted_date = raw_date
            except:
                formatted_date = raw_date

        st.markdown(f"<h3 class='section-title'>{L['metrics_title']}</h3>", unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric(L["name"], user_data.get("Name", L["not_provided"]))
        with m_col2:
            st.metric(L["gender"], user_data.get("Gender", L["not_provided"]))
        with m_col3:
            age_val = user_data.get("Age", L["not_provided"])
            st.metric(L["age"], f"{age_val}{L['age_unit']}" if str(age_val).isdigit() else age_val)
        with m_col4:
            st.metric(L["date"], formatted_date)

        st.info(f"** {L['subjective']}：** {user_data.get('Subjective_Conditions', L['no_check'])}")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<h3 class='section-title'>{L['tabs_title']}</h3>", unsafe_allow_html=True)
        
        tab_titles = [s[0] for s in st.session_state["sections"]]
        tabs = st.tabs(tab_titles)

        for i, tab in enumerate(tabs):
            with tab:
                content = st.session_state["sections"][i][1]
                formatted_content = format_ai_text(content)
                st.markdown(f"<div class='report-card'>{formatted_content}</div>", unsafe_allow_html=True)

        dl_name = user_data.get("Name", "Report")
        st.download_button(
            label=L["download_btn"],
            data=st.session_state["pdf_bytes"],
            file_name=f"{L['pdf_filename']}_{dl_name}.pdf",
            mime="application/pdf",
            width='stretch'
        )

        st.markdown("---")
        st.markdown(f"### {L['ref_title']}")
        st.markdown(L["ref_text"])