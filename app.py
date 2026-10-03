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
# 侧边栏：权重调整滑块
# ============================================
with st.sidebar:
    st.markdown("### ⚙️ 权重调整（±20%）")
    st.caption("调整后点击计算按钮生效，用于验证AHP标定敏感性")
    area_w = st.slider("面积权重", 0.12, 0.18, 0.15, 0.01)
    years_w = st.slider("年限权重", 0.08, 0.12, 0.10, 0.01)
    yield_w = st.slider("产量权重", 0.08, 0.12, 0.10, 0.01)
    specialty_w = st.slider("精品品种权重", 0.12, 0.18, 0.15, 0.01)
    performance_w = st.slider("履约记录权重", 0.12, 0.18, 0.15, 0.01)
    insurance_w = st.slider("保险权重", 0.08, 0.12, 0.10, 0.01)
    rating_w = st.slider("村集体评级权重", 0.08, 0.12, 0.10, 0.01)
    epay_w = st.slider("咖e付流水权重", 0.12, 0.18, 0.15, 0.01)

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
# 输入区（默认值为中性样本，对应D档）
# ============================================
st.markdown("### 📋 请输入经营主体信息")

col1, col2 = st.columns(2)

with col1:
    area = st.number_input("种植确权面积（亩）", min_value=1.0, max_value=100.0, value=15.0, step=0.5)
    years = st.number_input("种植年限（年）", min_value=1, max_value=30, value=3, step=1)
    specialty = st.selectbox("精品品种", ["已种植", "已备案改良+已参保", "有改良计划未参保", "无计划"], index=1)
    yield_amount = st.number_input("年产量（吨）", min_value=0.5, max_value=20.0, value=2.0, step=0.1)

with col2:
    coop = st.selectbox("合作社身份", ["是", "否"], index=1)
    performance = st.selectbox("历史交易履约记录", ["有记录且无逾期", "无记录", "有逾期"], index=1)
    insurance = st.selectbox("保险参保情况", ["已参保", "未参保"], index=1)
    village_rating = st.selectbox("村集体信用评级", ["A", "B", "C", "D"], index=1)
    e_pay_activity = st.selectbox("咖e付流水活跃度", ["近12个月稳定且核验", "有流水未核验", "无流水"], index=2)

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

    # ---------- 校验提示 ----------
    if result["validation_warning"]:
        st.warning(f"⚠️ {result['validation_warning']}")

    # ---------- 结果卡片 ----------
    st.markdown("### 📊 评分结果")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("信用评分", f"{result['score']} 分")
    col_b.metric("风险等级", f"{result['grade']} 档")
    col_c.metric("首期建议授信", result["credit_range"])
    col_d.metric("建议利率", result["rate"])

    if result["grade"] in ["A", "B", "C"]:
        st.info(f"ℹ️ {result['advice']}（提额后区间：{result['max_range']}）")
    else:
        st.warning(f"⚠️ {result['advice']}")

    st.caption("📌 演示提示：可调整上方输入项后点击“计算信用评分”，查看不同档位的评分结果。")

    if result["grade"] == "A":
        st.balloons()

    st.markdown("---")

    # ---------- 雷达图 + 明细表 ----------
    st.markdown("### 📈 各维度得分明细")

    indicator_keys = list(INDICATOR_NAMES.keys())

    detail_rows = []
    for k in indicator_keys:
        if k == "coop":
            # 合作社身份：加分项，满分显示为0.005（对应+5分）
            score_val = result["detail"][k]
            full_val = 0.005
            rate = (score_val / full_val * 100) if full_val > 0 else 0.0
        else:
            score_val = result["detail"][k]
            full_val = WEIGHTS[k]
            rate = (score_val / full_val * 100) if full_val > 0 else 0.0
        detail_rows.append({
            "指标": INDICATOR_NAMES[k],
            "加权得分": round(score_val, 3),
            "满分": full_val,
            "得分率": round(rate, 1),
            "折算得分（×1000）": int(round(score_val * 1000)),
        })

    detail_df = pd.DataFrame(detail_rows)

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

    # ---------- 导出按钮 ----------
    st.download_button(
        label="📥 导出评分结果（CSV）",
        data=detail_df.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"云咖智信评分结果_{result['score']}分.csv",
        mime="text/csv",
    )

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

    # ---------- 免责声明 ----------
    st.caption(
        "本工具为竞赛演示版本，评分规则参考保山整村授信公开案例标定，"
        "当前采用模拟样本完成调试，不作为实际风控审批依据。"
        "本结果不构成授信决策，如有异议可申请人工复核。"
    )
