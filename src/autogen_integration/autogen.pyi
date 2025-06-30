from typing import Any, Dict, List

class Agent:
    name: str
    def __init__(self, name: str = "") -> None: ...
    def send(self, message: Dict[str, Any], recipient: 'Agent', request_reply: bool) -> None: ...
    # Add other commonly used Agent methods
    def receive(self, message: Dict[str, Any], sender: 'Agent') -> None: ...
    def generate_reply(self, messages: List[Dict[str, Any]], sender: 'Agent') -> Dict[str, Any]: ...
    # Add other Agent methods as needed

class GroupChat:
    agents: List[Agent]
    messages: List[Dict[str, Any]]
    max_rounds: int
    def __init__(self) -> None: ...

class GroupChatManager:
    group_chat: GroupChat
    def __init__(self) -> None: ...