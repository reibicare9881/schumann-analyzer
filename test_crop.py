import fitz  # PyMuPDF
from PIL import Image
import io
import os

# ---------------------------------------------------------
# 貼上您原本的轉換與裁切函數
# ---------------------------------------------------------
def convert_pdf_to_images(file_stream):
    """將 PDF 轉為圖片 (模擬 Streamlit 上傳的檔案流)"""
    file_stream.seek(0)
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150) # 確保與正式環境解析度一致
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            images.append(image)
        return images
    except Exception as e:
        print(f"PDF 轉換失敗: {e}")
        return []

def crop_focus_regions(main_image):
    """
    動態裁切三個局部區塊
    ⚠️ 測試時，請主要微調這裡的 4 個數字 (左, 上, 右, 下)
    """
    width, height = main_image.size
    print(f"👉 載入全圖尺寸: 寬 {width} x 高 {height} 像素")

    # 預估座標，請根據輸出的圖片結果進行微調
    box_personal = (80, 90, 890, 165)
    box_subjective = (80, 165, 900, 230)   # 左上角
    box_flower = (890, 290, 1180, 510)      # 右上角
    box_scatter = (900, 90, 1180, 290)   # 右側中段
    box_lf_hf = (35, 1095, 1140, 1470)
    box_hr = (35, 535, 1135, 810)
    box_sdnn = (35, 815, 1135, 1090)
    box_yinyang = (38, 1468, 1140, 1725)
    box_tianren = (230, 515, 930, 540)
    
    img_personal = main_image.crop(box_personal)
    img_subj = main_image.crop(box_subjective)
    img_flower = main_image.crop(box_flower)
    img_scatter = main_image.crop(box_scatter)
    img_lf_hf = main_image.crop(box_lf_hf)
    img_hr = main_image.crop(box_hr)
    img_sdnn = main_image.crop(box_sdnn)
    img_yinyang = main_image.crop(box_yinyang)
    img_tianren = main_image.crop(box_tianren)
        
        
    return [img_personal, img_subj, img_flower, img_scatter, img_lf_hf, img_hr ,img_sdnn, img_yinyang, img_tianren]

# ---------------------------------------------------------
# 測試執行區塊
# ---------------------------------------------------------
if __name__ == "__main__":
    # ⚠️ 這裡換成您資料夾裡實際的 PDF 測試檔名
    test_pdf_filename = "record_伍芳儀_07-30-2019_BL28_LH8_MF77.txt.pdf" 
    
    output_folder = "test_cropped_images"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(test_pdf_filename):
        print(f"❌ 找不到測試檔案：{test_pdf_filename}")
    else:
        print(f"🚀 開始測試裁切：{test_pdf_filename}")
        
        # 模擬 Streamlit 上傳的檔案行為，使用二進位讀取模式開啟
        with open(test_pdf_filename, "rb") as f:
            images = convert_pdf_to_images(f)
            
            if images:
                main_img = images[0]
                
                # 儲存一張完整的全圖，方便您對照座標
                main_img.save(os.path.join(output_folder, "0_full_image.png"))
                
                # 執行裁切
                cropped_imgs = crop_focus_regions(main_img)
                
                # 儲存裁切後的圖片
                cropped_imgs[0].save(os.path.join(output_folder, "1_personal.png"))
                cropped_imgs[1].save(os.path.join(output_folder, "2_sub.png"))
                cropped_imgs[2].save(os.path.join(output_folder, "3_flower.png"))
                cropped_imgs[3].save(os.path.join(output_folder, "4_scatter.png"))
                cropped_imgs[4].save(os.path.join(output_folder, "5_lf_hf.png"))
                cropped_imgs[5].save(os.path.join(output_folder, "6_hr.png"))
                cropped_imgs[6].save(os.path.join(output_folder, "7_sdnn.png"))
                cropped_imgs[7].save(os.path.join(output_folder, "8_yinyang.png"))
                cropped_imgs[8].save(os.path.join(output_folder, "9_tianren.png"))
                
                print(f"✅ 裁切測試完成！請打開 [{output_folder}] 資料夾檢查圖片。")