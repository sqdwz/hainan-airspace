# 海南省禁飞及空域管制公告日报

一个静态网页，用于汇总海南省范围内公开发布的禁飞、临时禁飞、低慢小航空器及空域管制信息。

## 自动更新方式

本项目不需要额外服务器：

- 首页固定读取 `data/latest.json`。
- GitHub Actions 每天北京时间 12:00 左右运行 `scripts/update.py`。
- 自动搜索海南相关公开信息并更新数据。
- 同时保存 `data/history/YYYY-MM-DD.json` 历史快照。
- `data/notices.json` 用于去重和保留已发现公告。
- 根据管制时间自动判断“正在生效 / 即将生效 / 已结束”。

## 手动更新

在仓库 **Actions** 页面打开 `Daily Hainan Airspace Update`，点击 **Run workflow**。

## GitHub Pages

在仓库 **Settings → Pages** 中选择：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/ (root)`

启用后固定网址通常为：

`https://sqdwz.github.io/hainan-airspace/`

> 当前仓库为 Private。GitHub Pages 对私有仓库的支持取决于 GitHub 账户方案；如果使用 GitHub Free，最省事的方式是将该仓库改为 Public。

## 当前文件

- `index.html`：日报网页
- `styles.css`：页面样式
- `app.js`：读取并渲染日报数据
- `data/latest.json`：最新日报
- `data/notices.json`：公告去重数据库
- `data/history/`：历史日报
- `scripts/update.py`：每日检索与状态判断脚本
- `.github/workflows/daily-update.yml`：每日自动运行配置

## 说明

该项目依赖公开网页及搜索结果，可能存在网页未及时收录、页面结构变化或信息提取不完整的情况。实际无人机飞行前仍应核对 UOM、NOTAM、相关空管及属地审批要求。
