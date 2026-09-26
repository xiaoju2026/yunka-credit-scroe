import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scoring import calc_score
from config import INDICATOR_NAMES, WEIGHTS, MATERIALS

# ============================================
# 页面基础配置
# ============================================
st.set_page_config(
    page_title="云咖智信 · 产业信用评分工具",
    page_icon="☕",
    layout="wide",
)

# ============================================
# 标题区
# ============================================
st.title("☕ 云咖智信 · 保山小粒咖啡产业信用评分工具")
st.caption(
    "本工具为竞赛演示版，作为银行风控辅助参考，"
    "不替代工行生产风控审批系统，最终审批权限归属银行风控部门。"
)
st.markdown("---")

# ============================================
# 输入区
# ============================================
st.markdown("### 📋 请输入经营主体信息")

col1, col2 = st.columns(2)

with col1:
    area = st.number_input("种植确权面积（亩）", min_value=1.0, max_value=100.0, value=30.0, step=0.5)
    years = st.number_input("种植年限（年）", min_value=1, max_value=30, value=5, step=1)
    specialty = st.selectbox("精品品种", ["已种植", "已备案改良+已参保", "无计划"])
    yield_amount = st.number_input("年产量（吨）", min_value=0.5, max_value=20.0, value=4.0, step=0.1)

with col2:
    coop = st.selectbox("合作社身份", ["是", "否"])
    performance = st.selectbox("历史交易履约记录", ["有记录且无逾期", "无记录", "有逾期"])
    insurance = st.selectbox("保险参保情况", ["已参保", "未参保"])
    village_rating = st.selectbox("村集体信用评级", ["A", "B", "C", "D"])
    e_pay_activity = st.selectbox("咖e付流水活跃度", ["近12个月稳定且核验", "无流水"])

st.markdown("---")

# ============================================
# 计算与结果展示
# ============================================
if st.button("🔮 计算信用评分", type="primary", use_container_width=True):

    inputs = {
        "area": area,
        "years": years,
        "specialty": specialty,
        "yield_amount": yield_amount,
        "coop": coop,
        "performance": performance,
        "insurance": insurance,
        "village_rating": village_rating,
        "e_pay_activity": e_pay_activity,
    }

    result = calc_score(inputs)

    # ---------- 结果卡片 ----------
    st.markdown("### 📊 评分结果")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("信用评分", f"{result['score']} 分")
    col_b.metric("风险等级", f"{result['grade']} 档")
    col_c.metric("首期建议授信", result["credit_range"])
    col_d.metric("建议利率", result["rate"])

    if result["grade"] in ["A", "B"]:
        st.success(f"✅ {result['advice']}（提额后区间：{result['max_range']}）")
    elif result["grade"] == "D":
        st.warning(f"⚠️ {result['advice']}")
    else:
        st.info(f"ℹ️ {result['advice']}（提额后区间：{result['max_range']}）")

    if result["grade"] == "A":
        st.balloons()

    st.markdown("---")

    # ---------- 雷达图 + 明细表 ----------
    st.markdown("### 📈 各维度得分明细")

    indicator_keys = list(INDICATOR_NAMES.keys())
    weight_values = list(WEIGHTS.values())

    detail_df = pd.DataFrame({
        "指标": [INDICATOR_NAMES[k] for k in indicator_keys],
        "加权得分": [result["detail"][k] for k in indicator_keys],
        "满分": weight_values,
    })
    detail_df["得分率"] = (detail_df["加权得分"] / detail_df["满分"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=detail_df["得分率"].tolist(),
        theta=detail_df["指标"].tolist(),
        fill='toself',
        name='当前评分',
        line_color='#2E7D32',
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    detail_display = detail_df.copy()
    detail_display["得分率"] = detail_display["得分率"].astype(str) + "%"
    st.dataframe(detail_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ---------- 证明材料清单 ----------
    st.markdown("### 📎 证明材料清单（演示版）")

    with st.expander("点击查看需提交的证明材料"):
        mat_df = pd.DataFrame(MATERIALS)
        mat_df.columns = ["材料名称", "来源", "是否自动调取"]
        st.dataframe(mat_df, use_container_width=True, hide_index=True)

    st.markdown("### ✅ 审核状态（演示版）")
    st.info(
        "评分工具输出结果作为银行风控辅助参考。银行风控人员结合系统初筛评分与证明材料进行人工复核并最终审批。"
        "资金通过'咖e付'闭环发放，贷后持续监测交易流水。"
    )

    st.markdown("---")
    st.caption(
        "本工具为竞赛演示版本，评分规则参考保山整村授信公开案例标定，"
        "当前采用模拟样本完成调试，不作为实际风控审批依据。"
    )
