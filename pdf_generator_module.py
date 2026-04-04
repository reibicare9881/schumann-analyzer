from fpdf import FPDF
import os
import io
from pypdf import PdfWriter, PdfReader

def write_cjk_text(pdf, text, line_height=7):
    """專為中文字串設計的精準換行函數，徹底解決 multi_cell 的當機問題"""
    max_w = pdf.w - pdf.l_margin - pdf.r_margin - 2 # 留 2mm 緩衝區
    current_line = ""
    
    # 針對英文單字稍微優化的簡單處理
    words = text.split(' ') if ' ' in text else list(text)
    
    if ' ' in text: # 如果是英文句子 (包含空格)
        for word in words:
            if pdf.get_string_width(current_line + word + " ") > max_w:
                pdf.cell(0, line_height, txt=current_line, ln=True)
                current_line = word + " "
            else:
                current_line += word + " "
    else: # 如果是純中文 (無空格)
        for char in text:
            if pdf.get_string_width(current_line + char) > max_w:
                pdf.cell(0, line_height, txt=current_line, ln=True)
                current_line = char
            else:
                current_line += char
                
    if current_line.strip():
        pdf.cell(0, line_height, txt=current_line.strip(), ln=True)

# 🌟 新增 language 參數，預設為繁體中文
def create_full_report_pdf(sections, uploaded_file=None, language="繁體中文"):
    font_path = "NotoSansTC-Regular.ttf"
    has_font = os.path.exists(font_path)
    
    if not has_font:
        return None, False

    # 🌟 根據選擇的語言設定對應的標籤文字
    if language == "English":
        main_title_text = "Schumann Resonance Deep Analysis Report"
        lbl_element = "Element"
        lbl_chakra = "Chakra"
        lbl_meaning = "Meaning"
        lbl_status = "Status"
    else:
        main_title_text = "舒曼共振體驗結果深度解析報告"
        lbl_element = "五行"
        lbl_chakra = "脈輪"
        lbl_meaning = "含意"
        lbl_status = "狀態"

    pdf = FPDF()
    
    # 判斷上傳檔案的類型
    is_image = False
    is_pdf = False
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['png', 'jpg', 'jpeg']:
            is_image = True
        elif file_ext == 'pdf':
            is_pdf = True

    # 🌟 邏輯 A：如果是圖片，貼合在第一頁
    if is_image:
        pdf.add_page()
        temp_img_path = f"temp_upload_img.{file_ext}"
        with open(temp_img_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        pdf.image(temp_img_path, x=10, y=10, w=190, h=0)
        os.remove(temp_img_path) 

    # 🌟 新增一頁，開始寫入 AI 分析文字報告
    pdf.add_page()
    pdf.add_font('NotoSans', '', font_path)
    
    # --- 寫入大標題 ---
    pdf.set_font('NotoSans', '', 18)
    pdf.set_text_color(42, 90, 59) # 森林綠
    pdf.cell(0, 15, txt=main_title_text, align='C', ln=True)
    pdf.ln(5)
    
    # --- 迴圈寫入段落 ---
    for title, content in sections:
        # 🎨 為每個大段落加上有底色的質感標題
        pdf.set_font('NotoSans', '', 14)
        pdf.set_text_color(255, 255, 255) # 白字
        pdf.set_fill_color(79, 138, 101)  # 莫蘭迪綠底色
        pdf.cell(0, 10, txt=f"  {title} ", align='L', fill=True, ln=True)
        pdf.ln(3)
        
        # 清除影響排版的 Markdown 符號
        clean_content = content.replace("**", "").replace("* ", "• ")
        
        # 🌟 核心魔法：逐行解析並套用不同樣式
        lines = clean_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(2)
                continue
                
            # 🛠️ 攔截 1：將 Markdown 表格轉化為優雅的資訊卡片
            if line.startswith("|") and line.endswith("|"):
                if "---" in line:
                    continue 
                    
                cells = [c.strip() for c in line.strip("|").split("|")]
                
                # 跳過表頭 (同時檢查中文與英文的表頭關鍵字)
                if len(cells) >= 2 and ("顏色" in cells[0] or "Color" in cells[0]):
                    continue 
                    
                if len(cells) >= 5:
                    color, wuxing, chakra, meaning, status = cells[:5]
                    
                    # 顏色與屬性大標
                    pdf.set_font('NotoSans', '', 12)
                    pdf.set_text_color(42, 90, 59) 
                    write_cjk_text(pdf, f"✦ {color} ({lbl_element}: {wuxing} / {lbl_chakra}: {chakra})", line_height=8)
                    
                    # 含意與狀態內文
                    pdf.set_font('NotoSans', '', 11)
                    pdf.set_text_color(60, 60, 60)
                    write_cjk_text(pdf, f"  ▸ {lbl_meaning}: {meaning}", line_height=6)
                    write_cjk_text(pdf, f"  ▸ {lbl_status}: {status}", line_height=6)
                    pdf.ln(2)
                else:
                    pdf.set_font('NotoSans', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    write_cjk_text(pdf, " | ".join(cells), line_height=6)
                continue
            
            # 🛠️ 攔截 2：偵測 【次標題】 並獨立放大與變色
            if line.startswith("【") and "】" in line:
                end_idx = line.find("】") + 1
                title_part = line[:end_idx]
                rest_part = line[end_idx:].strip()
                
                # 印出放大的綠色標題
                pdf.set_font('NotoSans', '', 13)
                pdf.set_text_color(42, 90, 59) 
                write_cjk_text(pdf, title_part, line_height=8)
                
                # 印出後續的黑色內文
                if rest_part:
                    pdf.set_font('NotoSans', '', 12)
                    pdf.set_text_color(0, 0, 0)
                    write_cjk_text(pdf, rest_part, line_height=7)
            
            else:
                # 正常的一般內文
                pdf.set_font('NotoSans', '', 12)
                pdf.set_text_color(0, 0, 0)
                write_cjk_text(pdf, line, line_height=7)

        pdf.ln(5) # 每個大段落結束後，留出一點呼吸空間
        
    text_pdf_bytes = pdf.output()

    # 🌟 邏輯 B：合併 PDF
    if is_pdf:
        merger = PdfWriter()
        
        user_pdf = io.BytesIO(uploaded_file.getvalue())
        merger.append(user_pdf)
        
        text_pdf_io = io.BytesIO(text_pdf_bytes)
        merger.append(text_pdf_io)
        
        final_output = io.BytesIO()
        merger.write(final_output)
        merger.close()
        
        return final_output.getvalue(), True
        
    else:
        return bytes(text_pdf_bytes), True