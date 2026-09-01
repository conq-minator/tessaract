import pytest
from tutor_ui.services.permission import PermissionGuard, AutonomyLevel
from tutor_ui.services.notification import NotificationManager

def test_permission_guard_disabled():
    guard = PermissionGuard(default_level=AutonomyLevel.DISABLED)
    assert not guard.can_execute_automatically(1)
    assert not guard.requires_approval(1) # Blocked completely, doesn't require approval because it can't run

def test_permission_guard_suggestion():
    guard = PermissionGuard(default_level=AutonomyLevel.SUGGESTION)
    assert not guard.can_execute_automatically(1)
    assert guard.requires_approval(1)

def test_permission_guard_copilot():
    guard = PermissionGuard(default_level=AutonomyLevel.CO_PILOT)
    assert guard.can_execute_automatically(5)
    assert not guard.can_execute_automatically(6)
    assert guard.requires_approval(10)

def test_permission_guard_autonomous():
    guard = PermissionGuard(default_level=AutonomyLevel.AUTONOMOUS)
    assert guard.can_execute_automatically(10)
    assert not guard.requires_approval(10)

@pytest.mark.asyncio
async def test_notification_manager():
    nm = NotificationManager()
    queue = await nm.register_client()
    
    assert len(nm.clients) == 1
    
    # Broadcast
    await nm.broadcast("test_event", {"msg": "hello"})
    
    msg = await queue.get()
    assert msg["type"] == "test_event"
    assert msg["data"]["msg"] == "hello"
    
    nm.unregister_client(queue)
    assert len(nm.clients) == 0
