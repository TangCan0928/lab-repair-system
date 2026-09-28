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

# 侧边栏 / 导航栏美化样式（深蓝科技风）
NAV_CSS = """
<style>
/* 侧边栏背景：深蓝渐变 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b2239 0%, #123b5e 55%, #155e75 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* 侧边栏文字颜色 */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] .caption {
    color: #d7e7f3;
}

/* 导航链接基础样式 */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
section[data-testid="stSidebar"] a[data-testid="stPageLink"] {
    color: #cfe3f0;
    border-radius: 8px;
    padding: 0.45rem 0.65rem;
    margin-bottom: 2px;
    transition: all 0.2s ease;
}

/* 悬停效果 */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

/* 当前页高亮 */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"] {
    background: linear-gradient(90deg, #00b4d8, #48cae4);
    color: #06283d !important;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(0, 180, 216, 0.35);
}

/* 导航分组标题 */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] header,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] div[role="heading"] {
    color: #8fb7cd;
    letter-spacing: 1px;
    font-size: 0.8rem;
}

/* 滚动条配色 */
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}
section[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 6px;
}
</style>
"""


def inject_nav_css():
    """注入导航栏美化样式（需在 st.navigation 之后调用）。"""
    st.markdown(NAV_CSS, unsafe_allow_html=True)


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
    """页面 2：工单管理（列表 + 点击行选中查看详情 + 处理）。"""
    st.header("🗂️ 工单管理")
    st.caption("💡 在下方表格中**点击任意一行**，即可选中并查看该工单的详细内容。")

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

    # 列表用 DataFrame 展示（点击行可选中）
    show_cols = ["ticket_no", "reporter", "device_name", "location",
                 "category", "urgency", "status", "created_at"]
    import pandas as pd
    df = pd.DataFrame(rows)[show_cols]
    df.columns = ["工单号", "报修人", "设备", "位置", "类别", "紧急", "状态", "提交时间"]

    # 筛选条件变化时自动重置选中状态（key 随条件变化）
    table_key = f"wo_table_{f_category}_{f_status}_{f_keyword.strip() or '_'}"
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=320,
        on_select="rerun",
        selection_mode="single-row",
        key=table_key,
    )

    # 读取用户点击选中的行（位置索引 → 工单 id）
    selected_wo = None
    if event and event.selection.rows:
        pos = event.selection.rows[0]
        if 0 <= pos < len(rows):
            selected_wo = db.get_workorder(rows[pos]["id"])

    if selected_wo is None:
        st.info("👆 请在上方表格中点击一条工单，下方会显示它的详细内容。")
        return

    wo = selected_wo

    # 详情展示（卡片式）
    st.divider()
    st.subheader(f"📋 工单详情 — {wo['ticket_no']}")
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
    # 现代分组导航（官方组件，自动带图标、当前页高亮）
    pages = st.navigation(
        {
            "📋 工单业务": [
                st.Page(page_submit, title="提交报修", icon="📝", default=True),
                st.Page(page_manage, title="工单管理", icon="🗂️"),
            ],
            "📊 数据与知识": [
                st.Page(page_stats, title="统计看板", icon="📊"),
                st.Page(page_kb, title="故障知识库", icon="📚"),
            ],
        }
    )

    # 美化样式（必须在 st.navigation 之后注入）
    inject_nav_css()

    # 全局页头（所有页面统一显示）
    st.title("🔧 实验室设备报修与 AI 智能工单系统")
    st.caption("本地运行 · SQLite 持久化 · AI 规则分析 + 知识库匹配")

    # 侧边栏底部：小组信息卡片
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<div style="padding:0.7rem 0.8rem;background:rgba(255,255,255,0.08);'
            'border-radius:10px;border:1px solid rgba(255,255,255,0.16);">'
            '<div style="font-weight:700;color:#ffffff;font-size:0.9rem;">👥 小组信息</div>'
            '<div style="color:#cde1ef;font-size:0.8rem;margin-top:5px;">'
            '唐灿（组长）· 谢曼婕</div>'
            '<div style="color:#8fb7cd;font-size:0.75rem;margin-top:4px;">'
            'v1.0 · Streamlit + SQLite · 本地运行</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    pages.run()


if __name__ == "__main__":
    main()
