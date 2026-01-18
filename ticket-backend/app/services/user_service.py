from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentContext:
    id: str
    name: str
    status: str  # "active", "busy", "offline"
    skills: List[str]
    current_load: int  # Number of active tickets

class UserService:
    def __init__(self):
        # Hardcoded agents matching frontend users.ts
        self._agents = [
            AgentContext(
                id="user-1",
                name="IT Person",
                status="active",
                skills=["hardware", "networking", "support", "windows"],
                current_load=3
            ),
            AgentContext(
                id="user-2",
                name="Frontend Developer",
                status="busy",
                skills=["javascript", "react", "svelte", "css"],
                current_load=5
            ),
            AgentContext(
                id="user-3",
                name="Backend Developer",
                status="active",
                skills=["python", "api", "database", "docker"],
                current_load=2
            ),
            AgentContext(
                id="user-4",
                name="Database Developer",
                status="away",
                skills=["sql", "postgres", "optimization"],
                current_load=0
            ),
            AgentContext(
                id="user-5",
                name="UI Designer",
                status="active",
                skills=["figma", "design", "css", "ux"],
                current_load=1
            ),
            AgentContext(
                id="user-6",
                name="AI Engineer",
                status="active",
                skills=["python", "llm", "pytorch", "rag"],
                current_load=2
            ),
            AgentContext(
                id="user-7",
                name="Network Engineer",
                status="offline",
                skills=["cisco", "firewall", "vpn", "routing"],
                current_load=0
            ),
        ]

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of agents with their context for AI processing.
        Returns a list of dictionaries to be JSON-serializable.
        """
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "status": agent.status,
                "skills": agent.skills,
                "current_load": agent.current_load
            }
            for agent in self._agents
        ]

    def get_agent(self, agent_id: str) -> Optional[AgentContext]:
        for agent in self._agents:
            if agent.id == agent_id:
                return agent
        return None

# Global instance
user_service = UserService()
