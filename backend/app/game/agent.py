import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai_skills import SkillsToolset

from app.models import GameSession
from app.schemas import GameResponse

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../skills")


@dataclass
class GameDeps:
    session: GameSession
    pretest_weakness: str


def create_game_agent() -> Agent[GameDeps, GameResponse]:
    skills_toolset = SkillsToolset(
        directories=[SKILLS_DIR],
        exclude_tools=["run_skill_script"],
    )

    agent: Agent[GameDeps, GameResponse] = Agent(
        "google:gemini-3.5-flash",
        deps_type=GameDeps,
        output_type=GameResponse,
        toolsets=[skills_toolset],
        end_strategy="early",
        defer_model_check=True,
    )

    @agent.instructions
    async def game_instructions(ctx: RunContext[GameDeps]) -> str:
        session = ctx.deps.session
        return f"""你是反詐騙訓練遊戲的主持人。

當前遊戲狀態：
- 詐騙類型：{session.fraud_type}
- 目前第 {session.current_step + 1} 題
- 已答對：{session.total_correct} 題
- 已答錯：{session.total_wrong} 題
- 剩餘題數：{session.max_steps - session.current_step}
- 玩家前測弱點：{ctx.deps.pretest_weakness}

規則：
1. 你必須回傳 GameResponse 格式
2. 根據玩家上一題的表現調整難度
3. 選項要有 3-4 個，且不能有明顯荒謬的選項
4. 每 3-4 題插入一題「非詐騙」陷阱題（question_type 為 "trap"）
5. 使用已載入的 Skill 指令作為題目生成的依據
6. weakness_tag 從 time_pressure/authority/greed/social_proof/trust_building 中選取
7. 陷阱題的 weakness_tag 設為 null"""

    @agent.instructions
    async def skill_instructions(ctx: RunContext[GameDeps]) -> str:
        result = await skills_toolset.get_instructions(ctx)
        return result or ""

    return agent
