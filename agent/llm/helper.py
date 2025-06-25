import copy
import json
import tempfile
from typing import Any, Dict, Optional
import autogen
from autogen import ConversableAgent
from autogen.agentchat.contrib.img_utils import gpt4v_formatter, message_formatter_pil_to_b64

DEFAULT_LMM_SYS_MSG = "You are a helpful AI assistant."
DEFAULT_MODEL = "gpt-4o"

class MultimodalConversableAgent(ConversableAgent):
    DEFAULT_CONFIG = {
        "model": DEFAULT_MODEL,
    }

    def __init__(
        self,
        name: str,
        system_message: Optional[str] = DEFAULT_LMM_SYS_MSG,
        is_termination_msg: str = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(name, system_message, is_termination_msg=is_termination_msg, *args, **kwargs)
        self.update_system_message(system_message)
        self._is_termination_msg = is_termination_msg if is_termination_msg is not None else (lambda x: x.get("content") == "TERMINATE")
        self.replace_reply_func(
            ConversableAgent.generate_oai_reply,
            MultimodalConversableAgent.generate_oai_reply,
        )
        self.replace_reply_func(
            ConversableAgent.a_generate_oai_reply,
            MultimodalConversableAgent.a_generate_oai_reply,
        )

    def update_system_message(self, system_message: str) -> None:
        self._oai_system_message[0]["content"] = system_message
        self._oai_system_message[0]["role"] = "system"

    def generate_oai_reply(
        self,
        messages: Optional[list] = None,
        sender: Optional[ConversableAgent] = None,
        config: Optional[Any] = None,
    ):
        client = self.client if config is None else config
        if client is None:
            return False, None
        if messages is None:
            messages = self._oai_messages[sender]
        messages_with_b64_img = message_formatter_pil_to_b64(self._oai_system_message + messages)
        extracted_response = self._generate_oai_reply_from_client(llm_client=client, messages=messages_with_b64_img, cache=self.client_cache)
        return (False, None) if extracted_response is None else (True, extracted_response)

    async def a_generate_oai_reply(
        self,
        messages: Optional[list] = None,
        sender: Optional[ConversableAgent] = None,
        config: Optional[Any] = None,
    ):
        import asyncio
        import functools
        return await asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(
                self.generate_oai_reply,
                messages=messages,
                sender=sender,
                config=config,
            ),
        )

def convert_model_config_to_autogen_format(model_config: dict) -> list:
    env_var = [model_config]
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp:
        json.dump(env_var, temp)
        temp_file_path = temp.name
    return autogen.config_list_from_json(env_or_file=temp_file_path)

def create_multimodal_agent(
    name: str,
    system_message: str = "You are a multimodal conversable agent.",
    llm_config: Optional[Dict[str, Any]] = None,
) -> MultimodalConversableAgent:
    return MultimodalConversableAgent(name=name, system_message=system_message, llm_config=llm_config) 