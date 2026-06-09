"""科普标准题识别与答案渲染测试"""

from app.services.medical_business import is_factual_medical_question, render_answer


class TestFactualQuestionDetection:
    def test_diagnostic_criteria_question(self):
        msg = "确诊是通过空腹血糖、餐后2小时血糖还是糖化血红蛋白？具体数值是多少？"
        assert is_factual_medical_question(msg) is True

    def test_symptom_question_is_not_factual(self):
        assert is_factual_medical_question("我发烧三天了，还咳嗽") is False


class TestFactualAnswerRendering:
    def test_factual_render_skips_triage_template(self):
        data = {
            "conclusion": "三种指标均可用于诊断。",
            "reasoning": "空腹血糖≥7.0 mmol/L；餐后2小时或OGTT≥11.1 mmol/L；HbA1c≥6.5%。",
            "red_flags": ["胸痛"],
            "next_questions": ["你的血糖是多少？"],
            "care_advice": ["建议重复检测确认"],
        }
        answer = render_answer(
            "consultation",
            data,
            "内分泌科",
            "中风险",
            "确诊是通过空腹血糖还是糖化血红蛋白？具体数值是多少？",
        )
        assert "三种指标均可用于诊断" in answer
        assert "7.0" in answer
        assert "风险等级" not in answer
        assert "红旗信号" not in answer
        assert "建议补充追问" not in answer
        assert "内分泌科" in answer

    def test_case_consultation_keeps_full_template(self):
        data = {
            "conclusion": "建议尽快就诊。",
            "reasoning": "发热伴咳嗽需排除感染。",
            "red_flags": ["呼吸困难"],
            "care_advice": ["多喝水"],
        }
        answer = render_answer("consultation", data, "呼吸科", "中风险", "我发烧三天了")
        assert "风险等级" in answer
        assert "推荐预约挂号科室" in answer
        assert "需要及时线下就医或急诊的信号" in answer
