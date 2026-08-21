# 海南省禁飞及空域管制公告日报

固定网页展示海南省范围内禁飞、临时禁飞、低慢小航空器和空域管制公开信息。

## 自动更新方式

本项目采用“ChatGPT 定时任务 + GitHub 数据文件”的方式更新，不需要额外服务器。

- ChatGPT 定时任务每天北京时间中午检查海南禁飞/空域管制公开信息。
- 检索后直接更新本仓库 `data/latest.json`。
- 同时保存 `data/history/YYYY-MM-DD.json` 作为历史日报。
- 网页固定读取 `data/latest.json`，因此网址不变、内容自动变化。

## GitHub Pages

在 GitHub 打开：

`Settings → Pages → Build and deployment → Source: Deploy from a branch`

选择：

- Branch: `main`
- Folder: `/ (root)`

保存后，项目站点通常为：

`https://sqdwz.github.io/hainan-airspace/`

> GitHub Free 需要公共仓库才能使用 GitHub Pages；GitHub Pro 可从私有仓库发布 Pages。即使仓库为私有，只要 Pages 已发布，Pages 网站本身仍是公开访问的。

## 当前文件

- `index.html`：日报网页
- `styles.css`：页面样式
- `app.js`：读取并渲染日报数据
- `data/latest.json`：当前最新日报
- `data/history/`：每日历史快照

## 说明

本项目用于公开信息汇总和飞行前辅助检查，不替代 UOM 实时空域状态、NOTAM、军民航空管批复及属地公安/空管要求。
