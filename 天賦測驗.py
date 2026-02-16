import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.font_manager as fm
from fpdf import FPDF
import base64
import os
import io
import csv
import platform
import glob
from datetime import datetime

# --- 跨平台中文字型偵測 ---
def get_chinese_font():
    """回傳 (matplotlib字型名, fpdf字型路徑)"""
    if platform.system() == 'Windows':
        return 'Microsoft JhengHei', 'C:\\Windows\\Fonts\\msjh.ttc'
    else:
        # Linux (Streamlit Cloud) - 使用 Noto Sans CJK
        noto_paths = glob.glob('/usr/share/fonts/**/NotoSansCJK*.ttc', recursive=True)
        if noto_paths:
            font_path = noto_paths[0]
            fm.fontManager.addfont(font_path)
            # 找到字型名稱
            for f in fm.fontManager.ttflist:
                if 'Noto Sans CJK' in f.name and 'TC' in f.name:
                    return f.name, font_path
            return 'Noto Sans CJK TC', font_path
        return 'sans-serif', None

CN_FONT_NAME, CN_FONT_PATH = get_chinese_font()

# --- 數據紀錄功能 ---
def log_results_to_csv(name, responses, scores, final_profile):
    file_path = "results_log.csv"
    file_exists = os.path.isfile(file_path)
    
    # 準備題目的標頭 (Q1, Q2, ..., Q25)
    q_headers = [f"Q{i+1}" for i in range(25)]
    header = ["Timestamp", "Name"] + q_headers + ["Dynamo%", "Blaze%", "Tempo%", "Steel%", "FinalProfile"]
    
    # 計算百分比
    total = sum(scores.values()) if sum(scores.values()) > 0 else 1
    d_pct = round((scores["D"] / total) * 100)
    b_pct = round((scores["B"] / total) * 100)
    t_pct = round((scores["T"] / total) * 100)
    s_pct = round((scores["S"] / total) * 100)
    
    # 準備紀錄行
    # responses 是一個字典 {step_index: 'D/B/T/S'}
    ans_row = [responses.get(i, "") for i in range(25)]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, name] + ans_row + [d_pct, b_pct, t_pct, s_pct, final_profile]
    
    with open(file_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)

# --- PDF 生成函式 ---
def create_pdf(name, profile_name, profile_data, scores):
    pdf = FPDF()
    pdf.add_page()
    
    # 註冊中文字型 (自動偵測平台)
    font_to_use = "Arial"
    if CN_FONT_PATH and os.path.exists(CN_FONT_PATH):
        try:
            pdf.add_font('chinese', '', CN_FONT_PATH, uni=True)
            font_to_use = 'chinese'
            pdf.set_font('chinese', size=12)
        except:
            pdf.set_font('Arial', size=12)
    else:
        pdf.set_font('Arial', size=12)

    # 標題
    pdf.set_font(font_to_use, size=24)
    pdf.cell(200, 20, txt=f"天賦原動力測驗報告：{name}", ln=True, align='C')
    
    # 測驗結果
    pdf.set_font(font_to_use, size=16)
    pdf.cell(200, 15, txt=f"您的天賦角色：{profile_name}", ln=True, align='C')
    
    # 能量分佈
    pdf.set_font(font_to_use, size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"發電機 (Dynamo): {scores['D']}", ln=True)
    pdf.cell(200, 10, txt=f"火焰 (Blaze): {scores['B']}", ln=True)
    pdf.cell(200, 10, txt=f"節奏 (Tempo): {scores['T']}", ln=True)
    pdf.cell(200, 10, txt=f"鋼鐵 (Steel): {scores['S']}", ln=True)
    
    # 詳細分析
    pdf.ln(10)
    pdf.set_font(font_to_use, size=14)
    pdf.cell(200, 10, txt="天賦詳細分析", ln=True)
    
    pdf.set_font(font_to_use, size=12)
    # 使用 multi_cell 處理長文字換行
    pdf.multi_cell(0, 10, txt=f"核心能量：{profile_data['freq']}")
    pdf.multi_cell(0, 10, txt=f"財富之流：{profile_data['wealth_flow']}")
    pdf.multi_cell(0, 10, txt=f"團隊角色：{profile_data['team_role']}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"優勢：{profile_data['strength']}")
    pdf.multi_cell(0, 10, txt=f"盲點：{profile_data['blindspot']}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"成功方程式：{profile_data['success']}")
    pdf.multi_cell(0, 10, txt=f"失敗方程式：{profile_data['failure']}")
    
    return bytes(pdf.output(dest="S"))

# 1. 設置頁面配置
st.set_page_config(page_title="Talent Dynamics 天賦評測系統", page_icon="📈", layout="centered")

# 2. 自定義樣式
st.markdown("""
<style>
    /* 全域深色背景 */
    .stApp {
        background-color: #0f172a; /* Slate 900 */
        color: #f8fafc; /* Slate 50 */
    }
    
    /* 標題與文字 */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif;
    }
    p, label, div {
        color: #e2e8f0; /* Slate 200 */
        font-size: 1.1rem;
    }
    .stWarning {
        color: #fca5a5 !important;
    }
    
    /* 進度條樣式 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6 0%, #8b5cf6 100%);
    }

    /* 卡片式選項 (Dark Mode) */
    div[role="radiogroup"] > label {
        background-color: #1e293b; /* Slate 800 */
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid #334155; /* Slate 700 */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
        color: #f8fafc;
    }
    div[role="radiogroup"] > label:hover {
        background-color: #334155; /* Slate 700 */
        transform: translateY(-2px);
        border-color: #64748b;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    div[role="radiogroup"] > label p {
        color: #f8fafc; /* Ensure option text is white */
    }

    /* 問題容器 */
    .q-container {
        background-color: #1e293b;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #334155;
        border-bottom: 4px solid #3b82f6; # Blue 500
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 30px;
    }

    /* 結果頁標頭 */
    .result-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); /* Blue 900 -> 800 */
        color: white;
        padding: 24px;
        border-radius: 16px 16px 0 0;
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        letter-spacing: 1px;
        border-bottom: 1px solid #1e3a8a;
    }

    /* 統計數據區塊 */
    .result-stats {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
        background-color: #1e293b;
        padding: 20px;
        border-radius: 0 0 16px 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 30px;
        border: 1px solid #334155;
        border-top: none;
    }
    .stat-item {
        flex: 1 1 20%; /* 每行大約 4-5 個 */
        min-width: 100px;
        text-align: center;
    }
        font-size: 1.4em;
        font-weight: bold;
        color: #cbd5e1;
        width: 25%; 
        border-right: 1px solid #475569;
    }
    .stat-item:last-child { border-right: none; }

    /* 詳細資訊卡片 */
    .card-detail {
        background-color: #1e293b;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #334155;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .card-title {
        font-size: 1.3em;
        font-weight: bold;
        margin-bottom: 12px;
        color: #e2e8f0;
        border-bottom: 2px solid #334155;
        padding-bottom: 8px;
    }
    
    /* 按鈕樣式 (更顯眼) */
    .stButton > button {
        background-color: #3b82f6 !important; /* Blue 500 */
        color: white !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: bold;
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #2563eb !important; /* Blue 600 */
    }

    /* 專業天賦報告卡佈局 */
    .report-card {
        display: flex;
        flex-direction: row;
        gap: 20px;
        background-color: #0f172a;
        padding: 2px;
        border-radius: 20px;
        color: #f8fafc;
        font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif;
    }
    .card-left {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 15px;
    }
    .card-right {
        flex: 2;
        background-color: #1e293b;
        border: 4px solid #fbbf24;
        border-radius: 25px;
        padding: 25px;
        display: flex;
        flex-direction: column;
        gap: 15px;
        line-height: 1.6;
    }
    .profile-icon-box {
        width: 180px;
        height: 180px;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 100px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 2px solid #475569;
    }
    .profile-name-main {
        font-size: 48px;
        font-weight: 900;
        color: #f8fafc;
        margin: 5px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .info-box-yellow {
        background-color: #1e293b;
        border: 2px solid #fbbf24;
        border-radius: 20px;
        padding: 10px 15px;
        width: 100%;
        text-align: left;
        font-size: 18px;
    }
    .info-box-yellow span {
        color: #fbbf24;
        font-weight: bold;
    }
    .best-role-title {
        font-size: 28px;
        font-weight: bold;
        color: #f8fafc;
        margin: 10px 0;
    }
    .dev-area-box {
        background-color: #1e293b;
        border: 2.5px solid #fbbf24;
        border-radius: 15px;
        padding: 10px;
        width: 100%;
        text-align: left;
    }
    .dev-area-label {
        color: #fbbf24;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .dev-area-content {
        font-size: 18px;
    }
    .content-section {
        margin-bottom: 10px;
    }
    .content-label {
        font-size: 22px;
        font-weight: bold;
        color: #f8fafc;
    }
    .content-value {
        font-size: 20px;
        color: #e2e8f0;
    }
    .back-button-footer {
        align-self: flex-end;
        background-color: #3b82f6;
        color: white;
        padding: 5px 15px;
        border-radius: 5px;
        font-size: 16px;
        margin-top: auto;
    }

    /* 手機適應 */
    @media (max-width: 768px) {
        .report-card { flex-direction: column; }
    }
</style>
""", unsafe_allow_html=True)

# 3. 定義模型與完整 26 題庫 (加入 Emoji)
questions = [
    {"id": 1, "q": "朋友覺得你比較像哪一種人？", "opts": {"鬼點子特別多": "D", "很好聊、好相處": "B", "做亊很謹慎小心": "T", "很注重細節流程": "S"}},
    {"id": 2, "q": "你希望給別人的印象是？", "opts": {"很有影響力、有人緣": "B", "很穩重、值得託付": "T", "很特別、跟別人不一樣": "D", "很專業、不出錯": "S"}}, 
    {"id": 3, "q": "哪種狀況讓你覺得最爽？", "opts": {"事情都在掌握之中，沒意外": "S", "想到一個超棒的新點子": "D", "被大家喜歡和稱讚": "B", "感覺到自己抓對了時機點": "T"}},
    {"id": 4, "q": "當一個專案剛開始，你最想搶著做什麼？", "opts": {"畫大餅、定方向": "D", "找人聊、喬事情": "B", "盯進度、顧好大家": "T", "訂SOP、建立規則": "S"}},
    {"id": 5, "q": "在聚會場合中，通常你是？", "opts": {"一直丟出新話題的人": "D", "負責炒熱氣氛的人": "B", "在旁邊冷靜觀察的人": "S", "安靜聽大家說話的人": "T"}},
    {"id": 6, "q": "當計畫趕不上變化，場面一片混亂時，你會...？", "opts": {"先暫停動作，釐清數據跟流程哪裡出錯！": "S", "山不轉路轉，立馬想個新招來應對！": "D", "先找人討論，大家一起想辦法我不孤單！": "B", "先停下來看清局勢，慢慢來比較快！": "T"}},
    {"id": 7, "q": "你的朋友可能會抱怨你什麼？", "opts": {"太害羞、不愛說話": "S", "總是三分鐘熱度": "D", "想太多、猶豫不決": "T", "太急躁、沒耐心聽細節": "B"}},
    {"id": 8, "q": "要做重大決定時，你通常會？", "opts": {"問朋友意見": "B", "看大環境或別人都怎麼做": "T", "列優缺點分析表": "S", "憑直覺衝了": "D"}},
    {"id": 9, "q": "你最怕別人覺得你是？", "opts": {"老古板、不知變通": "D", "魯莽、沒大腦": "T", "難搞、沒人緣": "B", "兩光、一直出包": "S"}},
    {"id": 10, "q": "如果要創業，你對哪種生意有興趣？", "opts": {"買低賣高的貿易生意": "T", "有標準流程的連鎖加盟": "S", "改變世界的新創公司": "D", "可以一直接觸人群的服務業": "B"}},
    {"id": 11, "q": "專案中，你最不想做哪件事？", "opts": {"想策略 (太累了)": "D", "顧團隊 (太煩了)": "T", "寫系統 (太無聊)": "S", "去應酬 (太累人)": "B"}},
    {"id": 12, "q": "團隊裡你是什麼角色？", "opts": {"數據分析師 (看數據說話)": "S", "點子王 (負責想Idea)": "D", "公關發言人 (負責對外講話)": "B", "神隊友 (負責把事情落地)": "T"}},
    {"id": 13, "q": "你最不擅長什麼？", "opts": {"跟陌生人裝熟": "B", "跟人家殺價": "T", "從零開始想新東西": "D", "重複做一樣的事": "S"}},
    {"id": 14, "q": "你覺得你最強的能力是？", "opts": {"把複雜的事情標準化": "S", "把不同的人連結在一起": "B", "很會察言觀色、抓時機": "T", "無中生有的創造力": "D"}},
    {"id": 15, "q": "團隊發生什麼事會讓你最崩潰？", "opts": {"大家吵架、氣氛很僵": "B", "做事沒規矩、亂七八糟": "S", "一成不變、毫無進展": "D", "沒有明確的指令或目標": "T"}},
    {"id": 16, "q": "你最討厭遇到什麼？", "opts": {"突然跑來的不速之客": "S", "每天做一樣的例行公事": "D", "不知變通的老頑固": "B", "混亂、不知道下一步怎麼辦": "T"}},
    {"id": 17, "q": "你覺得自己天生自帶的「外掛」是什麼？", "opts": {"超強邏輯與整理術，再亂都能理出頭緒": "S", "源源不絕的創意，大腦停不下來": "D", "超強感染力，能瞬間跟陌生人變熟": "B", "超準的直覺，總能感覺到苗頭對不對": "T"}},
    {"id": 18, "q": "你覺得自己做什麼最弱？", "opts": {"建立一套系統": "S", "看清市場趨勢": "T", "想新點子": "D", "跟人打交道": "B"}},
    {"id": 19, "q": "什麼事情讓你最有成就感？", "opts": {"當我把複雜流程整理得井井有條時": "S", "當我想出別人想不到的新點子時": "D", "當我搞定這世界上最難搞的人時": "B", "當我精準預測到下一步會發生什麼時": "T"}},
    {"id": 20, "q": "你最受不了哪種人？", "opts": {"做事隨便、沒邏輯的人": "S", "腦袋僵化、講不聽的人": "D", "冷漠、不理人的人": "B", "一直催我、給壓力的人": "T"}},
    {"id": 21, "q": "在團隊或朋友圈中，大家公認你是...？", "opts": {"行走的百科全書，找資料問你就對了": "S", "天馬行空的夢想家，總有新奇想法": "D", "團隊的開心果，有你在就不冷場": "B", "最穩定的靠山，交給你就是安心": "T"}},
    {"id": 22, "q": "朋友絕對「不會」用哪個詞來形容你？", "opts": {"很嚴謹、做事一板一眼": "B", "很嗨、人來瘋": "S", "很穩重、按部就班": "D", "很有創意、鬼點子很多": "T"}},
    {"id": 23, "q": "你最擅長？", "opts": {"跟人相處": "B", "找機會": "T", "建系統": "S", "搞創新": "D"}},
    {"id": 24, "q": "當一切都不順利時，你通常會告訴自己？", "opts": {"冷靜下來，找出哪裡出錯修正就好！": "S", "換個方法試試看，一定有别的路！": "D", "沒關係，找大家一起幫忙就能過關！": "B", "只要撐下去，情況一定會好轉的！": "T"}},
    {"id": 25, "q": "專案結束後，你最享受什麼？", "opts": {"開慶功宴": "B", "感謝大家": "T", "整理結案報告": "S", "馬上開始下一個新專案": "D"}}
]
energy_theory = {
    "D": {"name": "發電機 (Dynamo)", "season": "🌱 春天", "question": "是什麼? (What)", "color": "#fbbf24", "desc": "擅長『創意』", "dir": "🧠 發想 (Ideation)", "element": "🌲 木 (Wood)"},
    "B": {"name": "火焰 (Blaze)", "season": "☀️ 夏天", "question": "是誰? (Who)", "color": "#f87171", "desc": "擅長『人際』", "dir": "👥 人 (People)", "element": "🔥 火 (Fire)"},
    "T": {"name": "節奏 (Tempo)", "season": "🍂 秋天", "question": "何時? (When)", "color": "#a78bfa", "desc": "擅長『感知』", "dir": "🤔 思考 (Thinking)", "element": "⛰️ 土 (Earth)"},
    "S": {"name": "鋼鐵 (Steel)", "season": "❄️ 冬天", "question": "怎麼作? (How)", "color": "#60a5fa", "desc": "擅長『細節』", "dir": "📁 事 (Things)", "element": "⛓️ 金 (Metal)"}
}

profile_details = {
    "創作者 (Creator)": {
        "freq": "發電機", "color": "#fbbf24",
        "thinking": "直覺", "action": "外傾",
        "best_role": "最佳產品開發者",
        "dev_area": "創意開發、產品設計、專案發想、目標設定",
        "wealth_flow": "創造更好的產品",
        "team_role": "發想創意、發想新的問題解決方式、大局思考、策略發想。",
        "desc": "你喜歡開創事物，但不太擅長把事情做完。你的成功就在於『創造』本身。",
        "strength": "樂觀、激勵、有遠見、有創造力、能鼓舞別人、可同時處理多個任務、很快創造出績效、擅長開創新事物。",
        "blindspot": "對時機的敏感度較差、缺乏耐心、過度樂觀、容易分心、不擅長把事情完成。",
        "success": "能自由創作、以及有團隊協助關照細節的就能有極為優異的表現。",
        "failure": "試圖掌控太多事情、以為靠自己就可以做所有的事，跑太快，常把團隊成員搞得筋疲力竭。",
        "famous": "史蒂夫·賈伯斯、理雅·布蘭森、比爾·蓋茲、貝多芬、愛迪生。",
        "opposite": "節奏型天才",
        "triangle": "創作者、支持者、積蓄者"
    },
    "明星 (Star)": {
        "freq": "發電機/火焰", "color": "#FF9800",
        "thinking": "直覺", "action": "外傾",
        "best_role": "最佳品牌推廣者",
        "dev_area": "品牌行銷、社交演說、產品演示、公關與形象",
        "wealth_flow": "創造獨特的品牌",
        "team_role": "可發揮創意的專案、大方向的思考規劃、專案的推廣，透過對話與討論來學習、透過辯論與表演進行溝通。",
        "desc": "最擅長建立個人品牌。透過亮眼的表現來獲得認同並引領方向。",
        "strength": "活躍、精力十足、在意形象、思考敏捷、引人注目、反應快。",
        "blindspot": "容易傲慢引發爭議、自我意識強、不輕易聽信別人、花錢很快。",
        "success": "自由發揮並發展自己的個性與品牌，且有一個團隊來協助會有最傑出的表現。",
        "failure": "勉強自己做太多事情，過度自信，過度接觸人，忽略價值在自己而非產品且沒有尋求合作。",
        "famous": "歐普拉、安東尼·羅賓、瑪麗蓮·夢露、麥可傑克遜。",
        "opposite": "積蓄者",
        "triangle": "明星、媒合者、地主"
    },
    "支持者 (Supporter)": {
        "freq": "火焰", "color": "#f87171",
        "thinking": "直覺", "action": "外傾",
        "best_role": "最佳團隊領導者",
        "dev_area": "團隊建立、激勵管理、客戶關係、溝通協調",
        "wealth_flow": "領導團隊",
        "team_role": "把團隊組織起來、跟人互動、激勵、溝通。",
        "desc": "你喜歡跟人相處，但也非常容易分心。你的成功在於領導並解決『誰』的問題。",
        "strength": "重視關係、很能為人建立信心、善於領導於跟隨、高忠誠。",
        "blindspot": "對數字或細節沒有耐心，且通常一獨處就坐立不安。他們容易分心、喜歡閒聊。",
        "success": "找到一個能認同的構想去發揮，建立團隊忠誠度，將創意及計算問題交由他人，只負責領導團隊就會勝出。",
        "failure": "需要找到可以發光發熱的空間，如果沒有將會一直停滯不前。",
        "famous": "史蒂夫·包默、比爾·柯林頓、傑克·威爾許、艾倫·狄珍妮。",
        "opposite": "鋼鐵型天才",
        "triangle": "支持者、商人、技師"
    },
    "媒合者 (Deal Maker)": {
        "freq": "火焰/節奏", "color": "#E91E63",
        "thinking": "感官", "action": "外傾",
        "best_role": "最佳資源整合者",
        "dev_area": "業務開發、資源媒合、談判協商、通路經營",
        "wealth_flow": "把人搓合在一起",
        "team_role": "對外尋找資源、一對一談話、溝通，照顧每一個人。",
        "desc": "最擅長在對的時間點將對的人湊在一起，從中創造價值。",
        "strength": "外向、有趣、好相處、善交際、交談間容易創造機會。",
        "blindspot": "自己定位容易模糊，常試圖讓每個人開心，容易錯失機會。",
        "success": "自由的去建立人脈，找到一個自己可以主宰的利基點，透過這樣的方式自動把交易吸引過來。",
        "failure": "太忙著建立人脈，等建立了關係才發現自己還在局外；因經常幫忙別人，而忽略了自己的團隊與自己的利潤。",
        "famous": "唐納·川普、魯柏·梅鐸。",
        "opposite": "技師",
        "triangle": "媒合者、積蓄者、創作者"
    },
    "商人 (Trader)": {
        "freq": "節奏", "color": "#a78bfa",
        "thinking": "感官", "action": "內傾/外傾",
        "best_role": "最佳時機掌控者",
        "dev_area": "市場交易、低買高賣、行情觀察、現狀分析",
        "wealth_flow": "買低賣高",
        "team_role": "把團隊成員凝聚在一起、維持公平、監管活動狀況與進度、注意時間進度、維持團隊腳踏實地，並讓顧客開心。",
        "desc": "你腳踏實地，但常迷失於活動中。擅長回答與『何時(When)』相關的問題。",
        "strength": "靠感覺、有洞察力、務實、常能觀察他人漏失的事項。",
        "blindspot": "過度務實，太過重視當下而犧牲未來。",
        "success": "從別人身上取得線索，並在腦力激盪後積極投入的行動中最能發揮潛力，而且要實際去做，能靈機應變。",
        "failure": "能同時從事多項任務，但如果因此能力而去處理創作、行政管理或簡報之類，那就會因工作過量而下沉。",
        "famous": "喬治·索羅斯、甘地、曼德拉、德蕾莎修女、華倫·巴菲特。",
        "opposite": "發電機型天才",
        "triangle": "商人、地主、明星"
    },
    "積蓄者 (Accumulator)": {
        "freq": "節奏/鋼鐵", "color": "#673AB7",
        "thinking": "感官", "action": "內傾",
        "best_role": "最佳專案管理者",
        "dev_area": "專案管理、研究、市調、計算、組織事務",
        "wealth_flow": "累積會增值的資產",
        "team_role": "確保按時完成、確保團隊獲得最新的資訊、把事做更好的透過觀察與度量來學習、透過資料與報表來進行溝通。",
        "desc": "最擅長收集並守住財富。透過可靠的長期持有與風險管理獲勝。",
        "strength": "可靠、謹慎、深思熟慮、擅長將計畫變成流程。",
        "blindspot": "經常拖延、因細節分心、需要很多資料才願意行動；常太慢建立動能，容易收集雜物，遇到混亂就想逃避。",
        "success": "如果能按照自己的步驟進行，就像龜兔賽跑贏得比賽的烏龜，避開舞台，樂於讓別人展現，幕後控制好步調就好。",
        "failure": "從未建立可起步的資產，或是找了門檻較低的方式進入市場，而沒有發揮強項找尋會增值的資產。",
        "famous": "華倫·巴菲特 (成熟期)。",
        "opposite": "明星",
        "triangle": "積蓄者、技師、支持者"
    },
    "地主 (Lord)": {
        "freq": "鋼鐵", "color": "#60a5fa",
        "thinking": "感官", "action": "內傾",
        "best_role": "最佳現金流管理者",
        "dev_area": "資料分析、成本控制、系統管理、資產監控",
        "wealth_flow": "掌控現金流資產",
        "team_role": "調度、資料管理、透過計算、資料、報表進行溝通。",
        "desc": "你擅長處理細節，但常過度小心。擅長回答關於『怎麼作(How)』的問題。",
        "strength": "善於控制、重視細節、善於分析，能找出別人遺漏的差異、能列舉每個細節。",
        "blindspot": "重視任務更甚於關係、對社會繁文縟節沒耐心，經常陷入過度組織化，常未見大局或錯過重要事件。",
        "success": "專注後端細節、不處理前端事務、掌控流程就能改善盈虧。",
        "failure": "處於創作或激勵他人的環境時，專斷的風格容易讓人難受，或沒有可以取得有效營運所需的資料，容易覺得受挫。",
        "famous": "拉克希米·米塔爾、約翰·洛克斐勒、雷·克洛克、亨利·福特。",
        "opposite": "火焰型天才",
        "triangle": "地主、創作者、媒合者"
    },
    "技師 (Mechanic)": {
        "freq": "鋼鐵/發電機", "color": "#03A9F4",
        "thinking": "直覺", "action": "內傾",
        "best_role": "最佳系統開發者",
        "dev_area": "系統優化、流程簡化、架構設計、自動化工程",
        "wealth_flow": "創造更好的系統",
        "team_role": "有創意方式的解決問題、改善提昇事物、規劃團隊的各個角色、以流程圖或心智圖來溝通。",
        "desc": "最擅長精煉既有的產品 or 流程。讓事物變得更精簡、更自動、更好用。",
        "strength": "創新、完美主義、易找出沒效率的地方、善簡化、複製。",
        "blindspot": "離群索居、過於有條理缺乏彈性、重視完美而不太願意改變。",
        "success": "處理業務流程中找出改良方法；可自由拆解事物，就能有非常好的表現。",
        "failure": "不擅制定計畫和策略，沒有相關成熟要素，與正確產品和團隊的運作環境，容易因眼前不完美而分心。",
        "famous": "馬克·祖克柏、華特·迪士尼、亨利·福特 (後期)。",
        "opposite": "媒合者",
        "triangle": "技師、明星、商人"
    }
}

# 4. 初始化 Session State (使用 responses 記錄每題答案)
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'uname' not in st.session_state:
    st.session_state.uname = ""

# 5. 邏輯處理
def calculate_scores():
    scores = {"D": 0, "B": 0, "T": 0, "S": 0}
    for q_idx, energy in st.session_state.responses.items():
        if energy in scores:
            scores[energy] += 1
    return scores

# 6. 介面渲染
if st.session_state.uname == "":
    st.title("🏹 Talent Dynamics 天賦原動力")
    st.info("了解你的自然能量，找到阻力最小的路徑。")
    # 停用瀏覽器自動完成
    st.markdown('<style>input[type="text"]{autocomplete:off !important;}</style>', unsafe_allow_html=True)
    name = st.text_input("請先輸入受測者姓名：", autocomplete="off")
    if st.button("開始評測 🚀") and name:
        st.session_state.uname = name
        st.rerun()

elif st.session_state.step < len(questions):
    # --- 視覺優化：階段提示 ---
    q_step = st.session_state.step + 1
    total_q = len(questions)
    
    if q_step <= 5:
        st.markdown("### 🧩 Part 1: 關於你的特質")
    elif q_step <= 9:
        st.markdown("### ⚡ Part 2: 你的優勢與地雷")
    elif q_step <= 15:
        st.markdown("### 💼 Part 3: 工作與專案偏好")
    else:
        st.markdown("### 🏔️ Part 4: 生活與價值觀")
        
    # 進度條優化
    st.progress(st.session_state.step / total_q, text=f"進度：{q_step}/{total_q}")

    q_data = questions[st.session_state.step]
    
    # --- 視覺優化：題目卡片 ---
    st.markdown(f"""
    <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4ade80; margin-bottom: 20px;">
        <h3 style="margin:0; color: #4ade80;">Q{q_data['id']}. {q_data['q']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 選項處理
    opts_map = {k: v for k, v in q_data["opts"].items()} # Label -> Value
    opts_labels = list(opts_map.keys())
    
    # 檢查是否有已存的答案
    default_idx = None
    if st.session_state.step in st.session_state.responses:
        saved_val = st.session_state.responses[st.session_state.step]
        # 反查 Label
        for i, label in enumerate(opts_labels):
            if opts_map[label] == saved_val:
                default_idx = i
                break
    
    choice = st.radio("選取最符合你的直覺描述：", opts_labels, index=default_idx, key=f"q_{st.session_state.step}")

    # 導航按鈕
    col_prev, col_next = st.columns([1, 1])
    
    with col_prev:
        if st.session_state.step > 0:
            if st.button("⬅️ 上一題"):
                if choice:
                    st.session_state.responses[st.session_state.step] = opts_map[choice]
                st.session_state.step -= 1
                st.rerun()
            
    with col_next:
        if st.button("下一題 ➡️"):
            if choice:
                st.session_state.responses[st.session_state.step] = opts_map[choice]
                st.session_state.step += 1
                st.rerun()
            else:
                st.warning("請選擇一個選項！")

# 7. 結果頁面
else:
    st.balloons()
    scores = calculate_scores()
    
    # 計算百分比
    total = sum(scores.values()) if sum(scores.values()) > 0 else 1
    d_pct = round((scores["D"] / total) * 100)
    b_pct = round((scores["B"] / total) * 100)
    t_pct = round((scores["T"] / total) * 100)
    s_pct = round((scores["S"] / total) * 100)
    
    # 先判定角色 (提前到 header 前，這樣上方能顯示)
    sorted_freqs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1 = sorted_freqs[0][0]
    top2 = sorted_freqs[1][0]
    
    if top1 == "D":
        final_profile = "創作者 (Creator)" if top2 not in ["B", "S"] else ("明星 (Star)" if top2 == "B" else "技師 (Mechanic)")
    elif top1 == "B":
        final_profile = "支持者 (Supporter)" if top2 not in ["D", "T"] else ("明星 (Star)" if top2 == "D" else "媒合者 (Deal Maker)")
    elif top1 == "T":
        final_profile = "商人 (Trader)" if top2 not in ["B", "S"] else ("媒合者 (Deal Maker)" if top2 == "B" else "積蓄者 (Accumulator)")
    else: # Steel
        final_profile = "地主 (Lord)" if top2 not in ["D", "T"] else ("技師 (Mechanic)" if top2 == "D" else "積蓄者 (Accumulator)")
    
    p_data = profile_details[final_profile]
    profile_short = final_profile.split(' ')[0]  # e.g. "技師"

    # 頂部：姓名 + 主要類別 + 四大能量
    st.markdown(f"""
    <div style="display:flex; flex-direction:column; gap:8px; margin-bottom:15px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.2em; color:#94a3b8; font-weight:bold;">姓名：</span>
            <span style="background:#334155; padding:6px 20px; border-radius:4px; font-size:1.2em; color:#60a5fa;">{st.session_state.uname}</span>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.2em; color:#94a3b8; font-weight:bold;">主要類別：</span>
            <span style="background:#334155; padding:6px 20px; border-radius:4px; font-size:1.2em; color:#60a5fa;">{profile_short}</span>
        </div>
    </div>
    <div class="result-header">我的天賦原動力圖表</div>
    <div class="result-stats">
        <div class="stat-item"><span style="color:#fbbf24">發電機：</span> {d_pct}%</div>
        <div class="stat-item"><span style="color:#f87171">火焰：</span> {b_pct}%</div>
        <div class="stat-item"><span style="color:#a78bfa">節奏：</span> {t_pct}%</div>
        <div class="stat-item"><span style="color:#60a5fa">鋼鐵：</span> {s_pct}%</div>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    # 雷達圖數據準備 (八角色 + 四能量)
    labels = ["創作者", "明星", "支持者", "媒合者", "商人", "積蓄者", "地主", "技師"]
    r_vals = [
        d_pct,              # 創作者 (Dynamo)
        (d_pct + b_pct)/2,  # 明星 (Dynamo/Blaze)
        b_pct,              # 支持者 (Blaze)
        (b_pct + t_pct)/2,  # 媒合者 (Blaze/Tempo)
        t_pct,              # 商人 (Tempo)
        (t_pct + s_pct)/2,  # 積蓄者 (Tempo/Steel)
        s_pct,              # 地主 (Steel)
        (s_pct + d_pct)/2   # 技師 (Steel/Dynamo)
    ]
    r_vals.append(r_vals[0])
    labels.append(labels[0])
    
    fig = go.Figure()
    max_val = max(r_vals) * 1.2 if max(r_vals) > 0 else 10

    # 1. 繪製放射狀虛線 (Axes)
    for i in range(8):
        fig.add_trace(go.Scatterpolar(
            r=[0, max_val],
            theta=[labels[i], labels[i]],
            mode='lines',
            line=dict(color='#94a3b8', width=1, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))

    # 2. 繪製八角形網格
    for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r_grid = [max_val * level] * 9
        fig.add_trace(go.Scatterpolar(
            r=r_grid,
            theta=labels,
            mode='lines',
            line=dict(color='#94a3b8', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))

    # 3. 繪製主要數據
    fig.add_trace(go.Scatterpolar(
        r=r_vals,
        theta=labels,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.15)',
        line=dict(color='#2563eb', width=3),
        marker=dict(size=8, color='#fbbf24')
    ))

    # 4. 八角色外圍黃色圓點 (裝飾)
    dot_r = [max_val * 1.02] * 8
    fig.add_trace(go.Scatterpolar(
        r=dot_r,
        theta=labels[:-1],
        mode='markers',
        marker=dict(size=10, color='#fbbf24'),
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, max_val * 1.1]),
            angularaxis=dict(
                visible=True,
                showline=False,
                showgrid=False,
                tickfont=dict(size=13, color='#e2e8f0'),
                direction="clockwise",
                rotation=90,
            ),
            bgcolor='rgba(255,255,255,0)'
        ),
        annotations=[
            # 四大能量標籤 (創作者在上，順時針)
            dict(x=0.5, y=0.73, text="<b>發電機</b>", showarrow=False, font=dict(size=14, color="#fbbf24")),
            dict(x=0.73, y=0.5, text="<b>火焰</b>", showarrow=False, font=dict(size=14, color="#f87171")),
            dict(x=0.5, y=0.27, text="<b>節奏</b>", showarrow=False, font=dict(size=14, color="#a78bfa")),
            dict(x=0.27, y=0.5, text="<b>鋼鐵</b>", showarrow=False, font=dict(size=14, color="#60a5fa")),
            # 內傾/外傾標籤
            dict(x=0.35, y=0.32, text="內傾", showarrow=False, font=dict(size=12, color="#94a3b8")),
            dict(x=0.65, y=0.32, text="外傾", showarrow=False, font=dict(size=12, color="#94a3b8")),
        ],
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

    # --- 截圖下載按鈕 ---
    def generate_result_image():
        """生成包含所有資訊的結果圖片"""
        fig_img, axes = plt.subplots(2, 1, figsize=(10, 14), 
                                      gridspec_kw={'height_ratios': [1.8, 8]},
                                      facecolor='#0f172a')
        
        # 上半部：資訊區
        ax_info = axes[0]
        ax_info.set_facecolor('#0f172a')
        ax_info.axis('off')
        ax_info.set_xlim(0, 10)
        ax_info.set_ylim(0, 3)
        
        # 姓名
        ax_info.text(0.3, 2.5, '姓名：', fontsize=16, color='#94a3b8',
                     fontfamily=CN_FONT_NAME, fontweight='bold', va='center')
        ax_info.add_patch(plt.Rectangle((1.8, 2.25), 3, 0.55, facecolor='#334155', 
                                         edgecolor='none', transform=ax_info.transData))
        ax_info.text(2.0, 2.5, st.session_state.uname, fontsize=16, color='#60a5fa',
                     fontfamily=CN_FONT_NAME, va='center')
        
        # 主要類別
        ax_info.text(0.3, 1.8, '主要類別：', fontsize=16, color='#94a3b8',
                     fontfamily=CN_FONT_NAME, fontweight='bold', va='center')
        ax_info.add_patch(plt.Rectangle((2.5, 1.55), 2.5, 0.55, facecolor='#334155',
                                         edgecolor='none', transform=ax_info.transData))
        ax_info.text(2.7, 1.8, profile_short, fontsize=16, color='#60a5fa',
                     fontfamily=CN_FONT_NAME, va='center')
        
        # 標題列
        ax_info.add_patch(plt.Rectangle((0, 0.8), 10, 0.6, facecolor='#1e3a8a',
                                         edgecolor='none', transform=ax_info.transData))
        ax_info.text(5, 1.1, '我的天賦原動力圖表', fontsize=20, color='white',
                     fontfamily=CN_FONT_NAME, fontweight='bold',
                     ha='center', va='center')
        
        # 能量百分比列
        ax_info.add_patch(plt.Rectangle((0, 0.2), 10, 0.55, facecolor='#1e293b',
                                         edgecolor='none', transform=ax_info.transData))
        energy_labels = [
            (1.2, f'發電機：{d_pct}%', '#fbbf24'),
            (3.7, f'火焰：{b_pct}%', '#f87171'),
            (6.2, f'節奏：{t_pct}%', '#a78bfa'),
            (8.7, f'鋼鐵：{s_pct}%', '#60a5fa'),
        ]
        for ex, etxt, ecol in energy_labels:
            ax_info.text(ex, 0.47, etxt, fontsize=13, color=ecol,
                         fontfamily=CN_FONT_NAME, fontweight='bold', va='center')
        
        # 下半部：雷達圖
        ax_radar = axes[1]
        ax_radar.set_facecolor('#0f172a')
        
        # 用極座標重繪雷達圖 (八角色)
        ax_radar.axis('off')
        radar_ax = fig_img.add_axes([0.1, 0.05, 0.8, 0.6], polar=True, facecolor='#0f172a')
        radar_ax.set_theta_zero_location('N')   # 0度在上方
        radar_ax.set_theta_direction(-1)         # 順時針
        
        angles = np.linspace(0, 2 * np.pi, 8, endpoint=False).tolist()
        r_data = [
            d_pct, (d_pct + b_pct)/2, b_pct, (b_pct + t_pct)/2,
            t_pct, (t_pct + s_pct)/2, s_pct, (s_pct + d_pct)/2
        ]
        angles += angles[:1]
        r_data += r_data[:1]
        
        radar_labels = ['創作者', '明星', '支持者', '媒合者', '商人', '積蓄者', '地主', '技師']
        
        max_v = max(r_data) * 1.2 if max(r_data) > 0 else 10
        
        # 網格
        for lvl in [0.2, 0.4, 0.6, 0.8, 1.0]:
            grid_r = [max_v * lvl] * 9
            grid_a = angles
            radar_ax.plot(grid_a, grid_r, '-', color='#94a3b8', linewidth=0.8)
        
        # 放射線
        for a in angles[:-1]:
            radar_ax.plot([a, a], [0, max_v], '--', color='#94a3b8', linewidth=0.8)
        
        # 數據
        radar_ax.fill(angles, r_data, color='#2563eb', alpha=0.15)
        radar_ax.plot(angles, r_data, color='#2563eb', linewidth=2.5)
        radar_ax.scatter(angles[:-1], r_data[:-1], color='#fbbf24', s=60, zorder=5)
        
        # 外圍黃色圓點
        for a in angles[:-1]:
            radar_ax.scatter([a], [max_v * 1.02], color='#fbbf24', s=50, zorder=5)
        
        radar_ax.set_ylim(0, max_v * 1.1)
        radar_ax.set_xticks(angles[:-1])
        radar_ax.set_xticklabels(radar_labels, fontsize=12, color='#e2e8f0',
                                 fontfamily=CN_FONT_NAME, fontweight='bold')
        radar_ax.set_yticklabels([])
        radar_ax.spines['polar'].set_visible(False)
        radar_ax.grid(False)
        
        # 四大能量標籤 (順時針: 上=發電機, 右=火焰, 下=節奏, 左=鋼鐵)
        radar_ax.text(0, max_v * 0.55, '發電機', fontsize=11, color='#fbbf24',
                      ha='center', va='center', fontfamily=CN_FONT_NAME, fontweight='bold')
        radar_ax.text(np.pi/2, max_v * 0.55, '火焰', fontsize=11, color='#f87171',
                      ha='center', va='center', fontfamily=CN_FONT_NAME, fontweight='bold')
        radar_ax.text(np.pi, max_v * 0.55, '節奏', fontsize=11, color='#a78bfa',
                      ha='center', va='center', fontfamily=CN_FONT_NAME, fontweight='bold')
        radar_ax.text(3*np.pi/2, max_v * 0.55, '鋼鐵', fontsize=11, color='#60a5fa',
                      ha='center', va='center', fontfamily=CN_FONT_NAME, fontweight='bold')
        # 內傾/外傾
        radar_ax.text(np.pi * 1.25, max_v * 0.35, '內傾', fontsize=10, color='#94a3b8',
                      ha='center', va='center', fontfamily=CN_FONT_NAME)
        radar_ax.text(np.pi * 0.75, max_v * 0.35, '外傾', fontsize=10, color='#94a3b8',
                      ha='center', va='center', fontfamily=CN_FONT_NAME)
        
        plt.subplots_adjust(hspace=0.05)
        
        buf = io.BytesIO()
        fig_img.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                        facecolor='#0f172a', edgecolor='none')
        buf.seek(0)
        plt.close(fig_img)
        return buf.getvalue()
    
    img_bytes = generate_result_image()
    st.download_button(
        label="📸 截圖下載",
        data=img_bytes,
        file_name=f"天賦原動力_{st.session_state.uname}.png",
        mime="image/png",
        type="primary"
    )


    # --- 7.5 自動紀錄數據 (僅記錄一次) ---
    if "logged" not in st.session_state:
        log_results_to_csv(st.session_state.uname, st.session_state.responses, scores, final_profile)
        st.session_state.logged = True

    # --- 8. 視覺優化：專業天賦報告卡 (Professional Profile Card) ---
    st.markdown("---")
    
    # 找對應的 Icon
    if "發電機" in p_data["freq"] and "火焰" not in p_data["freq"] and "鋼鐵" not in p_data["freq"]: icon = "💡" # Creator
    elif "發電機" in p_data["freq"] and "火焰" in p_data["freq"]: icon = "🌟" # Star
    elif "火焰" in p_data["freq"] and "節奏" not in p_data["freq"]: icon = "🤝" # Supporter
    elif "火焰" in p_data["freq"] and "節奏" in p_data["freq"]: icon = "🔗" # Deal Maker
    elif "節奏" in p_data["freq"] and "鋼鐵" not in p_data["freq"]: icon = "📉" # Trader
    elif "節奏" in p_data["freq"] and "鋼鐵" in p_data["freq"]: icon = "📦" # Accumulator
    elif "鋼鐵" in p_data["freq"] and "發電機" not in p_data["freq"]: icon = "🏰" # Lord
    else: icon = "⚙️" # Mechanic

    card_html = f"""
<div class="report-card">
<div class="card-left">
<div class="profile-icon-box">{icon}</div>
<div class="profile-name-main">{final_profile.split(' ')[0]}</div>
<div class="info-box-yellow">
<div><span>能量頻率：</span>{p_data['freq']}</div>
<div><span>思維傾向：</span>{p_data['thinking']}</div>
<div><span>行為傾向：</span>{p_data['action']}</div>
</div>
<div class="best-role-title">{p_data['best_role']}</div>
<div class="dev-area-box">
<div class="dev-area-label">適合發展：</div>
<div class="dev-area-content">{p_data['dev_area']}</div>
</div>
</div>
<div class="card-right">
<div class="content-section">
<span class="content-label">團隊角色：</span>
<span class="content-value">{p_data['team_role']}</span>
</div>
<div class="content-section">
<span class="content-label">優點：</span>
<span class="content-value">{p_data['strength']}</span>
</div>
<div class="content-section">
<span class="content-label">缺點：</span>
<span class="content-value">{p_data['blindspot']}</span>
</div>
<div class="content-section">
<span class="content-label">成功之道：</span>
<span class="content-value">{p_data['success']}</span>
</div>
<div class="content-section">
<span class="content-label">失敗導因：</span>
<span class="content-value">{p_data['failure']}</span>
</div>
</div>
</div>
"""
    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 9. 社交分享功能 (Social Share) ---
    st.markdown("### 📤 分享你的天賦結果")
    st.write("點擊右上角複製按鈕，分享給朋友！")
    
    share_text = f"""
🎯 我的天賦原動力測驗結果：
我是「{final_profile.split(' ')[0]}」型天才！{icon}

🌟 我的天賦優勢：
{p_data['wealth_flow']}

🔥 我的最佳拍檔：
{p_data['triangle']}

👉 快來測測看你的天賦是什麼？
(填入你的測驗連結)
    """
    st.markdown(f"""
    <div style="background-color:#1e293b; padding:20px; border-radius:12px; border:1px solid #334155; white-space:pre-wrap; font-size:1rem; color:#e2e8f0; line-height:1.8;">{share_text}</div>
    """, unsafe_allow_html=True)

    # --- 9.5 PDF 報告下載 ---
    # 生成 PDF
    pdf_bytes = create_pdf(st.session_state.uname, final_profile, p_data, scores)
    
    st.download_button(
        label="📄 下載完整分析報告 (PDF)",
        data=pdf_bytes,
        file_name=f"天賦原動力報告_{st.session_state.uname}.pdf",
        mime="application/pdf",
        type="primary"
    )

    # --- 10. 詳細分析 (Detailed Breakdown) ---
    st.markdown("---")
    st.subheader("📖 深度角色解析")
    
    # 使用 Tabs 分頁顯示所有角色
    tabs = st.tabs([p.split(' ')[0] for p in profile_details.keys()])
    
    for i, (p_name, p_tabs) in enumerate(zip(profile_details.keys(), tabs)):
        with p_tabs:
            detail_data = profile_details[p_name]
            st.markdown(f"### {p_name}")
            st.markdown(f"**核心頻率**：{detail_data['freq']}")
            st.markdown(f"**財富之流**：{detail_data['wealth_flow']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"**✅ 優勢**：\n{detail_data['strength']}")
                st.markdown(f"**🚀 成功方程式**：\n{detail_data['success']}")
            with c2:
                st.error(f"**⚠️ 盲點**：\n{detail_data['blindspot']}")
                st.markdown(f"**📉 失敗方程式**：\n{detail_data['failure']}")
                
            st.info(f"**💡 適合角色**：{detail_data['team_role']}")
            st.markdown(f"**👥 代表人物**：{detail_data['famous']}")
            st.caption(f"最佳拍檔：{detail_data['triangle']} | 相反屬性：{detail_data['opposite']}")
    
    st.markdown("---")
    if st.button("重新測試 🔄"):
        st.session_state.responses = {}
        st.session_state.step = 0
        st.session_state.uname = ""
        if "logged" in st.session_state:
            del st.session_state["logged"]
        st.rerun()
