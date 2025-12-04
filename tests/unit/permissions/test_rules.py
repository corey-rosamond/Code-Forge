"""Unit tests for permission rules and pattern matching."""

import pytest

from opencode.permissions.models import (
    PermissionLevel,
    PermissionRule,
)
from opencode.permissions.rules import (
    PatternMatcher,
    RuleSet,
)


class TestPatternMatcherToolPatterns:
    """Tests for PatternMatcher tool patterns."""

    def test_exact_tool_match(self):
        """Test exact tool name match."""
        assert PatternMatcher.match("tool:bash", "bash", {}) is True
        assert PatternMatcher.match("tool:read", "read", {}) is True

    def test_exact_tool_no_match(self):
        """Test exact tool name non-match."""
        assert PatternMatcher.match("tool:bash", "read", {}) is False
        assert PatternMatcher.match("tool:read", "bash", {}) is False

    def test_glob_tool_match_star(self):
        """Test glob pattern with * wildcard."""
        assert PatternMatcher.match("tool:bash*", "bash", {}) is True
        assert PatternMatcher.match("tool:bash*", "bash_output", {}) is True
        assert PatternMatcher.match("tool:*bash", "mybash", {}) is True
        assert PatternMatcher.match("tool:*", "anything", {}) is True

    def test_glob_tool_match_question(self):
        """Test glob pattern with ? wildcard."""
        assert PatternMatcher.match("tool:rea?", "read", {}) is True
        assert PatternMatcher.match("tool:rea?", "real", {}) is True
        assert PatternMatcher.match("tool:rea?", "reads", {}) is False

    def test_implicit_tool_pattern(self):
        """Test pattern without tool: prefix is treated as tool pattern."""
        assert PatternMatcher.match("bash", "bash", {}) is True
        assert PatternMatcher.match("bash*", "bash_output", {}) is True


class TestPatternMatcherArgumentPatterns:
    """Tests for PatternMatcher argument patterns."""

    def test_exact_arg_match(self):
        """Test exact argument value match."""
        assert PatternMatcher.match(
            "arg:command:ls", "bash", {"command": "ls"}
        ) is True

    def test_exact_arg_no_match(self):
        """Test exact argument value non-match."""
        assert PatternMatcher.match(
            "arg:command:ls", "bash", {"command": "cat"}
        ) is False

    def test_glob_arg_match(self):
        """Test glob pattern on argument value."""
        assert PatternMatcher.match(
            "arg:command:*git*", "bash", {"command": "git status"}
        ) is True
        assert PatternMatcher.match(
            "arg:command:*git*", "bash", {"command": "ls"}
        ) is False

    def test_missing_arg_no_match(self):
        """Test that missing argument doesn't match."""
        assert PatternMatcher.match(
            "arg:command:*", "bash", {}
        ) is False
        assert PatternMatcher.match(
            "arg:file_path:*", "read", {"other_arg": "value"}
        ) is False

    def test_arg_without_pattern(self):
        """Test arg pattern without explicit pattern matches any value."""
        assert PatternMatcher.match(
            "arg:command", "bash", {"command": "anything"}
        ) is True

    def test_arg_converts_to_string(self):
        """Test that argument values are converted to strings."""
        assert PatternMatcher.match(
            "arg:count:42", "tool", {"count": 42}
        ) is True


class TestPatternMatcherRegexPatterns:
    """Tests for PatternMatcher regex patterns."""

    def test_regex_starts_with_caret(self):
        """Test regex pattern starting with ^."""
        assert PatternMatcher.match(
            "arg:file_path:^/etc/.*", "write", {"file_path": "/etc/passwd"}
        ) is True
        assert PatternMatcher.match(
            "arg:file_path:^/etc/.*", "write", {"file_path": "/home/user"}
        ) is False

    def test_regex_ends_with_dollar(self):
        """Test regex pattern ending with $."""
        assert PatternMatcher.match(
            "arg:file_path:.*\\.py$", "read", {"file_path": "test.py"}
        ) is True
        assert PatternMatcher.match(
            "arg:file_path:.*\\.py$", "read", {"file_path": "test.pyc"}
        ) is False

    def test_regex_with_alternation(self):
        """Test regex pattern with | alternation."""
        assert PatternMatcher.match(
            "arg:command:(rm|del)", "bash", {"command": "rm file"}
        ) is True
        assert PatternMatcher.match(
            "arg:command:(rm|del)", "bash", {"command": "del file"}
        ) is True
        assert PatternMatcher.match(
            "arg:command:(rm|del)", "bash", {"command": "cp file"}
        ) is False

    def test_invalid_regex_returns_false(self):
        """Test that invalid regex pattern returns False."""
        # Invalid regex with unmatched parenthesis
        assert PatternMatcher.match(
            "arg:command:((invalid", "bash", {"command": "anything"}
        ) is False


class TestPatternMatcherCategoryPatterns:
    """Tests for PatternMatcher category patterns."""

    def test_category_match_by_value(self):
        """Test category matching by category value."""
        assert PatternMatcher.match(
            "category:read_operations", "read", {}
        ) is True
        assert PatternMatcher.match(
            "category:write_operations", "write", {}
        ) is True

    def test_category_match_by_name(self):
        """Test category matching by category name."""
        assert PatternMatcher.match(
            "category:read", "read", {}
        ) is True
        assert PatternMatcher.match(
            "category:execute", "bash", {}
        ) is True

    def test_category_no_match(self):
        """Test category non-match."""
        assert PatternMatcher.match(
            "category:write_operations", "read", {}
        ) is False
        assert PatternMatcher.match(
            "category:execute", "read", {}
        ) is False


class TestPatternMatcherCombinedPatterns:
    """Tests for PatternMatcher combined patterns."""

    def test_tool_and_arg_both_match(self):
        """Test combined tool and arg pattern when both match."""
        assert PatternMatcher.match(
            "tool:bash,arg:command:*rm*",
            "bash",
            {"command": "rm file.txt"}
        ) is True

    def test_tool_matches_arg_doesnt(self):
        """Test combined pattern when tool matches but arg doesn't."""
        assert PatternMatcher.match(
            "tool:bash,arg:command:*rm*",
            "bash",
            {"command": "ls"}
        ) is False

    def test_tool_doesnt_match_arg_does(self):
        """Test combined pattern when tool doesn't match but arg does."""
        assert PatternMatcher.match(
            "tool:bash,arg:command:*rm*",
            "read",
            {"command": "rm file.txt"}
        ) is False

    def test_multiple_args(self):
        """Test pattern with multiple argument constraints."""
        assert PatternMatcher.match(
            "tool:bash,arg:command:ls,arg:timeout:30",
            "bash",
            {"command": "ls", "timeout": "30"}
        ) is True
        assert PatternMatcher.match(
            "tool:bash,arg:command:ls,arg:timeout:30",
            "bash",
            {"command": "ls", "timeout": "60"}
        ) is False


class TestPatternMatcherParsePattern:
    """Tests for PatternMatcher.parse_pattern."""

    def test_parse_tool_pattern(self):
        """Test parsing tool pattern."""
        components = PatternMatcher.parse_pattern("tool:bash")
        assert components == [("tool", "", "bash")]

    def test_parse_arg_pattern(self):
        """Test parsing arg pattern."""
        components = PatternMatcher.parse_pattern("arg:command:*rm*")
        assert components == [("arg", "command", "*rm*")]

    def test_parse_arg_pattern_no_value(self):
        """Test parsing arg pattern without value pattern."""
        components = PatternMatcher.parse_pattern("arg:command")
        assert components == [("arg", "command", "*")]

    def test_parse_category_pattern(self):
        """Test parsing category pattern."""
        components = PatternMatcher.parse_pattern("category:read")
        assert components == [("category", "", "read")]

    def test_parse_combined_pattern(self):
        """Test parsing combined pattern."""
        components = PatternMatcher.parse_pattern("tool:bash,arg:command:*")
        assert components == [
            ("tool", "", "bash"),
            ("arg", "command", "*"),
        ]

    def test_parse_implicit_tool(self):
        """Test parsing implicit tool pattern."""
        components = PatternMatcher.parse_pattern("bash")
        assert components == [("tool", "", "bash")]


class TestPatternMatcherSpecificity:
    """Tests for PatternMatcher.specificity."""

    def test_exact_tool_more_specific_than_glob(self):
        """Test exact tool is more specific than glob."""
        exact = PatternMatcher.specificity("tool:bash")
        glob = PatternMatcher.specificity("tool:bash*")
        assert exact > glob

    def test_tool_more_specific_than_category(self):
        """Test tool pattern is more specific than category."""
        tool = PatternMatcher.specificity("tool:read")
        category = PatternMatcher.specificity("category:read_operations")
        assert tool > category

    def test_tool_with_arg_more_specific(self):
        """Test tool+arg is more specific than just tool."""
        tool_only = PatternMatcher.specificity("tool:bash")
        tool_arg = PatternMatcher.specificity("tool:bash,arg:command:*")
        assert tool_arg > tool_only

    def test_exact_arg_more_specific_than_glob_arg(self):
        """Test exact arg is more specific than glob arg."""
        exact = PatternMatcher.specificity("tool:bash,arg:command:ls")
        glob = PatternMatcher.specificity("tool:bash,arg:command:*")
        assert exact > glob


class TestRuleSet:
    """Tests for RuleSet class."""

    def test_creation_empty(self):
        """Test creating empty rule set."""
        ruleset = RuleSet()
        assert len(ruleset) == 0
        assert ruleset.default == PermissionLevel.ASK

    def test_creation_with_rules(self):
        """Test creating rule set with rules."""
        rules = [
            PermissionRule("tool:read", PermissionLevel.ALLOW),
            PermissionRule("tool:bash", PermissionLevel.ASK),
        ]
        ruleset = RuleSet(rules=rules, default=PermissionLevel.DENY)
        assert len(ruleset) == 2
        assert ruleset.default == PermissionLevel.DENY

    def test_add_rule(self):
        """Test adding a rule."""
        ruleset = RuleSet()
        ruleset.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))
        assert len(ruleset) == 1

    def test_remove_rule_exists(self):
        """Test removing an existing rule."""
        ruleset = RuleSet()
        ruleset.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))
        assert ruleset.remove_rule("tool:bash") is True
        assert len(ruleset) == 0

    def test_remove_rule_not_exists(self):
        """Test removing non-existent rule."""
        ruleset = RuleSet()
        assert ruleset.remove_rule("tool:nonexistent") is False

    def test_get_rule_exists(self):
        """Test getting an existing rule."""
        ruleset = RuleSet()
        rule = PermissionRule("tool:bash", PermissionLevel.ASK)
        ruleset.add_rule(rule)
        found = ruleset.get_rule("tool:bash")
        assert found is rule

    def test_get_rule_not_exists(self):
        """Test getting non-existent rule."""
        ruleset = RuleSet()
        assert ruleset.get_rule("tool:nonexistent") is None

    def test_iterate_rules(self):
        """Test iterating over rules."""
        rules = [
            PermissionRule("tool:read", PermissionLevel.ALLOW),
            PermissionRule("tool:bash", PermissionLevel.ASK),
        ]
        ruleset = RuleSet(rules=rules)
        collected = list(ruleset)
        assert collected == rules


class TestRuleSetEvaluate:
    """Tests for RuleSet.evaluate."""

    def test_no_matching_rules_returns_default(self):
        """Test that no matching rules returns default."""
        ruleset = RuleSet(default=PermissionLevel.ASK)
        result = ruleset.evaluate("unknown", {})
        assert result.level == PermissionLevel.ASK
        assert result.rule is None
        assert "default" in result.reason.lower()

    def test_matching_rule_returns_its_permission(self):
        """Test matching rule returns its permission level."""
        ruleset = RuleSet()
        ruleset.add_rule(PermissionRule("tool:read", PermissionLevel.ALLOW))
        result = ruleset.evaluate("read", {})
        assert result.level == PermissionLevel.ALLOW
        assert result.rule is not None
        assert result.rule.pattern == "tool:read"

    def test_disabled_rule_not_matched(self):
        """Test that disabled rules are not matched."""
        ruleset = RuleSet()
        ruleset.add_rule(
            PermissionRule("tool:bash", PermissionLevel.DENY, enabled=False)
        )
        result = ruleset.evaluate("bash", {})
        assert result.level == PermissionLevel.ASK  # Default
        assert result.rule is None

    def test_most_specific_rule_wins(self):
        """Test that more specific rule wins over general."""
        ruleset = RuleSet()
        ruleset.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))
        ruleset.add_rule(
            PermissionRule("tool:bash,arg:command:ls", PermissionLevel.ALLOW)
        )
        result = ruleset.evaluate("bash", {"command": "ls"})
        assert result.level == PermissionLevel.ALLOW

    def test_higher_priority_wins(self):
        """Test that higher priority rule wins."""
        ruleset = RuleSet()
        ruleset.add_rule(
            PermissionRule("tool:bash", PermissionLevel.ALLOW, priority=0)
        )
        ruleset.add_rule(
            PermissionRule("tool:bash", PermissionLevel.DENY, priority=10)
        )
        result = ruleset.evaluate("bash", {})
        assert result.level == PermissionLevel.DENY

    def test_more_restrictive_wins_on_tie(self):
        """Test that more restrictive rule wins on tie."""
        ruleset = RuleSet()
        ruleset.add_rule(
            PermissionRule("tool:bash", PermissionLevel.ALLOW, priority=0)
        )
        ruleset.add_rule(
            PermissionRule("tool:bash", PermissionLevel.DENY, priority=0)
        )
        result = ruleset.evaluate("bash", {})
        assert result.level == PermissionLevel.DENY

    def test_rule_description_in_reason(self):
        """Test that rule description appears in reason."""
        ruleset = RuleSet()
        ruleset.add_rule(
            PermissionRule(
                "tool:bash",
                PermissionLevel.ASK,
                description="Confirm shell commands",
            )
        )
        result = ruleset.evaluate("bash", {})
        assert result.reason == "Confirm shell commands"

    def test_rule_pattern_in_reason_when_no_description(self):
        """Test that rule pattern appears in reason when no description."""
        ruleset = RuleSet()
        ruleset.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))
        result = ruleset.evaluate("bash", {})
        assert "tool:bash" in result.reason


class TestRuleSetSerialization:
    """Tests for RuleSet serialization."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        ruleset = RuleSet(default=PermissionLevel.DENY)
        ruleset.add_rule(PermissionRule("tool:read", PermissionLevel.ALLOW))
        data = ruleset.to_dict()
        assert data["default"] == "deny"
        assert len(data["rules"]) == 1
        assert data["rules"][0]["pattern"] == "tool:read"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "default": "ask",
            "rules": [
                {"pattern": "tool:read", "permission": "allow"},
                {"pattern": "tool:bash", "permission": "ask"},
            ],
        }
        ruleset = RuleSet.from_dict(data)
        assert ruleset.default == PermissionLevel.ASK
        assert len(ruleset) == 2

    def test_from_dict_empty(self):
        """Test deserialization from empty dictionary."""
        ruleset = RuleSet.from_dict({})
        assert ruleset.default == PermissionLevel.ASK
        assert len(ruleset) == 0

    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict are symmetric."""
        original = RuleSet(default=PermissionLevel.DENY)
        original.add_rule(
            PermissionRule(
                "tool:bash,arg:command:*rm*",
                PermissionLevel.DENY,
                description="Block rm",
                priority=50,
            )
        )
        data = original.to_dict()
        restored = RuleSet.from_dict(data)
        assert restored.default == original.default
        assert len(restored) == len(original)
        assert restored.rules[0].pattern == original.rules[0].pattern
        assert restored.rules[0].permission == original.rules[0].permission
