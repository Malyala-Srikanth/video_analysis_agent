import traceback
from typing import Annotated, List, Dict
from analysis_agent.tool_registry import tool
from analysis_agent.agent import AnalysisAgent

@tool(
    agent_names=["planner_agent", "helper_agent", "analysis_agent"],
    name="analyze_test_deviation",
    description="Analyze test execution deviation by comparing planned steps with video evidence. Returns a deviation report. Arguments: planning_log (path to agent_inner_thoughts.json), final_output (path to test.feature_result.html).",
)
async def analyze_test_deviation(
    planning_log: Annotated[str, "Path to the planning log JSON file (agent_inner_thoughts.json)"],
    final_output: Annotated[str, "Path to the final output HTML file (test.feature_result.html)"],
) -> List[Dict]:
    """
    Analyze test execution deviation by comparing planned steps with video evidence.
    Returns a deviation report as a list of dicts.
    """
    try:
        analysis_agent = AnalysisAgent()
        report = await analysis_agent.analyze(planning_log, final_output)
        return report
    except Exception as e:
        traceback.print_exc()
        return [{"error": str(e)}] 