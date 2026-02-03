import streamlit as st
import shioaji as sj
import pandas as pd
import datetime

# ==========================================
# 1. 頁面基礎設定
# ==========================================
st.set_page_config(page_title="V4 財富分配中控台", page_icon="💎", layout="centered")
st.title("💎 V4 財富分配中控台")
st.caption("專注於極端行情的財富重分配機會")

# ==========================================
# 2. 連線設定 (讀取 Secrets)
# ==========================================
@st.cache_resource
def init_shioaji():
    # 使用模擬環境 (simulation=True)
    api = sj.Shioaji(simulation=True)
    try:
        # 從雲端金庫讀取帳密
        api.login(
            api_key=st.secrets["shioaji"]["api_key"], 
            secret_key=st.secrets["shioaji"]["secret_key"]
        )
        return api, "✅ 系統連線成功"
    except Exception as e:
        return None, f"❌ 連線失敗: {str(e)}"

api, status_msg = init_shioaji()

# 顯示連線狀態
if api:
    st.success(status_msg)
else:
    st.error(status_msg)
    st.warning("請檢查 Secrets 設定是否正確")
    st.stop() # 連線失敗則停止執行

st.divider()

# ==========================================
# 3. 策略邏輯核心 (V4 Brain)
# ==========================================
def check_v4_signal(open_price, high_price, low_price, close_price, vol, avg_vol):
    """
    輸入數據，判斷是否符合 V4 財富分配訊號
    """
    signals = []
    
    # 計算關鍵指標
    # 漲跌幅 %
    day_ret_pct = (close_price - open_price) / open_price * 100
    # 量能比 (預估量 / 均量)
    vol_ratio = vol / avg_vol if avg_vol > 0 else 0
    # 上影線長度
    upper_shadow = high_price - close_price
    # 實體長度
    body_len = abs(close_price - open_price)
    
    # --- 策略 A: 🩸 絕地求生 (Panic Climax) ---
    # 條件: 跌幅 > 1.5% 且 爆量 > 1.5倍
    if day_ret_pct < -1.5 and vol_ratio > 1.5:
        signals.append({
            "name": "🩸 絕地求生 (Panic Climax)",
            "desc": f"跌幅 {day_ret_pct:.2f}% | 量能 {vol_ratio:.1f}倍 | 恐慌極致，準備反彈",
            "action": "建議：尾盤進場做多 (留倉)",
            "type": "danger" # 紅色警示
        })

    # --- 策略 B: 🐉 飛龍在天 (Momentum) ---
    # 條件: 漲幅 > 1.5% 且 光頭紅棒 (上影線 < 實體20%)
    # 避免除以0錯誤
    if body_len > 0:
        shadow_ratio = upper_shadow / body_len
    else:
        shadow_ratio = 1.0

    if day_ret_pct > 1.5 and shadow_ratio < 0.2:
        signals.append({
            "name": "🐉 飛龍在天 (Strongest Momentum)",
            "desc": f"漲幅 {day_ret_pct:.2f}% | 收最高 (影線{shadow_ratio:.2f}) | 動能強勁",
            "action": "建議：尾盤追價做多 (留倉)",
            "type": "danger" # 紅色警示
        })
        
    return signals
