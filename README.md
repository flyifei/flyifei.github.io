# FLYIFEI · 通往国泰驾驶舱

个人网站，记录我申请国泰航空见习飞行员培训计划（Cadet Pilot Programme）的全过程。

线上地址：**https://flyifei.github.io**

## 页面

| 文件 | 内容 |
| --- | --- |
| `index.html` | 首页：目标、当前阶段进度、四个板块入口、时间线 |
| `apply.html` | 申请信息：资格要求对照表、英语成绩要求、六步遴选流程、材料清单 |
| `cathay.html` | 国泰与训练：职级阶梯、80 周训练路径、机队、第二副驾驶待遇 |
| `resources.html` | 学习资料：官方资料、ATPL 科目、英语与陆空通话、MSFS 练习科目、书单 |
| `logbook.html` | 飞行记录：MSFS 与真实飞行分开记录，自动统计 |
| `404.html` | 错误页 |

## 目录结构

```
.
├── index.html / apply.html / cathay.html / resources.html / logbook.html / 404.html
├── assets/
│   ├── css/style.css        # 全站样式（深色、无依赖）
│   ├── js/main.js           # 导航、滚动动画、数字动画、清单本地保存、标签切换
│   ├── js/logbook.js        # 读取 JSON 渲染飞行记录与统计
│   ├── data/msfs.json       # 模拟机记录（自己往里加）
│   ├── data/real-flights.json # 真实飞行记录
│   └── img/favicon.svg
└── .nojekyll                # 告诉 GitHub Pages 不要跑 Jekyll
```

## 本地预览

飞行记录页要读 JSON，必须走 HTTP，不能直接双击 `file://` 打开。

```powershell
cd flyifei-site
python -m http.server 8080
# 然后浏览器打开 http://localhost:8080
```

没有 Python 的话，用 Node 也行：

```powershell
npx serve .
```

## 新增一条飞行记录

编辑 `assets/data/msfs.json` 或 `assets/data/real-flights.json`，在 `flights` 数组里加一个对象：

```json
{
  "date": "2026-12-01",
  "type": "A320neo",
  "reg": "B-LCN",
  "from": "VHHH",
  "to": "VMMC",
  "hours": 1.2,
  "ldg": 2,
  "cat": "区域航线",
  "remarks": "今天练了什么、哪里出错"
}
```

- `hours` 小时（可小数），`ldg` 降落次数
- `from` / `to` 用 ICAO 四字码：VHHH 香港、VMMC 澳门、EGLL 伦敦希思罗
- 去掉 `"example": true` 就不会再显示「示例」标签
- 加完保存、刷新页面即可，统计自动重算

## 改其他内容

- **当前进度**：`index.html` 里搜 `data-progress`，把 `27` 换成你的百分比；旁边「第 3 / 11 步」也一起改
- **时间线**：`index.html` 搜 `timeline`，复制 `<div class="tl-item">` 改内容；`done` / `future` 控制节点样式
- **申请清单**：`apply.html` 搜 `check-item`，复制一行改 `data-key`（`data-key` 唯一即可）
- **资料条目**：`resources.html` 搜 `linklist`，按现有格式加 `<li><a ...>`
- **里程碑**：`logbook.html` 搜 `Milestones`

## 部署

仓库已开 GitHub Pages（用户站点 `flyifei.github.io`，从 `master` 分支根目录发布），推上去就是线上版本：

```powershell
git add .
git commit -m "更新飞行记录 / 申请进度"
git push
```

站点是纯静态的，不需要构建、不需要 Actions。

## 说明

- 站内的国泰相关信息（约 80 周培训、资格要求、遴选流程、第二副驾驶薪酬）抓取自国泰招聘官网，数据截至 2026 年 1 月；政策会变，请以官网为准。
- 本页是个人记录，不代表国泰航空官方立场。