# 小朋友下樓梯 (NS-SHAFT) — 網頁版 🎮

使用 HTML5 Canvas + JavaScript 實作的「小朋友下樓梯」單機網頁遊戲。

直接用瀏覽器打開 `index.html` 即可遊玩，無需安裝任何東西。

## 執行方式

```bash
open 3rd-game/index.html       # macOS
xdg-open 3rd-game/index.html   # Linux
start 3rd-game/index.html      # Windows
```

## 操作方式

| 按鍵 | 功能 |
|------|------|
| `A` / `←` | 左移 |
| `D` / `→` | 右移 |
| `P` / `Esc` | 暫停 |
| `Q` | 退出 |
| `Enter` / `Space` | 開始 / 重試 |

## 平台類型

| 平台 | 顏色 | 效果 |
|------|------|------|
| 普通 | 🟢 綠色 | 正常站立 |
| 傷害 ⚡ | 🔴 紅色 | 踩到扣血 |
| 補血 💚 | 💚 亮綠 | 踩到回血 |
| 移動 ↔ | 🔵 藍色 | 左右移動 |
| 崩壞 💥 | 🟤 棕色 | 踩一下就碎 |
| 彈簧 🔺 | 🟡 黃色 | 踩到會大力彈跳 |

## 遊戲特色

- 🎮 HTML5 Canvas 渲染，流暢 60 FPS
- ✨ 粒子特效（傷害、回血、彈簧、角色尾跡）
- 🌟 星空背景 + 動態尖刺動畫
- 📈 難度隨時間遞增
- 🏆 本地排行榜（localStorage）
- 🎨 漸層、光暈、角色表情動畫
- ⏸ 開始畫面 / 暫停 / Game Over 畫面
- 📱 單一 HTML 檔案，無需伺服器

## 專案結構

```
3rd-game/
├── index.html   # 完整遊戲（HTML + CSS + JS 全包）
└── README.md    # 本文件
```
