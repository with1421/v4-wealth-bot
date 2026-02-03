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

# ==========================================
# 4. 數據監控儀表板
# ==========================================
st.subheader("🔍 今日盤勢監控 (TXF)")

# --- 模式選擇：實戰 vs 測試 ---
# 預設開啟測試模式，因為現在可能是盤後，抓不到報價
use_test_data = st.checkbox("開啟測試模式 (強制生成訊號)", value=True)

current_open = 0
current_close = 0
current_high = 0
current_low = 0
current_vol = 0
avg_vol_20 = 100000 # 預設均量

if use_test_data:
    # --- [測試模式] 模擬一個符合「絕地求生」的數據 ---
    st.info("⚠️ 目前為【測試模式】，數據為虛擬生成的。")
    current_open = 22000.0
    current_close = 21600.0 # 大跌 400點
    current_high = 22050.0
    current_low = 21580.0
    current_vol = 160000    # 爆量
    avg_vol_20 = 100000

else:
    # --- [實戰模式] 抓取真實數據 ---
    try:
        # 抓取台指期近月代碼 (TXFR1)
        contract = api.Contracts.Futures.TXF.TXFR1
        
        # 抓取 Snapshot (即時報價)
        snapshot = api.snapshots([contract])[0]
        
        current_close = snapshot.close
        current_high = snapshot.high
        current_low = snapshot.low
        current_open = snapshot.open
        current_vol = snapshot.total_volume
        
        # 實戰中，均量建議抓 K 線計算，這裡暫時寫死或手動輸入
        # 為了 MVP 穩定，先用固定值，後續可升級
        avg_vol_20 = 80000 

        if current_close == 0:
            st.warning("目前無盤中報價 (可能休市中)，請勾選上方「測試模式」查看效果")
            st.stop()
            
    except Exception as e:
        st.error(f"數據抓取錯誤: {e}")
        st.stop()

# --- 顯示數據指標 ---
# 計算漲跌
change = current_close - current_open
change_pct = (change / current_open) * 100 if current_open > 0 else 0
vol_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("目前價格", f"{current_close:.0f}", f"{change_pct:.2f}%")
col2.metric("預估量能", f"{vol_ratio:.1f}x", "20MA基準")
col3.metric("K棒狀態", "長黑" if change_pct < -1.5 else ("長紅" if change_pct > 1.5 else "震盪"))

st.divider()

# ==========================================
# 5. 訊號掃描結果
# ==========================================
st.subheader("📡 V4 戰略訊號")

# 呼叫大腦檢查
signals = check_v4_signal(current_open, current_high, current_low, current_close, current_vol, avg_vol_20)

if len(signals) == 0:
    st.success("✅ 今日無特殊訊號，請繼續空手觀望。")
    st.caption("V4 核心：不頻繁交易，只狙擊極端行情。")
    
    # 顯示延遲狩獵提醒 (手動觀察)
    with st.expander("🐢 關於【延遲狩獵】策略"):
        st.write("若**昨天**是大跌崩盤日，請觀察**今天**是否止跌。")
        st.write("若止跌，建議：**尾盤進場做多**。")
else:
    # 有訊號！發布警報
    for sig in signals:
        if sig["type"] == "danger":
            st.error(f"🚨 觸發：{sig['name']}")
        else:
            st.warning(f"⚡ 觸發：{sig['name']}")
            
        st.write(f"**詳細數據**：{sig['desc']}")
        st.markdown(f"### 👉 {sig['action']}")
        st.markdown("---")

# ==========================================
# 6. 歷史戰績 (激勵用)
# ==========================================
with st.expander("📜 V4 歷史戰績回顧 (激勵用)"):
    st.write("過去兩年經典戰役：")
    history_data = {
        "日期": ["2025-04-08", "2024-08-05", "2024-08-02"],
        "策略": ["延遲狩獵 (T+1)", "絕地求生", "絕地求生"],
        "獲利點數": ["+1698 點", "+265 點", "-331 點 (停損)"],
        "結果": ["🏆 大勝", "✅ 勝", "❌ 損"]
    }
    st.table(pd.DataFrame(history_data))
