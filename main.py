import argparse
import asyncio
from agent.core import AnalysisAgent


def main():
    parser = argparse.ArgumentParser(description="Run the AnalysisAgent on test execution artifacts.")
    parser.add_argument("--planning_log", help="Path to the planning log JSON file (agent_inner_thoughts.json)")
    parser.add_argument("--final_output", help="Path to the final output HTML file (test.feature_result.html)")
    args = parser.parse_args()

    async def run():
        agent = AnalysisAgent()
        report = await agent.analyze(args.planning_log, args.final_output)
        print("Deviation Report:")
        for step in report:
            print(step)

    asyncio.run(run())

if __name__ == "__main__":
    main()