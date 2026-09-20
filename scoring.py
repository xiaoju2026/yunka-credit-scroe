from config import WEIGHTS, VILLAGE_RATING_MAP, GRADE_THRESHOLDS, GRADE_OUTPUT


# ---------- 各指标归一化函数 ----------

def normalize_area(area: float) -> float:
    """种植面积：10亩以上满分，5-10亩中档，5亩以下低档"""
    if area >= 10:
        return 1.0
    elif area >= 5:
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


def normalize_yield(yield_amount: float) -> float:
    """年产量：5吨以上满分，2-5吨中档，2吨以下低档"""
    if yield_amount >= 5:
        return 1.0
    elif yield_amount >= 2:
        return 0.7
    else:
        return 0.4


def normalize_bool(value: str, true_val: str = "是") -> float:
    """布尔型指标：是=1.0，否=0.0"""
    return 1.0 if value == true_val else 0.0


def normalize_performance(value: str) -> float:
    """履约记录：无逾期=1.0，有逾期=0.0"""
    return 1.0 if value == "无逾期" else 0.0


def normalize_insurance(value: str) -> float:
    """保险参保：已参保=1.0，未参保=0.0"""
    return 1.0 if value == "已参保" else 0.0


def normalize_default(value: str) -> float:
    """历史逾期：无=1.0，有=0.0"""
    return 1.0 if value == "无" else 0.0


# ---------- 核心评分函数 ----------

def calc_score(inputs: dict) -> dict:
    """
    输入：包含9个指标的字典
    输出：信用分、等级、建议授信区间、建议利率、各维度明细
    """

    # 第一步：把每个输入值归一化到 0~1
    normalized = {
        "area": normalize_area(inputs["area"]),
        "years": normalize_years(inputs["years"]),
        "specialty": normalize_bool(inputs["specialty"]),
        "yield_amount": normalize_yield(inputs["yield_amount"]),
        "coop": normalize_bool(inputs["coop"]),
        "performance": normalize_performance(inputs["performance"]),
        "insurance": normalize_insurance(inputs["insurance"]),
        "village_rating": VILLAGE_RATING_MAP[inputs["village_rating"]],
        "default_flag": normalize_default(inputs["default_flag"]),
    }

    # 第二步：乘以权重，得到每个维度的加权得分
    weighted = {k: normalized[k] * WEIGHTS[k] for k in WEIGHTS}

    # 第三步：求和，得到原始分（0~1之间）
    raw_score = sum(weighted.values())

    # 第四步：归一化到 0~1000 分
    final_score = int(raw_score * 1000)

    # 第五步：判定风险等级
    grade = "D"
    for g, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if final_score >= threshold:
            grade = g
            break

    # 第六步：获取对应建议
    output = GRADE_OUTPUT[grade]

    return {
        "score": final_score,
        "grade": grade,
        "credit_range": output["range"],
        "rate": output["rate"],
        "advice": output["advice"],
        "detail": weighted,
        "normalized": normalized,
    }