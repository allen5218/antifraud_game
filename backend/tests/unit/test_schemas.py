from app.schemas import (
    AnswerResponse,
    AnswerResult,
    FraudTypeResult,
    GameOption,
    GameOverResult,
    GameResponse,
    GameStartRequest,
    MascotPopup,
    PretestAnswer,
    PretestSubmitRequest,
    PretestSubmitResponse,
    WeaknessDetail,
)


def test_game_option():
    opt = GameOption(key="A", text="選項 A")
    assert opt.key == "A"
    assert opt.text == "選項 A"


def test_game_response_scenario():
    resp = GameResponse(
        question_type="scenario",
        narrative="你在社群媒體上看到一則投資廣告...",
        question="你會怎麼做？",
        options=[
            GameOption(key="A", text="加入免費群看看"),
            GameOption(key="B", text="忽略廣告"),
            GameOption(key="C", text="檢查該公司是否合法"),
        ],
        correct_option="B",
        explanation="這是典型的投資詐騙手法",
        weakness_tag="greed",
        difficulty=1,
    )
    assert resp.question_type == "scenario"
    assert len(resp.options) == 3
    assert resp.weakness_tag == "greed"


def test_game_response_trap_null_weakness():
    resp = GameResponse(
        question_type="trap",
        narrative="你的銀行理專推薦一個定存方案...",
        question="這是詐騙嗎？",
        options=[
            GameOption(key="A", text="是詐騙"),
            GameOption(key="B", text="不是詐騙"),
        ],
        correct_option="B",
        explanation="這是合法的銀行服務",
        weakness_tag=None,
        difficulty=1,
    )
    assert resp.weakness_tag is None
    assert resp.question_type == "trap"


def test_pretest_submit_request():
    req = PretestSubmitRequest(
        answers=[
            PretestAnswer(question_id="abc123", selected_option="A"),
            PretestAnswer(question_id="def456", selected_option="B"),
        ]
    )
    assert len(req.answers) == 2


def test_pretest_submit_response():
    resp = PretestSubmitResponse(
        results_by_type={
            "investment": FraudTypeResult(correct=1, total=3),
            "shopping": FraudTypeResult(correct=3, total=3),
        },
        weakest_type="investment",
        ready_for_game=True,
    )
    assert resp.weakest_type == "investment"
    assert resp.results_by_type["investment"].correct == 1


def test_game_start_request_default():
    req = GameStartRequest()
    assert req.fraud_type is None


def test_game_start_request_with_type():
    req = GameStartRequest(fraud_type="investment")
    assert req.fraud_type == "investment"


def test_answer_response_with_mascot():
    resp = AnswerResponse(
        answer_result=AnswerResult(
            is_correct=True,
            correct_option="A",
            explanation="正確！",
            score_earned=10,
            total_score=50,
        ),
        mascot_popup=MascotPopup(show=True, message="太棒了！連續答對 5 題！"),
        next_question=GameResponse(
            question_type="judgment",
            narrative="下一題...",
            question="判斷這個情境",
            options=[GameOption(key="A", text="是"), GameOption(key="B", text="否")],
            correct_option="A",
            explanation="解說",
            weakness_tag="authority",
            difficulty=2,
        ),
        game_over=None,
    )
    assert resp.mascot_popup is not None
    assert resp.mascot_popup.show is True
    assert resp.next_question is not None
    assert resp.game_over is None


def test_game_over_result():
    result = GameOverResult(
        total_score=280,
        correct_rate=0.85,
        grade="A",
        weakness_analysis=[
            WeaknessDetail(
                tag="greed",
                count=2,
                label="貪念誘惑",
                suggestion="注意「保證獲利」等話術",
            ),
        ],
        strength_tags=["authority", "time_pressure"],
    )
    assert result.grade == "A"
    assert len(result.weakness_analysis) == 1
    assert result.weakness_analysis[0].tag == "greed"


def test_answer_response_game_over():
    resp = AnswerResponse(
        answer_result=AnswerResult(
            is_correct=False,
            correct_option="B",
            explanation="這其實是詐騙",
            score_earned=0,
            total_score=200,
        ),
        mascot_popup=None,
        next_question=None,
        game_over=GameOverResult(
            total_score=200,
            correct_rate=0.6,
            grade="B",
            weakness_analysis=[],
            strength_tags=[],
        ),
    )
    assert resp.game_over is not None
    assert resp.next_question is None
    assert resp.game_over.grade == "B"
