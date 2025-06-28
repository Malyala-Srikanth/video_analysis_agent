import argparse
import asyncio
import json
import os

from agent.core import AnalysisAgent


def main():
    parser = argparse.ArgumentParser(
        description="Run the AnalysisAgent on test execution artifacts."
    )
    parser.add_argument(
        "--planning_log",
        help="Path to the planning log JSON file (agent_inner_thoughts.json)",
    )
    parser.add_argument(
        "--final_output",
        help="Path to the final output HTML file (test.feature_result.html)",
    )
    args = parser.parse_args()

    async def run():
        agent = AnalysisAgent()
        report = await agent.analyze(args.planning_log, args.final_output)
        print("Deviation Report:")
        for step in report:
            print(step)
        # Save report as JSON in the same directory as the final_output file
        output_dir = os.path.dirname(args.final_output) if args.final_output else "."
        output_path = os.path.join(output_dir, "deviation_report.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    asyncio.run(run())


if __name__ == "__main__":
    main()
