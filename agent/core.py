import asyncio
import json
import logging
import os
from typing import Any, Dict, List

import cv2
from bs4 import BeautifulSoup
from PIL import Image

from agent.llm.config_manager import AgentsLLMConfigManager
from agent.llm.helper import create_multimodal_agent

logger = logging.getLogger(__name__)


class AnalysisAgent:
    def __init__(self):
        config_manager = AgentsLLMConfigManager.get_instance()
        agent_config = config_manager.get_agent_config()
        llm_config = agent_config.get("model_config_params", {}).copy()
        llm_config.update(agent_config.get("llm_config_params", {}))
        self.agent = create_multimodal_agent(
            name="step-verifier",
            system_message="You are a visual verification agent. Given a step description and a set of images (frames from a video), determine if the step is visible in any of the frames. Respond with 'Observed' or 'Deviation' and a brief note.",
            llm_config=llm_config,
        )

    def parse_planning_log(self, path: str) -> List[str]:
        with open(path, "r") as f:
            data = json.load(f)
        steps = []
        for entry in data.get("planner_agent", []):
            content = entry.get("content")
            if isinstance(content, dict) and "plan" in content:
                plan_lines = content["plan"].split("\n")
                for line in plan_lines:
                    step = line.strip()
                    if step and step[0].isdigit():
                        step = step[2:].strip()
                        steps.append(step)
                break
        return steps

    def parse_final_output(self, path: str):
        with open(path, "r") as f:
            soup = BeautifulSoup(f, "html.parser")
        outcome = None
        outcome_tag = soup.find("td", string="Outcome:")
        if outcome_tag:
            outcome = outcome_tag.find_next_sibling("td").text.strip()
        video_path = None
        for th in soup.find_all("th"):
            if "Proofs Video" in th.text:
                video_path = th.find_next_sibling("td").text.strip()
                break
        if not video_path:
            logger.error(
                f"Could not find 'Proofs Video' in {path}. Please check the HTML structure."
            )
            raise ValueError(
                f"Could not find 'Proofs Video' in {path}. Please check the HTML structure."
            )
        return outcome, video_path

    def extract_frames(self, video_path: str, interval_sec: int = 1):
        frames = []
        if not os.path.exists(video_path):
            print(f"Video not found: {video_path}")
            return frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps else 0
        frame_indices = [int(i * fps) for i in range(0, int(duration), interval_sec)]
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img)
                frames.append((idx / fps, pil_img))
        cap.release()
        return frames

    def pil_image_to_openai_image_message(self, img: Image.Image):
        return {"type": "image_url", "image_url": {"url": img}}

    async def is_blank_image(self, img: Image.Image) -> bool:
        prompt = (
            "Is this image blank (all white, all black, or empty)? Respond with 'Yes' if it is blank, otherwise 'No'. "
            "Do not explain, just answer 'Yes' or 'No'."
        )
        content = [
            {"type": "text", "text": prompt},
            self.pil_image_to_openai_image_message(img),
        ]
        try:
            success, reply = await asyncio.to_thread(
                self.agent.generate_oai_reply, [{"role": "user", "content": content}]
            )
            if not success:
                raise RuntimeError("Failed to get a reply from the multimodal agent.")
            reply_str = str(reply).strip().lower()
            return reply_str.startswith("yes")
        except Exception as e:
            logger.error(f"Error in is_blank_image: {e}", exc_info=True)
            return False

    async def filter_non_blank_unique_frames(self, frames: List[Any]):
        """Filter out blank and duplicate frames (by image bytes hash)."""
        non_blank_frames = []
        seen_hashes = set()
        for ts, img in frames:
            if not await self.is_blank_image(img):
                img_bytes = img.tobytes()
                img_hash = hash(img_bytes)
                if img_hash not in seen_hashes:
                    seen_hashes.add(img_hash)
                    non_blank_frames.append((ts, img))
        print(f"Non-blank frames: {len(non_blank_frames)}")
        return non_blank_frames

    async def verify_step_with_llm(self, step_desc: str, frames: List[Any]):
        # Uniformly sample up to 20 frames if more are available
        if len(frames) > 20:
            step = len(frames) / 20
            selected_indices = [int(i * step) for i in range(20)]
            selected_frames = [frames[i] for i in selected_indices]
        else:
            selected_frames = frames
        prompt = (
            f"Given the following step description, determine if the step is visible in any of the provided images.\n\n"
            f"Step: {step_desc}\n\n"
            f"For each image, check if the step is being performed or its result is visible. "
            f"Respond with 'Observed' if you see evidence, otherwise 'Deviation'. Provide a brief note explaining your reasoning."
        )
        images = [
            self.pil_image_to_openai_image_message(img) for _, img in selected_frames
        ]
        content = [{"type": "text", "text": prompt}] + images
        try:
            success, reply = await asyncio.to_thread(
                self.agent.generate_oai_reply, [{"role": "user", "content": content}]
            )
            if not success:
                raise RuntimeError("Failed to get a reply from the multimodal agent.")
            observed = "Observed" in str(reply)
            notes = str(reply)
        except Exception as e:
            logger.error(f"Error in verify_step_with_llm: {e}", exc_info=True)
            observed = False
            notes = f"Error: {e}"
        return observed, notes

    async def analyze(
        self, planning_log: str, final_output: str
    ) -> List[Dict[str, Any]]:
        try:
            steps = self.parse_planning_log(planning_log)
            outcome, video_path = self.parse_final_output(final_output)
            if not video_path:
                raise ValueError(f"No video path found in final output: {final_output}")
            frames = self.extract_frames(video_path)
            # Filter blank and duplicate frames ONCE, store at instance level
            self.filtered_frames = await self.filter_non_blank_unique_frames(frames)
            report = []
            num_frames = len(self.filtered_frames)
            num_steps = len(steps)
            window_size = 20
            if num_frames <= window_size or num_steps == 1:
                # Use all frames for every step if not enough frames or only one step
                for step in steps:
                    observed, notes = await self.verify_step_with_llm(
                        step, self.filtered_frames
                    )
                    result = "✅ Observed" if observed else "❌ Deviation"
                    report.append({"Step": step, "Result": result, "Notes": notes})
            else:
                # Sliding window logic
                stride = max(1, (num_frames - window_size) // max(1, num_steps - 1))
                for i, step in enumerate(steps):
                    start = i * stride
                    end = start + window_size
                    # Clamp window to the end if it would go out of bounds
                    if end > num_frames:
                        end = num_frames
                        start = max(0, end - window_size)
                    window_frames = self.filtered_frames[start:end]
                    observed, notes = await self.verify_step_with_llm(
                        step, window_frames
                    )
                    result = "✅ Observed" if observed else "❌ Deviation"
                    report.append({"Step": step, "Result": result, "Notes": notes})
            return report
        except Exception as e:
            logger.error(f"Error in AnalysisAgent.analyze: {e}", exc_info=True)
            return [{"error": str(e)}]
