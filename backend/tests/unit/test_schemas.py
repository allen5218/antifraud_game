from app.schemas import (
    FraudTypeResult,
    PretestAnswer,
    PretestSubmitRequest,
    PretestSubmitResponse,
)


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

