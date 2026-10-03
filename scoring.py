from config import WEIGHTS, VILLAGE_RATING_MAP, GRADE_THRESHOLDS, GRADE_OUTPUT


# ---------- 各指标归一化函数（五档线性插值） ----------

def normalize_area(area: float) -> float:
    """种植面积：30亩以上=100%，25-30亩=80%，15-25亩=60%，5-15亩=30%，5亩以下=10%"""
    if area >= 30:
        return 1.0
    elif area >= 25:
        return 0.8
    elif area >= 15:
        return 0.6
    elif area >= 5:
        return 0.3
    else:
        return 0.1


def normalize_years(years: int) -> float:
    """种植年限：8年以上=100%，5-8年=80%，3-5年=60%，2-3年=30%，2年以下=10%"""
    if years >= 8:
        return 1.0
    elif years >= 5:
        return 0.8
    elif years >= 3:
        return 0.6
    elif years >= 2:
        return 0.3
    else:
        return 0.1


def normalize_specialty(specialty: str) -> float:
    """精品品种：已种植=100%；已备案改良+参保=60%；有改良计划未参保=40%；无计划=10%"""
    if specialty == "已种植":
        return 1.0
    elif specialty == "已备案改良+已参保":
        return 0.6
    elif specialty == "有改良计划未参保":
        return 0.4
    else:
        return 0.1


def normalize_yield(yield_amount: float) -> float:
    """年产量：4吨以上=100%，3-4吨=80%，2-3吨=60%，1-2吨=30%，1吨以下=10%"""
    if yield_amount >= 4:
        return 1.0
    elif yield_amount >= 3:
        return 0.8
    elif yield_amount >= 2:
        return 0.6
    elif yield_amount >= 1:
        return 0.3
    else:
        return 0.1


def normalize_coop(coop: str) -> float:
    """合作社身份：加分项，不占权重"""
    return 1.0 if coop == "是" else 0.0


def normalize_performance(performance: str) -> float:
    """履约记录：有记录且无逾期=100%；无记录=50%（配合3个月观察期）；有逾期=0"""
    if performance == "有记录且无逾期":
        return 1.0
    elif performance == "无记录":
        return 0.5
    else:
        return 0.0


def normalize_insurance(insurance: str) -> float:
    """保险参保：已参保=100%，未参保=0"""
    return 1.0 if insurance == "已参保" else 0.0


def normalize_epay(e_pay_activity: str) -> float:
    """咖e付流水活跃度：近12个月稳定且核验=100%，有流水未核验=50%，无流水=0"""
    if e_pay_activity == "近12个月稳定且核验":
        return 1.0
    elif e_pay_activity == "有流水未核验":
        return 0.5
    else:
        return 0.0


# ---------- 核心评分函数 ----------

def calc_score(inputs: dict) -> dict:
    """
    输入：包含9个指标的字典
    输出：信用分、等级、建议授信区间、建议利率、各维度明细
    """

    normalized = {
        "area": normalize_area(inputs["area"]),
        "years": normalize_years(inputs["years"]),
        "specialty": normalize_specialty(inputs["specialty"]),
        "yield_amount": normalize_yield(inputs["yield_amount"]),
        "coop": normalize_coop(inputs["coop"]),
        "performance": normalize_performance(inputs["performance"]),
        "insurance": normalize_insurance(inputs["insurance"]),
        "village_rating": VILLAGE_RATING_MAP[inputs["village_rating"]],
        "e_pay_activity": normalize_epay(inputs["e_pay_activity"]),
    }

    # 加权得分（合作社身份权重为0，单独作为加分项处理）
    weighted = {}
    for k in WEIGHTS:
        if k == "coop":
            weighted[k] = 0.005 if inputs["coop"] == "是" else 0.0
        else:
            weighted[k] = round(normalized[k] * WEIGHTS[k], 4)

    raw_score = round(sum(weighted.values()), 4)
    final_score = int(raw_score * 1000)

    # ★ 总分上限1000分
    final_score = min(final_score, 1000)

    # 风险等级判定
    grade = "D"
    for g, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if final_score >= threshold:
            grade = g
            break

    output = GRADE_OUTPUT[grade]

    # 亩均产量合理性校验
    validation_warning = ""
    if inputs["area"] >= 10 and inputs["yield_amount"] <= 1:
        validation_warning = "亩均产量异常（面积≥10亩且年产量≤1吨），建议核对数据"

    return {
        "score": final_score,
        "grade": grade,
        "credit_range": output["range"],
        "max_range": output["max_range"],
        "rate": output["rate"],
        "advice": output["advice"],
        "detail": weighted,
        "normalized": normalized,
        "validation_warning": validation_warning,
    }
