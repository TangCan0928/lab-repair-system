# -*- coding: utf-8 -*-
"""
实验室设备报修与 AI 智能工单系统 —— Streamlit 主应用。

启动方式：
    streamlit run app.py
"""
import streamlit as st

import database as db
import ai_engine
from knowledge_base import get_all

st.set_page_config(
    page_title="实验室设备报修与AI工单系统",
    page_icon="🔧",
    layout="wide",
)

# 初始化数据库（幂等）
db.init_db()

STATUS_COLOR = {
    db.STATUS_PENDING: "#ff4b4b",
    db.STATUS_PROCESSING: "#ffa500",
    db.STATUS_DONE: "#2ecc71",
}
URGENCY_COLOR = {"高": "#ff4b4b", "中": "#ffa500", "低": "#2ecc71"}


def page_submit():
    """页面 1：提交报修。"""
    st.header("📝 提交设备报修")
    st.caption("填写以下信息，系统会自动生成工单编号并调用 AI 辅助分析。")

    with st.form("repair_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            reporter = st.text_input("报修人 *", placeholder="例如：张三")
            location = st.text_input("设备位置 *", placeholder="例如：实验室302")
        with c2:
            device_name = st.text_input("设备名称 *", placeholder="例如：STM32开发板 / 显示器")
            contact = st.text_input("联系方式 *", placeholder="例如：13800000001 或 企业微信")
        description = st.text_area(
            "故障描述 *",
            height=120,
            placeholder="请尽量描述清楚：发生了什么现象、什么时候开始、是否有报错信息……",
        )
        submitted = st.form_submit_button("🚀 提交报修", type="primary", use_container_width=True)

    if submitted:
        # 必填校验
        missing = []
        if not reporter.strip():
            missing.append("报修人")
        if not device_name.strip():
            missing.append("设备名称")
        if not location.strip():
            missing.append("位置")
        if not contact.strip():
            missing.append("联系方式")
        if not description.strip():
            missing.append("故障描述")
        if missing:
            st.error(f"请填写必填项：{ '、'.join(missing) }")
            return

        # AI 分析
        result = ai_engine.analyze(
            reporter=reporter.strip(),
            device_name=device_name.strip(),
            location=location.strip(),
            description=description.strip(),
            contact=contact.strip(),
        )
        new_id, ticket_no = db.create_workorder(
            reporter=reporter.strip(),
            device_name=device_name.strip(),
            location=location.strip(),
            description=description.strip(),
            contact=contact.strip(),
            category=result["category"],
            urgency=result["urgency"],
            summary=result["summary"],
            suggestion=result["suggestion"],
            matched_kb=result["matched_kb"],
            need_manual=result["need_manual"],
        )
        st.success(f"✅ 工单已提交！工单编号：**{ticket_no}**（ID={new_id}）")

        # 展示 AI 分析结果
        st.subheader("🤖 AI 辅助分析结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("故障类别", result["category"])
        col2.metric("紧急程度", result["urgency"])
        col3.metric(
            "需人工确认",
            "是" if result["need_manual"] else "否",
        )
        st.markdown(f"**故障摘要：** {result['summary']}")
        with st.expander("📚 匹配的知识库条目", expanded=True):
            st.write(result["matched_kb"])
        with st.expander("💡 初步排查建议", expanded=True):
            st.write(result["suggestion"])
        if result["info_problems"]:
            st.warning("⚠️ 信息不足，已标记需人工确认：" + "；".join(result["info_problems"]))


def page_manage():
    """页面 2：工单管理（列表 + 筛选 + 详情处理）。"""
    st.header("🗂️ 工单管理")

    # 筛选区
    f1, f2, f3 = st.columns(3)
    with f1:
        f_category = st.selectbox("按类别筛选", ["全部"] + db.CATEGORIES)
    with f2:
        f_status = st.selectbox("按状态筛选", ["全部"] + db.VALID_STATUSES)
    with f3:
        f_keyword = st.text_input("关键词搜索（报修人/设备/描述/工单号）")

    rows = db.list_workorders(category=f_category, status=f_status, keyword=f_keyword.strip() or None)
    st.caption(f"共 {len(rows)} 条工单")

    if not rows:
        st.info("暂无符合条件的工单。")
        return

    # 列表用 DataFrame 风格展示
    show_cols = ["ticket_no", "reporter", "device_name", "location",
                 "category", "urgency", "status", "created_at"]
    import pandas as pd
    df = pd.DataFrame(rows)[show_cols]
    df.columns = ["工单号", "报修人", "设备", "位置", "类别", "紧急", "状态", "提交时间"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 选择某条工单查看详情
    st.divider()
    options = {f"{r['ticket_no']} | {r['device_name']} | {r['status']}": r["id"] for r in rows}
    selected_label = st.selectbox("选择一条工单查看详情 / 处理", list(options.keys()))
    wo = db.get_workorder(options[selected_label])
    if not wo:
        st.warning("未找到该工单。")
        return

    # 详情展示
    st.subheader(f"工单详情 — {wo['ticket_no']}")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**报修人：** {wo['reporter']}")
    c1.markdown(f"**联系方式：** {wo['contact']}")
    c2.markdown(f"**设备：** {wo['device_name']}")
    c2.markdown(f"**位置：** {wo['location']}")
    c3.markdown(f"**提交时间：** {wo['created_at']}")
    c3.markdown(f"**最后更新：** {wo['updated_at']}")

    st.markdown(f"**故障描述：**\n> {wo['description']}")

    # AI 分析结果
    with st.expander("🤖 AI 分析结果", expanded=True):
        a1, a2, a3 = st.columns(3)
        a1.markdown(f"**类别：** {wo['category']}")
        a2.markdown(f"**紧急：** {wo['urgency']}")
        a3.markdown(f"**需人工：** {'是' if wo['need_manual'] else '否'}")
        st.markdown(f"**摘要：** {wo['summary']}")
        st.markdown(f"**知识库匹配：** {wo['matched_kb']}")
        st.markdown(f"**初步建议：**\n{wo['suggestion']}")

    # 处理操作
    st.divider()
    st.subheader("🛠️ 处理工单")
    n1, n2 = st.columns([1, 2])
    with n1:
        new_status = st.selectbox(
            "修改状态",
            db.VALID_STATUSES,
            index=db.VALID_STATUSES.index(wo["status"]) if wo["status"] in db.VALID_STATUSES else 0,
        )
    with n2:
        new_result = st.text_area("填写处理结果 / 备注", value=wo["result"], height=100)

    if st.button("💾 保存修改", type="primary"):
        db.update_status(wo["id"], new_status, new_result.strip())
        st.success("已保存。")
        st.rerun()


def page_stats():
    """页面 3：统计看板。"""
    st.header("📊 统计看板")
    s = db.stats()

    m1, m2, m3 = st.columns(3)
    m1.metric("工单总数", s["total"])
    pending = s["by_status"].get(db.STATUS_PENDING, 0)
    processing = s["by_status"].get(db.STATUS_PROCESSING, 0)
    done = s["by_status"].get(db.STATUS_DONE, 0)
    m2.metric("待处理", pending)
    m3.metric("处理中", processing)
    st.metric("已完成", done)

    import pandas as pd
    st.subheader("按故障类别统计")
    if s["by_category"]:
        df_c = pd.DataFrame(
            [{"类别": k, "数量": v} for k, v in sorted(s["by_category"].items(), key=lambda x: -x[1])]
        )
        st.bar_chart(df_c.set_index("类别"))
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.info("暂无数据。")

    st.subheader("按状态统计")
    if s["by_status"]:
        df_s = pd.DataFrame(
            [{"状态": k, "数量": v} for k, v in s["by_status"].items()]
        )
        st.dataframe(df_s, use_container_width=True, hide_index=True)

    st.subheader("按紧急程度统计")
    if s["by_urgency"]:
        df_u = pd.DataFrame(
            [{"紧急程度": k, "数量": v} for k, v in s["by_urgency"].items()]
        )
        st.dataframe(df_u, use_container_width=True, hide_index=True)


def page_kb():
    """页面 4：知识库浏览。"""
    st.header("📚 故障知识库")
    kb = get_all()
    st.caption(f"共 {len(kb)} 条常见故障及处理办法（AI 建议优先依据这里）。")
    for item in kb:
        with st.expander(f"#{item['id']} {item['name']}  〔{item['category']}〕"):
            st.markdown(f"**涉及设备：** { '、'.join(item['devices']) }")
            st.markdown(f"**典型症状：** {item['symptoms']}")
            st.markdown(f"**触发关键词：** { '、'.join(item['keywords']) }")
            st.markdown("**排查建议：**")
            st.code(item["suggestions"])


def main():
    st.title("🔧 实验室设备报修与 AI 智能工单系统")
    st.caption("本地运行 · SQLite 持久化 · AI 规则分析 + 知识库匹配")

    with st.sidebar:
        st.header("导航")
        page = st.radio(
            "选择功能页",
            ["📝 提交报修", "🗂️ 工单管理", "📊 统计看板", "📚 知识库"],
            index=0,
        )

    if page.startswith("📝"):
        page_submit()
    elif page.startswith("🗂️"):
        page_manage()
    elif page.startswith("📊"):
        page_stats()
    else:
        page_kb()


if __name__ == "__main__":
    main()
