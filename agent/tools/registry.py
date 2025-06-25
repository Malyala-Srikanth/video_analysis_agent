from collections import defaultdict
from collections.abc import Callable
from typing import Any

tool_registry = defaultdict(list)

def tool(agent_names: list[str], description: str, name: str | None = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        for agent_name in agent_names:
            tool_registry[agent_name].append({
                "name": (name if name else func.__name__),
                "func": func,
                "description": description,
            })
        return func
    return decorator 