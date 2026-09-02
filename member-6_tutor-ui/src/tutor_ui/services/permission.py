from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

class AutonomyLevel(IntEnum):
    DISABLED = 0
    PASSIVE = 1
    SUGGESTION = 2
    CO_PILOT = 3
    SUPERVISED = 4
    AUTONOMOUS = 5

class PermissionGuard:
    """
    Enforces autonomy levels. Checks if actions require explicit approval.
    """
    def __init__(self, default_level: AutonomyLevel = AutonomyLevel.SUGGESTION):
        self.current_level = default_level
        
    def set_level(self, level: int):
        if 0 <= level <= 5:
            self.current_level = AutonomyLevel(level)
            logger.info(f"Autonomy Level set to {self.current_level.name} ({level})")
        else:
            raise ValueError(f"Invalid autonomy level: {level}")

    def can_execute_automatically(self, action_risk_score: int) -> bool:
        """
        Risk Score mapping:
        1: Low risk (e.g., fetch data, show hint)
        5: Medium risk (e.g., compile code, switch file)
        10: High risk (e.g., delete file, execute shell script)
        """
        if self.current_level == AutonomyLevel.DISABLED:
            return False
            
        if self.current_level == AutonomyLevel.AUTONOMOUS:
            return True
            
        if self.current_level == AutonomyLevel.SUPERVISED:
            # Can do everything automatically EXCEPT high risk
            return action_risk_score < 10
            
        if self.current_level == AutonomyLevel.CO_PILOT:
            # Can do low/medium risk automatically
            return action_risk_score <= 5
            
        # Passive or Suggestion levels cannot execute actions automatically
        # They must ask for approval via UI or just show suggestions
        return False
        
    def requires_approval(self, action_risk_score: int) -> bool:
        """Returns True if the action needs explicit user approval dialog."""
        if self.current_level == AutonomyLevel.DISABLED:
            return False # Blocked completely
            
        return not self.can_execute_automatically(action_risk_score)
