"""Unit tests for permission models."""

import pytest

from opencode.permissions.models import (
    PermissionLevel,
    PermissionCategory,
    PermissionRule,
    PermissionResult,
    TOOL_CATEGORIES,
    get_tool_category,
)


class TestPermissionLevel:
    """Tests for PermissionLevel enum."""

    def test_values(self):
        """Test that all expected values exist."""
        assert PermissionLevel.ALLOW.value == "allow"
        assert PermissionLevel.ASK.value == "ask"
        assert PermissionLevel.DENY.value == "deny"

    def test_less_than_allow_ask(self):
        """Test ALLOW < ASK."""
        assert PermissionLevel.ALLOW < PermissionLevel.ASK

    def test_less_than_ask_deny(self):
        """Test ASK < DENY."""
        assert PermissionLevel.ASK < PermissionLevel.DENY

    def test_less_than_allow_deny(self):
        """Test ALLOW < DENY."""
        assert PermissionLevel.ALLOW < PermissionLevel.DENY

    def test_greater_than_deny_allow(self):
        """Test DENY > ALLOW."""
        assert PermissionLevel.DENY > PermissionLevel.ALLOW

    def test_greater_than_deny_ask(self):
        """Test DENY > ASK."""
        assert PermissionLevel.DENY > PermissionLevel.ASK

    def test_greater_than_ask_allow(self):
        """Test ASK > ALLOW."""
        assert PermissionLevel.ASK > PermissionLevel.ALLOW

    def test_less_than_equal_same(self):
        """Test equality with less than or equal."""
        assert PermissionLevel.ALLOW <= PermissionLevel.ALLOW
        assert PermissionLevel.ASK <= PermissionLevel.ASK
        assert PermissionLevel.DENY <= PermissionLevel.DENY

    def test_greater_than_equal_same(self):
        """Test equality with greater than or equal."""
        assert PermissionLevel.ALLOW >= PermissionLevel.ALLOW
        assert PermissionLevel.ASK >= PermissionLevel.ASK
        assert PermissionLevel.DENY >= PermissionLevel.DENY

    def test_less_than_equal_different(self):
        """Test less than or equal with different values."""
        assert PermissionLevel.ALLOW <= PermissionLevel.ASK
        assert PermissionLevel.ASK <= PermissionLevel.DENY

    def test_greater_than_equal_different(self):
        """Test greater than or equal with different values."""
        assert PermissionLevel.DENY >= PermissionLevel.ASK
        assert PermissionLevel.ASK >= PermissionLevel.ALLOW

    def test_comparison_with_non_permission_level(self):
        """Test comparison with non-PermissionLevel returns NotImplemented."""
        assert PermissionLevel.ALLOW.__lt__("allow") is NotImplemented
        assert PermissionLevel.ALLOW.__le__("allow") is NotImplemented
        assert PermissionLevel.ALLOW.__gt__("allow") is NotImplemented
        assert PermissionLevel.ALLOW.__ge__("allow") is NotImplemented

    def test_string_conversion(self):
        """Test string value matches enum value."""
        assert str(PermissionLevel.ALLOW) == "PermissionLevel.ALLOW"
        assert PermissionLevel.ALLOW.value == "allow"


class TestPermissionCategory:
    """Tests for PermissionCategory enum."""

    def test_values(self):
        """Test that all expected values exist."""
        assert PermissionCategory.READ.value == "read_operations"
        assert PermissionCategory.WRITE.value == "write_operations"
        assert PermissionCategory.EXECUTE.value == "execute_operations"
        assert PermissionCategory.NETWORK.value == "network_operations"
        assert PermissionCategory.DESTRUCTIVE.value == "destructive_operations"
        assert PermissionCategory.OTHER.value == "other_operations"


class TestPermissionRule:
    """Tests for PermissionRule dataclass."""

    def test_creation_minimal(self):
        """Test creating a rule with minimal arguments."""
        rule = PermissionRule(
            pattern="tool:bash",
            permission=PermissionLevel.ASK,
        )
        assert rule.pattern == "tool:bash"
        assert rule.permission == PermissionLevel.ASK
        assert rule.description == ""
        assert rule.enabled is True
        assert rule.priority == 0

    def test_creation_full(self):
        """Test creating a rule with all arguments."""
        rule = PermissionRule(
            pattern="tool:bash",
            permission=PermissionLevel.DENY,
            description="Block bash commands",
            enabled=False,
            priority=100,
        )
        assert rule.pattern == "tool:bash"
        assert rule.permission == PermissionLevel.DENY
        assert rule.description == "Block bash commands"
        assert rule.enabled is False
        assert rule.priority == 100

    def test_to_dict(self):
        """Test serialization to dictionary."""
        rule = PermissionRule(
            pattern="tool:read",
            permission=PermissionLevel.ALLOW,
            description="Allow file reading",
            enabled=True,
            priority=10,
        )
        data = rule.to_dict()
        assert data == {
            "pattern": "tool:read",
            "permission": "allow",
            "description": "Allow file reading",
            "enabled": True,
            "priority": 10,
        }

    def test_from_dict_minimal(self):
        """Test deserialization from minimal dictionary."""
        data = {
            "pattern": "tool:write",
            "permission": "deny",
        }
        rule = PermissionRule.from_dict(data)
        assert rule.pattern == "tool:write"
        assert rule.permission == PermissionLevel.DENY
        assert rule.description == ""
        assert rule.enabled is True
        assert rule.priority == 0

    def test_from_dict_full(self):
        """Test deserialization from full dictionary."""
        data = {
            "pattern": "tool:bash",
            "permission": "ask",
            "description": "Confirm commands",
            "enabled": False,
            "priority": 50,
        }
        rule = PermissionRule.from_dict(data)
        assert rule.pattern == "tool:bash"
        assert rule.permission == PermissionLevel.ASK
        assert rule.description == "Confirm commands"
        assert rule.enabled is False
        assert rule.priority == 50

    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict are symmetric."""
        original = PermissionRule(
            pattern="tool:bash,arg:command:*rm*",
            permission=PermissionLevel.DENY,
            description="Block dangerous commands",
            enabled=True,
            priority=99,
        )
        data = original.to_dict()
        restored = PermissionRule.from_dict(data)
        assert restored.pattern == original.pattern
        assert restored.permission == original.permission
        assert restored.description == original.description
        assert restored.enabled == original.enabled
        assert restored.priority == original.priority


class TestPermissionResult:
    """Tests for PermissionResult dataclass."""

    def test_creation_minimal(self):
        """Test creating a result with minimal arguments."""
        result = PermissionResult(level=PermissionLevel.ALLOW)
        assert result.level == PermissionLevel.ALLOW
        assert result.rule is None
        assert result.reason == ""

    def test_creation_full(self):
        """Test creating a result with all arguments."""
        rule = PermissionRule(pattern="tool:bash", permission=PermissionLevel.ASK)
        result = PermissionResult(
            level=PermissionLevel.ASK,
            rule=rule,
            reason="Matched rule: tool:bash",
        )
        assert result.level == PermissionLevel.ASK
        assert result.rule == rule
        assert result.reason == "Matched rule: tool:bash"

    def test_allowed_property_true(self):
        """Test allowed property when level is ALLOW."""
        result = PermissionResult(level=PermissionLevel.ALLOW)
        assert result.allowed is True
        assert result.needs_confirmation is False
        assert result.denied is False

    def test_needs_confirmation_property_true(self):
        """Test needs_confirmation property when level is ASK."""
        result = PermissionResult(level=PermissionLevel.ASK)
        assert result.allowed is False
        assert result.needs_confirmation is True
        assert result.denied is False

    def test_denied_property_true(self):
        """Test denied property when level is DENY."""
        result = PermissionResult(level=PermissionLevel.DENY)
        assert result.allowed is False
        assert result.needs_confirmation is False
        assert result.denied is True


class TestToolCategories:
    """Tests for tool category mapping."""

    def test_read_tools(self):
        """Test read tool categories."""
        assert get_tool_category("read") == PermissionCategory.READ
        assert get_tool_category("glob") == PermissionCategory.READ
        assert get_tool_category("grep") == PermissionCategory.READ
        assert get_tool_category("bash_output") == PermissionCategory.READ

    def test_write_tools(self):
        """Test write tool categories."""
        assert get_tool_category("write") == PermissionCategory.WRITE
        assert get_tool_category("edit") == PermissionCategory.WRITE
        assert get_tool_category("notebook_edit") == PermissionCategory.WRITE

    def test_execute_tools(self):
        """Test execute tool categories."""
        assert get_tool_category("bash") == PermissionCategory.EXECUTE
        assert get_tool_category("kill_shell") == PermissionCategory.EXECUTE

    def test_network_tools(self):
        """Test network tool categories."""
        assert get_tool_category("web_fetch") == PermissionCategory.NETWORK
        assert get_tool_category("web_search") == PermissionCategory.NETWORK

    def test_unknown_tool(self):
        """Test unknown tool returns OTHER category."""
        assert get_tool_category("unknown_tool") == PermissionCategory.OTHER
        assert get_tool_category("custom_tool") == PermissionCategory.OTHER

    def test_tool_categories_constant(self):
        """Test TOOL_CATEGORIES constant is populated."""
        assert "read" in TOOL_CATEGORIES
        assert "write" in TOOL_CATEGORIES
        assert "bash" in TOOL_CATEGORIES
        assert TOOL_CATEGORIES["read"] == PermissionCategory.READ
