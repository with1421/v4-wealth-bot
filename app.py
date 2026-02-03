import streamlit as st
import shioaji as sj
import pandas as pd
import datetime

# ==========================================
# 1. 頁面設定
# ==========================================
st.set_page_config(page_title="V4 財富分配中控台", page_icon="💎", layout="centered")
st.title("💎 V4 財富分配中控台")
st.caption("專注於極端行情的財富重分配機會")

# ==========================================
# 2. 連線設定 (永豐 API)
# ==========================================
@st.cache_resource
def init_shioaji():
    api = sj.Shioaji(simulation=True) # 模擬模式
    try:
        api.login(
            api_key=st.secrets["shioaji"]["api_key"], 
            secret_key=st.secrets["shioaji"]["secret_key"]
        )
        return api, "✅ 連線成功"
    except Exception as e:
        return None, f"❌ 連線失敗: {str(e)}"

api, status_msg = init_shioaji()

# 顯示連線狀態
if api:
    st.success(f"系統狀態：{status_msg}")
else:
    st.error(f"系統狀態：{status_msg}")
    st.stop() # 連線失敗就停止執行

st.divider()

# ==========================================
# 3. 策略邏輯核心 (V4 Brain)
# ==========================================
def check_v4_signal(open_price, high_price, low_price, close_price, vol, avg_vol):
    """
    輸入今天的數據，回傳是否有 V4 訊號
    """
    signals = []
    
    # 計算關鍵指標
    day_ret_pct = (close_price - open_price) / open_price * 100
    vol_ratio = vol / avg_vol if avg_vol > 0 else 0
    upper_shadow = high_price - close_price
    body_len = abs(close_price - open_price)
    
    # 策略 A: 絕地求生 (Panic Climax)
    # 條件: 跌幅 > 1.5% 且 爆量 > 1.5倍
    if day_ret_pct < -1.5 and vol_ratio > 1.5:
        signals.append({
            "name": "🩸 絕地求生 (Panic Climax)",
            "desc": f"跌幅 {day_ret_pct:.2f}% | 量能 {vol_ratio:.1f}倍 | 恐慌極致，準備反彈",
            "action": "尾盤做多 (留倉)",
            "type": "error" # 紅色警示
        })

    # 策略 B: 飛龍在天 (Strongest Momentum)
    # 條件: 漲幅 > 1.5% 且 光頭紅棒 (上影線 < 實體20%)
    if day_ret_pct > 1.5 and upper_shadow < (body_len * 0.2):
        signals.append({
            "name": "🐉 飛龍在天 (Momentum)",
            "desc": f"漲幅 {day_ret_pct:.2f}% | 收最高 | 多頭動能強勁",
            "action": "尾盤做多 (留倉)",
            "type": "error" # 紅色警示
        })
        
    return signals

# ==========================================
# 4. 儀表板顯示區
# ==========================================
st.subheader("🔍 今日盤勢監控")

# 這裡我們先用「模擬數據」來測試介面
# 因為現在可能是收盤時間，抓不到即時跳動
# 我們做一個開關，讓你可以手動切換「正常模式」與「測試訊號模式」

use_test_data = st.checkbox("開啟測試模式 (強制生成訊號)", value=False)

if use_test_data:
    # --- 測試情境：模擬某天大跌爆量 ---
    current_open = 22000.0
    current_high = 22100.0
    current_low = 21500.0
    current_close = 21550.0 # 大跌
    current_vol = 150000    # 爆量
    avg_vol_20 = 80000
    st.warning("⚠️ 目前使用測試數據")
else:
    # --- 實戰情境：嘗試抓取真實數據 (若收盤可能抓不到，會顯示0) ---
    try:
        # 抓取台指期近月 (TXFR1)
        contract = api.Contracts.Futures.TXF.TXFR1
        # 抓取日K (1分K太細，我們看日K趨勢)
        # 注意: Shioaji 模擬環境的歷史資料可能不完整，這裡僅示範邏輯
        # 實戰中建議抓 1分K 再自己合成日K，或者直接抓 Quote
        snapshot = api.snapshots([contract])[0]
        
        current_close = snapshot.close
        current_high = snapshot.high
        current_low = snapshot.low
        current_open = snapshot.open
        current_vol = snapshot.total_volume
        avg_vol_20 = 100000 # 暫時寫死，因為歷史均量需要抓更長資料
        
        if current_close == 0:
            st.info("目前無盤中報價 (可能休市中)，請勾選上方「測試模式」查看效果")
            st.stop()
            
    except Exception as e:
        st.error(f"數據抓取錯誤: {e}")
        st.stop()

# 計算漲跌
change = current_close - current_open
change_pct = (change / current_open) * 100
vol_ratio = current_vol / avg_vol_20

# 顯示三大指標 (Metric)
col1, col2, col3 = st.columns(3)
col1.metric("目前價格", f"{current_close:.0f}", f"{change_pct:.2f}%")
col2.metric("預估量能比", f"{vol_ratio:.1f}x", "20MA基準")
col3.metric("K棒型態", "長黑" if change_pct < -1.5 else ("長紅" if change_pct > 1.5 else "震盪"))

st.divider()

# ==========================================
# 5. 訊號掃描結果
# ==========================================
st.subheader("📡 V4 戰略訊號")

# 呼叫大腦檢查
signals = check_v4_signal(current_open, current_high, current_low, current_close, current_vol, avg_vol_20)

if len(signals) == 0:
    st.success("✅ 今日無特殊訊號，請繼續空手觀望。")
    st.caption("V4 策略核心：不頻繁交易，只狙擊極端行情。")
else:
    for sig in signals:
        if sig["type"] == "error":
            st.error(f"🚨 觸發：{sig['name']}")
        else:
            st.warning(f"⚡ 觸發：{sig['name']}")
            
        st.write(f"**詳細數據**：{sig['desc']}")
        st.write(f"**建議操作**：{sig['action']}")
        st.markdown("---")

# ==========================================
# 6. (選用) 歷史回測數據展示
# ==========================================
with st.expander("查看 V4 歷史戰績 (參考)"):
    st.write("過去兩年觸發紀錄：")
    data = {
        "日期": ["2025-04-08", "2024-08-05", "2024-08-02"],
        "策略": ["延遲狩獵", "絕地求生", "絕地求生"],
        "獲利點數": ["+1698", "+265", "-331"],
        "結果": ["大勝", "勝", "停損"]
    }
    st.table(pd.DataFrame(data))