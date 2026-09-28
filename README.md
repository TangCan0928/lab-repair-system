# 实验室设备报修与 AI 智能工单系统

> 专升本大三 · 小组考核项目 · 本地最小可用版
> 技术栈：**Python + Streamlit + SQLite**

## 小组成员

| 姓名 | 角色 | 主要负责 |
| ---- | ---- | -------- |
| 唐灿 | 组长 | 项目搭建、数据库、AI 分析引擎、Git 仓库管理 |
| 谢曼婕 | 组员 | 知识库整理、测试用例、文档与 README |

## 一、功能一览

| 序号 | 功能 | 说明 |
| ---- | ---- | ---- |
| 1 | 报修提交 | 填写报修人、设备名称、位置、故障描述、联系方式；自动生成工单编号与提交时间 |
| 2 | 数据存储 | SQLite 持久化，程序重启后数据仍在（`data/repair.db`） |
| 3 | AI 辅助分析 | 规则引擎 + 关键词匹配，输出故障摘要、类别、紧急度、初步建议；信息不足时标记需人工确认 |
| 4 | 知识库匹配 | 内置 10 条常见故障及处理办法，AI 建议优先引用知识库并显示命中条目 |
| 5 | 工单管理 | 列表查看、按类别/状态/关键词筛选、详情、修改状态（待处理/处理中/已完成）、填写处理结果 |
| 6 | 简单统计 | 工单总数、各类别数量、各状态数量、各紧急度数量，柱状图可视化 |

## 二、目录结构

```
lab_repair_system/
├── app.py               # Streamlit 主应用（入口）
├── database.py          # SQLite 建表与 CRUD
├── ai_engine.py         # AI 辅助分析引擎（规则版，无需 API Key）
├── knowledge_base.py    # 故障知识库（10 条）
├── requirements.txt     # 依赖清单
├── README.md            # 本文件
├── data/
│   └── repair.db        # SQLite 数据库（首次运行自动生成）
├── test_cases/
│   ├── seed_test_data.py   # 一键灌入 12 条模拟测试工单
│   └── test_workorders.md  # 12 条测试工单与测试结果
├── docs/
│   ├── test_report.md       # 测试报告（含 2 个真实失败案例与修复过程）
│   ├── ai_usage_record.md   # AI 使用记录
│   ├── code_review.md       # 代码审阅记录
│   ├── contribution.md      # 个人贡献说明
│   └── version_changes.md   # 第一版与最终版变化说明
└── lab_repair_system_v1.0_final.zip   # 最终代码压缩包（提交材料）
```

## 三、环境准备与启动

### 1. 安装依赖

建议使用虚拟环境（PyCharm 中新建项目时已自动建好）：

```bash
cd lab_repair_system
pip install -r requirements.txt
```

### 2. 启动系统

```bash
cd lab_repair_system
streamlit run app.py
```

启动后浏览器会自动打开 <http://localhost:8501>。

### 3. 在 PyCharm 中运行

1. 用 PyCharm 打开 `lab_repair_system` 文件夹；
2. 右下角选择已安装依赖的 Python 解释器；
3. 打开终端，先执行 `cd lab_repair_system`，再执行 `streamlit run app.py`；
4. 或新建 Run Configuration：Script 填 `app.py`，Parameters 留空，Working directory 填项目根目录。

## 四、内置账号 / 角色说明

本系统按任务书要求**不做注册登录与复杂权限**，**无需任何账号**，启动即用，分两个使用视角：

- **普通使用者**：在「📝 提交报修」页提交工单（不需要登录，直接填表）；
- **管理员/维修人员**：在「🗂️ 工单管理」页查看、筛选、处理工单，在「📊 统计看板」查看概览。

> 示例工单：可直接用数据库预置的 12 条测试工单演示，或提交新的报修（如报修人"张三"、设备"显示器"、位置"实验室302"、描述"屏幕不亮"）。

## 五、AI 分析说明

为了保证**完全本地可运行、不依赖外部大模型 API**，本系统的“AI”采用规则引擎：

- **类别判定**：把故障描述与知识库 10 条目的关键词做命中打分，取最高分条目的类别；无命中则归为“其他”。
- **紧急程度**：命中“急/立即/实验课/答辩/马上”等高优词判为“高”；命中“无法/不能/报错”等判为“中”；其余为“低”。
- **摘要**：拼接设备名 + 疑似故障名 + 描述前 40 字。
- **建议**：直接引用知识库条目的排查步骤；无匹配时引导报修人补充信息。
- **需人工确认**：当必填字段缺失、描述过短、知识库无匹配或紧急度为高时，自动置位 `need_manual=1`。

## 六、测试数据

运行以下脚本可一键灌入 12 条模拟工单（覆盖正常、模糊、紧急、知识库外、同义表达、异常输入）：

```bash
python test_cases/seed_test_data.py
```

详见 `test_cases/test_workorders.md` 与 `docs/test_report.md`（含 2 个真实失败案例）。

## 七、Git 协作约定（小组参考）

- `main` 分支保持可运行；成员各开 `feature/xxx` 分支开发；
- 提交信息使用 `feat: / fix: / docs: / test:` 前缀；
- 每人至少 5 次有效提交，分布在至少 2 个时间段；
- 合并前在 Issues 中记录负责人与目标。

## 八、最终提交材料清单（自检）

| # | 材料 | 位置 |
|---|------|------|
| 1 | Git 仓库地址及最终代码压缩包 | `https://github.com/TangCan0928/lab-repair-system` + `lab_repair_system_v1.0_final.zip` |
| 2 | README 运行说明、依赖清单、启动方式 | 本文件 + `requirements.txt` |
| 3 | 数据库文件/建表脚本 | `data/repair.db` + `database.py` |
| 4 | 故障知识库（10 条，≥8） | `knowledge_base.py` |
| 5 | 12 条测试工单及结果 | `test_cases/` |
| 6 | 2 个失败案例及修改过程 | `docs/test_report.md` |
| 7 | AI 使用记录 | `docs/ai_usage_record.md` |
| 8 | Git 提交记录、代码审阅、个人贡献 | Git 仓库 + `docs/code_review.md` + `docs/contribution.md` |
| 9 | 3-5 分钟演示视频 | 待录制（脚本见考核说明） |
| 10 | 第一版与最终版变化说明 | `docs/version_changes.md` |
