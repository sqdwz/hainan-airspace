# 海南省禁飞及空域管制公告日报

一个静态网页，用于汇总海南省范围内公开发布的禁飞、临时禁飞、低慢小航空器及空域管制信息。

## 自动更新方式

本项目不需要额外服务器，当前采用：

**ChatGPT 定时任务 → GitHub 数据文件 → GitHub Pages**

- ChatGPT 定时任务每天北京时间中午检索海南禁飞/空域管制公开信息。
- 检索后直接读取并更新本仓库 `data/notices.json`、`data/latest.json`。
- 同时保存 `data/history/YYYY-MM-DD.json` 作为当天历史日报。
- `data/notices.json` 用于去重、保留旧公告和更新 active / upcoming / ended 状态。
- 首页固定读取 `data/latest.json`，因此网址不变、内容随数据更新。
- 每次 `main` 分支数据发生变化后，`.github/workflows/pages.yml` 会自动重新部署网页。

因此，日常更新不依赖仓库里的 Python 定时脚本；GitHub 只负责存储数据和发布页面。

## 手动备用更新

仓库保留了一套 Python 检索脚本作为备用方案，但不会每天自动运行。

需要手动执行时，在仓库 **Actions** 页面打开 `Manual Hainan Airspace Fallback`，点击 **Run workflow**。

相关文件：

- `scripts/update.py`：备用检索与状态判断脚本
- `.github/workflows/daily-update.yml`：仅手动触发的备用工作流

## GitHub Pages

在仓库 **Settings → Pages** 中，**Build and deployment → Source** 使用：

`GitHub Actions`

网页由 `.github/workflows/pages.yml` 自动部署。

固定网址：

`https://sqdwz.github.io/hainan-airspace/`

当前仓库已设为 **Public**，并已启用 GitHub Pages。

## 当前文件

- `index.html`：日报网页
- `styles.css`：页面样式
- `app.js`：读取并渲染日报数据
- `data/latest.json`：最新日报
- `data/notices.json`：公告去重数据库
- `data/history/`：历史日报
- `scripts/update.py`：手动备用检索脚本
- `.github/workflows/daily-update.yml`：手动备用更新
- `.github/workflows/pages.yml`：网页自动部署

## 说明

公开网页检索可能存在页面未及时收录、网页结构变化、信息提取不完整等情况。该日报用于辅助检查，不替代 UOM 实时空域状态、NOTAM、军民航空管批复及属地审批要求。
