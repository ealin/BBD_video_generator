# -*- coding: utf-8 -*-
import os


def extract_sections_from_file(file_path):
    """
    從文字檔中擷取章節（以 >>>> 開頭、@@@@ 結尾），
    保留 >>>> 後的章節標題，並移除特殊符號。
    """
    sections = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = []
    recording = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('>>>>'):
            recording = True
            # ✅ 保留 >>>> 後的文字作為章節標題
            title = stripped[4:].lstrip()
            current_section = [title]
        elif recording:
            if stripped.endswith('@@@@'):
                recording = False
                sections.append('\n'.join(current_section).strip())  # 儲存純章節內容
            else:
                current_section.append(line.rstrip())

    return sections


def write_sections_to_file(sections, output_path):
    """
    將每個章節寫入指定的輸出檔案。
    """
    style_string = "吉卜力動畫"  # "洛可可風"  #"梵谷" #"吉卜力動畫"
    girl_string = ""

    _1st_prompt = "--- 截取標題： ---\n\n你是一個專業的插畫家，擅長吸收一篇講稿的內容，並產出可表達每個章節內容的插圖，包含可呈現整篇講稿內涵的封面與結論的插圖。請先分析附件\"講稿.txx\"，列出所有用\">>>>\"開頭的章節名稱。\n\n"
    main_frame_prompt_string = "針對整個講稿產生一張演講海報封面圖畫，圖畫用來表達以下文字的內涵。圖片比例為16:9，解析度為1792x1024, " + style_string + "畫風，主角為漂亮年輕女性，圖畫中不要出現任何文字。 "
 
    #topic_prompt_string = "請解析講稿中的以下文字這段章節的文字，設計一張能代表此章節含義的圖畫，沿用上圖的女主角，圖片比例為16:9，解析度為1792x1024, " + style_string +"畫風，圖畫中不要出現任何文字。"
    topic_prompt_string = "請解析講稿中的以下文字這段章節的文字，設計能代表此章節含義的圖畫，沿用上圖的女主角，圖片比例為16:9，解析度為1792x1024, " + style_string +"畫風，圖畫中不要出現任何文字。"

    with open(output_path, 'w', encoding='utf-8') as f:

        f.write(_1st_prompt)


        for i, section in enumerate(sections, 1):


            if i == 1:
                f.write(f"--- 封面 ---\n") 
                f.write(main_frame_prompt_string + "\n\n\"\"\"")
            else:
                f.write(f"--- 第 {i-1} 章 ---\n")
                f.write(topic_prompt_string + "\n\n\"\"\"")
            f.write(section + "\n\n")
            f.write( "\"\"\"\n\n")



def extract_sections_from_file2(file_path):
    """
    從文字檔中擷取章節（以 >>>> 開頭、@@@@ 結尾），
    保留 >>>> 後的章節標題，並移除特殊符號。
    """
    sections = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = []
    recording = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('>>>>'):
            recording = True
            # ✅ 保留 >>>> 後的文字作為章節標題
            title = stripped[4:].lstrip()
            current_section = [title]
        elif recording:
            if stripped.endswith('@@@@'):
                recording = False
                sections.append('\n'.join(current_section).strip())  # 儲存純章節內容
            #else:
     
    return sections
       #    current_section.append(line.rstrip())


def write_sections_to_file2(sections, output_path):
    """
    將每個章節寫入指定的輸出檔案。
    """
    style_string =  "寫實法醫畫風"  #"愛德華·孟克畫作\"吶喊\""   #"\"葬送的芙莉蓮\"動畫" #"吉卜力動畫"  # "洛可可風"  #"梵谷" #"吉卜力動畫"
    girl_string = ""

    _1st_prompt = "--- 截取標題： ---\n\n你是一個專業的插畫家，擅長吸收一篇講稿的內容，並產出可表達每個章節內容的插圖，包含可呈現整篇講稿內涵的封面與結論的插圖。請先分析附件\"講稿.txx\"，列出所有用\">>>>\"開頭的章節名稱。\n\n"
    
    main_frame_prompt_string = "產生封面插圖。圖片比例為16:9，解析度為1792x1024, " + style_string + "畫風，主角為漂亮年輕女性，圖畫中不要出現任何文字。 "
    summary_frame_prompt_string = "產生結尾插圖。圖片比例為16:9，解析度為1792x1024,"  + style_string +  "畫風，主角為漂亮年輕女性，圖畫中不要出現任何文字。 "
 
    topic_prompt_string = "請解析講稿中的以下文字這段章節的文字，設計能代表此章節含義的圖畫，沿用上圖的女主角，圖片比例為16:9，解析度為1792x1024, " + style_string +"畫風，圖畫中不要出現任何文字。"

    with open(output_path, 'w', encoding='utf-8') as f:

        f.write(_1st_prompt)


        for i, section in enumerate(sections, 1):


            if i == 1:
                f.write(f"--- 封面 ---\n") 
                f.write(main_frame_prompt_string + "\n\n\"\"\"")
            else:
                f.write(f"--- 第 {i-1} 章 ---\n")
                f.write("產生章節" + f"{i-1} (" + section + ")插圖，以一個具象化的主題元素繪製。圖片比例為16:9，解析度為1792x1024," + style_string +"畫風，最好可以不突兀地加入一個漂亮年輕女主角，圖畫中不要出現任何文字。\n\n\"\"\"")

            #f.write( "\"\"\"\n\n")



# ✅ 測試主程式（你可以修改檔名）
if __name__ == "__main__":
    file_path = "./bg_image/講稿.txt"  # 替換為你的實際檔案路徑
    output_path = "./bg_image/prompt.txt"

    if os.path.exists(file_path):
        sections = extract_sections_from_file2(file_path)
        print(f"共擷取到 {len(sections)} 個章節。\n")
        '''
        for i, section in enumerate(sections, 1):
            print(f"--- 第 {i} 章 ---")
            print(section)
            print()
        '''
        write_sections_to_file2(sections, output_path)
        print('done!\n')

    else:
        print(f"檔案不存在：{file_path}")






