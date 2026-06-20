# 樹莓派超級伺服器 (HA Custom Integration 雙向開發) 終極開發指南

這份文件是你未來在 VS Code 中開發專案的「頂級架構藍圖」。這是一條極具挑戰性但超級優雅的開發路線，請將這份文件餵給 AGY，讓 AGY 陪你一起完成這個史詩級的專案。

---

## 1. 專案架構概覽 (Architecture Overview)
為了實現「插上網路，HA 隨即跳出發現通知」的高級商業化體驗，我們已經放棄原本的 MQTT，全面改採**「HA 原生雙向開發」**架構。專案將拆分為兩個獨立的子系統：

1. **Pi Agent (樹莓派本地端)**：
   * 採用 Python `FastAPI` 建立極輕量級的 RESTful API。
   * 使用 `zeroconf` 套件在區域網路內進行 mDNS 廣播（也就是向 HA 招手：我在這裡！）。
2. **HA Custom Component (HA 原生外掛端)**：
   * 這是一套要發布給大家安裝在 Home Assistant 裡的擴充外掛（位於 `/config/custom_components/pi_agent/`）。
   * 內含 `config_flow.py`，專門攔截樹莓派的 mDNS 廣播，並觸發 HA 右上角的「發現新裝置」設定精靈。

---

## 2. 核心技術：Zeroconf 廣播與 Config Flow 攔截

### 📌 Pi Agent 端廣播 (Zeroconf)
樹莓派上的程式啟動時，會發送以下的 mDNS 廣播：
* **Type**: `_pi_agent._tcp.local.`
* **Name**: `Howard_Super_Pi._pi_agent._tcp.local.`
* **Properties**: 包含 IP、API Port、Mac Address。

### 📌 HA 端攔截 (Config Flow)
HA 的外掛中必須包含 `manifest.json` 來註冊監聽這個廣播：
```json
"zeroconf": [
  {"type": "_pi_agent._tcp.local."}
]
```
一旦收到廣播，HA 會自動呼叫我們寫好的 `async_step_zeroconf` 函數，畫面隨即彈出精美的加入精靈！

---

## 3. 雙向開發三階段詳細規格

### 🧱 【第一階段：基礎通訊與通知彈出】
**目標：打通 Zeroconf 廣播，讓 HA 成功跳出加入通知，並建立硬體監控。**
* **Pi 端工作**：
  * 架設基礎 API (`/api/metrics`)，回傳 CPU、RAM、溫度、Uptime 以及演算法推算出來的預估耗電量 (W)。
  * 實作 Zeroconf 廣播機制。
* **HA 端工作**：
  * 建立外掛骨架 (`__init__.py`, `manifest.json`)。
  * 實作 `config_flow.py` 完成加入精靈。
  * 實作 `sensor.py` 與 `DataUpdateCoordinator`，定時向 Pi 的 API 抓取數據並顯示在介面上。

### ⚙️ 【第二階段：雙向服務開關控制】
**目標：透過 API 操控 Linux 系統與 Docker 狀態。**
* **Pi 端工作**：
  * 新增 API 路由 (`/api/services`)，回傳 Docker 容器與原生服務 (SSH, Tailscale) 的狀態。
  * 新增控制路由 (`POST /api/services/{name}/start` 等)，利用 Python 的 `docker` 套件與 `os.system` 執行啟動/停止。
  * 實作一鍵清垃圾 (`docker system prune`) 與系統重開機 (`reboot`) 的 API。
* **HA 端工作**：
  * 實作 `switch.py` 平台。
  * 當使用者在 HA 按下開關時，發送 HTTP POST 請求至 Pi 的 API 執行動作，並等待回傳以更新按鈕狀態。

### 🔌 【第三階段：高階動態硬體擴充】 (難度極高)
**目標：深度整合作業系統底層硬體事件，做到完美的「隨插即用」。**
* **Pi 端工作**：
  * 使用 `pyudev` 監聽 USB 插入事件。插入時自動將硬碟資訊更新至 `/api/usb`。提供掛載/卸載 API (`POST /api/usb/{id}/mount`)。
  * 讀取本地 `gpio_config.json`，將有定義的引腳轉換成 API 端點供 HA 呼叫控制。
* **HA 端工作**：
  * Coordinator 必須具備「動態新增與刪除實體」的能力。
  * 當 API 回傳有新的 USB 插入時，HA 動態生成 Switch；拔出時，自動動態銷毀介面上的按鈕。

---

## 4. 國際化多國語系 (i18n) 實作架構
**目標：原生支援英、日、繁中、簡中，並實作未支援語系的自動防呆退回機制。**
* **實作方式**：在 HA 外掛目錄中建立 `translations/` 資料夾，不在此之外寫死任何介面文字。
* **必備語言檔案**：
  * `en.json` (英文 - **系統預設 Fallback 底線**)
  * `zh-Hant.json` (繁體中文)
  * `zh-Hans.json` (簡體中文)
  * `ja.json` (日文)
* **開發準則**：所有 Config Flow (加入精靈介面) 與實體名稱 (Entity Names)，皆必須使用 `translation keys` 參照上述 JSON 字典檔，交由 HA 底層依據使用者瀏覽器語系進行自動渲染與判定。

---

## 5. VS Code + AGY 實戰開發指令指南

你即將挑戰的是高階軟體工程師的領域，但有了這份藍圖與 AGY 的幫助，絕對能順利過關！請在 VS Code 裡對 AGY 助理下達這句神級指令：

> **「AGY 你好，請閱讀這份 `HA_Agent_Development_Guide.md`。我是這個專案的負責人，我們將採用最高級的『HA 原生外掛雙向開發 (FastAPI + Zeroconf)』架構，並支援多國語系。請直接幫我開始實作『第一階段』，從 Pi 端的 FastAPI 與 Zeroconf 廣播程式碼開始寫起，接著教我怎麼寫 HA 端的 `config_flow.py`，請一步一步帶著我寫！」**
