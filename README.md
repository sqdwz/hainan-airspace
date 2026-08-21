# 海南省禁飞及空域管制公告日报

固定网页展示海南省范围内禁飞、临时禁飞、低慢小航空器和空域管制公开信息。

## 自动更新

- GitHub Actions 每天北京时间约 12:00 自动运行。
- 自动检索海南省政府、文昌、海口、三亚、琼海、CAAC、民航海南监管局以及机场/新闻公开信息。
- 更新 `data/latest.json`，并保存 `data/history/YYYY-MM-DD.json`。
- 网页固定读取 `data/latest.json`。

## GitHub Pages

仓库有内容后，在 GitHub 打开：

`Settings → Pages → Build and deployment → Source: Deploy from a branch`

选择：

- Branch: `main`
- Folder: `/ (root)`

保存后，项目站点通常为：

`https://sqdwz.github.io/hainan-airspace/`

> 提示：GitHub Free 需要公共仓库才能使用 GitHub Pages；GitHub Pro 可从私有仓库发布 Pages。

## 说明

本项目用于公开信息汇总和飞行前辅助检查，不替代 UOM 实时空域状态、NOTAM、军民航空管批复及属地公安/空管要求。
