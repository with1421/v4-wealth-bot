import streamlit as st

st.title("🕵️‍♀️ 金庫偵測模式")

# 1. 檢查 Secrets 是否存在
if not st.secrets:
    st.error("❌ 嚴重錯誤：App 完全讀不到任何 Secrets！")
    st.info("可能原因：Streamlit Cloud 後台的 Secrets 欄位是空的，或是沒有按 Save。")
    st.stop()

# 2. 檢查有哪些「分類」 (Top-level keys)
# 我們只印出 Key，不印出密碼，確保安全
keys = list(st.secrets.keys())
st.write(f"目前讀取到的分類 Keys: {keys}")

# 3. 專門檢查 shioaji
if "shioaji" in st.secrets:
    st.success("✅ 成功找到 [shioaji] 分類！")
    # 再深入檢查裡面的 api_key
    if "api_key" in st.secrets["shioaji"]:
        st.success("✅ 成功找到 api_key！")
        # 顯示前兩碼確認不是空的 (例如 "P9***")
        key_val = st.secrets["shioaji"]["api_key"]
        st.info(f"Key 的前兩碼為: {key_val[:2]}***")
    else:
        st.error("❌ 找到 shioaji 分類，但裡面沒有 api_key！")
else:
    st.error("❌ 找不到 [shioaji] 分類！")
    st.warning("請檢查 Secrets 設定，第一行必須是 [shioaji]")
