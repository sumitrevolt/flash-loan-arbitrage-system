from typing import List, Any, Optional, Dict, TypeVar

T = TypeVar('T')

class Agent:
    def __init__(
        self,
        name_or_id: Optional[str] = None,
        human_input_mode: Optional[str] = None,
        system_message: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None: ...

class AssistantAgent(Agent):
    def __init__(
        self,
        name_or_id: Optional[str] = None,
        human_input_mode: Optional[str] = None,
        system_message: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None: ...

class UserProxyAgent(Agent):
    def __init__(
        self,
        name_or_id: Optional[str] = None,
        human_input_mode: Optional[str] = None,
        system_message: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None: ...
    
    def initiate_chat(
        self,
        assistant: AssistantAgent,
        message: Optional[str] = None,
        **kwargs: Any
    ) -> Any: ...

class GroupChat:
    def __init(
        self,
        agents: List[Agent],
        messages: List[Any],
        max_round: int
    ) -> None: ...

class GroupChatManager:
    def __init(
        self,
        group_chat: GroupChat,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None: ...

    def initiate_chat(self, *args: Any, **kwargs: Any) -> Any: ...
