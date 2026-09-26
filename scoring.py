from config import WEIGHTS, VILLAGE_RATING_MAP, GRADE_THRESHOLDS, GRADE_OUTPUT


# ---------- 各指标归一化函数 ----------

def normalize_area(area: float) -> float:
    """种植面积：30亩以上满分，15-30亩中档，15亩以下低档"""
    if area >= 30:
        return 1.0
    elif area >= 15:
        return 0.7
    else:
        return 0.4


def normalize_years(years: int) -> float:
    """种植年限：5年以上满分，3-5年中档，3年以下低档"""
    if years >= 5:
        return 1.0
    elif years >= 3:
        return 0.7
    else:
        return 0.4


def normalize_specialty(specialty: str) -> float:
    """精品品种：已种植=满分；已备案改良+买保险=中档；无计划=低档"""
    if specialty == "已种植":
        return 1.0
    elif specialty == "已备案改良+已参保":
        return 0.6
    else:
        return 0.2


def normalize_yield(yield_amount: float) -> float:
    """年产量：4吨以上满分，2-4吨中档，2吨以下低档"""
    if yield_amount >= 4:
        return 1.0
    elif yield_amount >= 2:
        return 0.7
    else:
        return 0.4


def normalize_coop(coop: str) -> float:
    """合作社身份：加分项，是=满分，否=部分分值"""
    return 1.0 if coop == "是" else 0.5


def normalize_performance(performance: str) -> float:
    """履约记录：有记录且无逾期=满分；无记录=中档；有逾期=低档"""
    if performance == "有记录且无逾期":
        return 1.0
    elif performance == "无记录":
        return 0.6
    else:
        return 0.2


def normalize_insurance(insurance: str) -> float:
    """保险参保：已参保=1.0，未参保=0.0"""
    return 1.0 if insurance == "已参保" else 0.0


def normalize_epay(e_pay_activity: str) -> float:
    """咖e付流水活跃度：近12个月稳定且核验=1.0，无流水=0.0"""
    return 1.0 if e_pay_activity == "近12个月稳定且核验" else 0.0


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

    weighted = {k: normalized[k] * WEIGHTS[k] for k in WEIGHTS}
    raw_score = sum(weighted.values())
    final_score = int(raw_score * 1000)

    grade = "D"
    for g, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if final_score >= threshold:
            grade = g
            break

    output = GRADE_OUTPUT[grade]

    return {
        "score": final_score,
        "grade": grade,
        "credit_range": output["range"],
        "max_range": output["max_range"],
        "rate": output["rate"],
        "advice": output["advice"],
        "detail": weighted,
        "normalized": normalized,
    }
