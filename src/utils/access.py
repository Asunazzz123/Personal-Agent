import json
from pathlib import Path
from decouple import config
from src.core.schema import SafetyStatus
from src.utils.constant import TOOL_JSON_PATH
from src.utils.logger import setup_access_logger

access_logger = setup_access_logger()



def access_validator(fun) -> callable:
    """
    工具安全校验装饰器
    """
    def wrapper(*args, **kwargs) -> None:
        tool_name = fun.__name__
        access = Access(tool_name)
        safety_status = access.load_access_policy()
        if safety_status.access_policy == "Denied":
            access_logger.warning(f"[Access Control]{tool_name} Access to {tool_name} is denied by safety policy.")
            return safety_status
        elif safety_status.access_policy == "Onced":
            access_logger.warning(f"[Access Control]{tool_name} Access to {tool_name} is denied due to one-time use policy.")
            return safety_status
        elif safety_status.access_policy == "Once":
            access_logger.info(f"[Access Control]{tool_name} Access to {tool_name} is granted for one-time use.")
            result = fun(*args, **kwargs)
            with open(TOOL_JSON_PATH, "r+") as f:
                tool_data = json.load(f)
                for grp in tool_data:
                    for tool in grp.get("tools", []):
                        if tool.get("tool_name") == tool_name:
                            tool["policy"] = "Onced"
                            break
                f.seek(0)
                json.dump(tool_data, f, indent=4, ensure_ascii=False)
                f.truncate()
            return result
        else:
            access_logger.info(f"[Access Control]{tool_name} Access to {tool_name} is granted by safety policy.")
            return fun(*args, **kwargs)


def load_access_policy(tool_name: str) -> SafetyStatus:
    """
    读取单个工具的访问策略
    """
    return Access(tool_name).load_access_policy()
    


class Access:
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.group_name = Path(__file__).stem
    
    def _logic_check(tool_policy:str, group_policy:str) -> str:
        """
        策略匹配: 工具组的安全策略强于单一工具的安全策略
        """
        def _map(policy:str) -> int:
            if policy == "Denied":
                return -1
            elif policy == "Onced":
                return 0
            elif policy == "Once":
                return 1
            elif policy == "Whitelist":
                return 2
            else:
                return -2
        if _map(tool_policy) <= _map(group_policy):
            return tool_policy
        return group_policy

    def _find_group(self, tool_data: list) -> dict | None:
        for grp in tool_data:
            group_name = grp.get("group_name", "")
            if group_name.lower() == str(self.tool_name).lower():
                return grp
            for tool in grp.get("tools", []):
                if tool.get("tool_name") == self.tool_name:
                    return grp
        return None
    
    def load_tool_list(self) -> list:
        with open(TOOL_JSON_PATH, "r") as f:
            tool_data = json.load(f)
        grp = self._find_group(tool_data)
        if grp:
            return [tool["tool_name"] for tool in grp.get("tools", [])]
        return []
    
    def load_access_policy(self) -> SafetyStatus:
        with open(TOOL_JSON_PATH, "r") as f:
            tool_data = json.load(f)
        grp = self._find_group(tool_data)
        if not grp:
            return SafetyStatus(tool_name=self.tool_name, access_policy="Denied")

        group_name = grp.get("group_name", "")
        tool_policy = grp.get("policy", "Denied")
        for tool in grp.get("tools", []):
            if tool.get("tool_name") == self.tool_name:
                tool_policy = tool.get("policy", tool_policy)
                break

        group_policy = config(group_name.upper() + "_ACCESS_POLICY", default=grp.get("policy", "Denied"))
        policy = self._logic_check(tool_policy, group_policy)
        return SafetyStatus(tool_name=self.tool_name, access_policy=policy)
