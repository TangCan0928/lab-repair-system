# -*- coding: utf-8 -*-
"""
AI 辅助分析引擎（本地规则版）。
不依赖外部大模型 API，通过关键词 + 知识库匹配完成：
  - 故障摘要
  - 故障类别判定
  - 紧急程度判定
  - 初步排查建议（优先引用知识库条目）
  - 信息不足时标记 need_manual = True，提示人工确认
"""
import re
from knowledge_base import search

# 紧急程度触发词
URGENT_HIGH_WORDS = [
    "急", "紧急", "立即", "马上", "立刻", "赶紧", "实验课", "答辩",
    "考试", "演示", "演示课", "马上要", "现在", "今天要用", " deadline",
    "马上实验", "整组", "全部", "全实验室", "断电", "起火", "冒烟",
    "触电", "漏水", "短路",
]
URGENT_MID_WORDS = [
    "无法", "不能", "连不上", "不行", "坏了", "故障", "报错", "异常",
    "失败", "用不了", "打不了", "开不了",
]

# 信息完整性：描述过短阈值
MIN_DESC_LEN = 5


def _detect_urgency(description: str, device_name: str = "") -> str:
    """根据关键词判断紧急程度：高 / 中 / 低。"""
    text = f"{description} {device_name}".lower()
    for w in URGENT_HIGH_WORDS:
        if w.lower() in text:
            return "高"
    for w in URGENT_MID_WORDS:
        if w.lower() in text:
            return "中"
    return "低"


def _detect_info_missing(description: str, reporter: str, device_name: str,
                         location: str, contact: str) -> list:
    """检查必填字段是否缺失/异常，返回需要补充说明的问题列表。"""
    problems = []
    if not reporter or not reporter.strip():
        problems.append("报修人未填写")
    if not device_name or not device_name.strip():
        problems.append("设备名称未填写")
    if not location or not location.strip():
        problems.append("位置未填写")
    if not contact or not contact.strip():
        problems.append("联系方式未填写")
    desc = (description or "").strip()
    if len(desc) < MIN_DESC_LEN:
        problems.append(f"故障描述过短（{len(desc)}字），无法判断现象")
    if re.fullmatch(r"[?？。，,\s]+", desc):
        problems.append("故障描述无实质内容")
    return problems


def _make_summary(description: str, device_name: str, matched) -> str:
    """生成一句话故障摘要。"""
    desc = (description or "").strip().replace("\n", " ")
    # 截取前 40 字作为描述主体
    snippet = desc[:40] + ("…" if len(desc) > 40 else "")
    if matched:
        top = matched[0]
        return f"【{device_name or '未知设备'}】疑似「{top['name']}」：{snippet}"
    return f"【{device_name or '未知设备'}】{snippet or '未提供故障描述'}"


def analyze(reporter: str, device_name: str, location: str,
            description: str, contact: str):
    """
    主分析入口。返回 dict：
      category, urgency, summary, suggestion, matched_kb,
      need_manual, info_problems, top_match
    """
    info_problems = _detect_info_missing(description, reporter, device_name,
                                         location, contact)
    # 知识库匹配
    matched = search(description or "", top_n=3)

    # 类别判定：取最高分条目的类别；无匹配则“其他”
    if matched:
        category = matched[0]["category"]
    else:
        category = "其他"

    urgency = _detect_urgency(description, device_name)

    summary = _make_summary(description, device_name, matched)

    # 建议：有匹配则引用知识库，无匹配给出通用建议
    if matched:
        top = matched[0]
        suggestion = (
            f"参考知识库《{top['name']}》（命中关键词：{ '、'.join(top['hits']) }）：\n"
            f"{top['suggestions']}"
        )
        matched_kb = "；".join(f"#{m['id']} {m['name']}(得分{m['score']})" for m in matched)
    else:
        suggestion = (
            "知识库中未找到高匹配条目，请报修人补充以下信息后由人工排查：\n"
            "1) 设备品牌型号；2) 故障发生时间与频率；\n"
            "3) 是否有报错代码/提示音；4) 最近是否改动过软件或接线。"
        )
        matched_kb = "无高匹配条目"

    # 是否需要人工确认：信息缺失 或 无知识库匹配 或 紧急度高
    need_manual = 1 if (info_problems or not matched or urgency == "高") else 0

    return {
        "category": category,
        "urgency": urgency,
        "summary": summary,
        "suggestion": suggestion,
        "matched_kb": matched_kb,
        "need_manual": need_manual,
        "info_problems": info_problems,
        "top_match": matched[0] if matched else None,
    }


if __name__ == "__main__":
    # 简单自测
    cases = [
        ("张三", "STM32开发板", "实验室302", "今天实验课要用，板子下载不进去程序，串口也没反应", "13800000001"),
        ("李四", "显示器", "实验室301", "屏幕不亮", "13800000002"),
        ("王五", "台式机", "实验室305", "", "13800000003"),
        ("赵六", "电脑", "实验室302", "经常蓝屏重启", "13800000004"),
        ("钱七", "投影仪", "会议室", "无信号", "13800000005"),
    ]
    for c in cases:
        r = analyze(*c)
        print("-" * 60)
        print("报修人:", c[0], "| 设备:", c[1], "| 描述:", c[3])
        print("类别:", r["category"], "| 紧急:", r["urgency"], "| 需人工:", bool(r["need_manual"]))
        print("摘要:", r["summary"])
        print("匹配:", r["matched_kb"])
        print("建议:", r["suggestion"][:80], "…")
        if r["info_problems"]:
            print("信息问题:", r["info_problems"])
