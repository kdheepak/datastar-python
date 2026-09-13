import json
import math

import pytest

from datastar_py import attributes


@pytest.mark.parametrize(
    ("attribute", "expected"),
    (
        (
            attributes.attribute_generator.attr(title="first, second"),
            {"data-attr": '{"title": (first, second)}'},
        ),
        (
            attributes.attribute_generator.class_({"active": "first, second"}),
            {"data-class": '{"active": (first, second)}'},
        ),
        (
            attributes.attribute_generator.style(width="first, second"),
            {"data-style": '{"width": (first, second)}'},
        ),
        (
            attributes.attribute_generator.signals(
                items1=["first", "second"],
                items2=["first, second"],
                items3="first, second",
            ),
            {
                "data-signals": (
                    '{"items1": ["first", "second"], "items2": ["first, second"], "items3": "first, second"}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                items1=["first", "second"],
                items2=["first, second"],
                items3="first, second",
                expressions_=True,
            ),
            {
                "data-signals": (
                    '{"items1": [(first), (second)], "items2": [(first, second)], "items3": (first, second)}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "items1": ["first", "second"],
                    "items2": ["first, second"],
                    "items3": "first, second",
                },
            ),
            {
                "data-signals": (
                    '{"items1": ["first", "second"], "items2": ["first, second"], "items3": "first, second"}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "items1": ["first", "second"],
                    "items2": ["first, second"],
                    "items3": "first, second",
                    "expressions_": False,
                },
                expressions_=True,
            ),
            {
                "data-signals": (
                    '{"items1": [(first), (second)], "items2": [(first, second)], "items3": (first, second), "expressions_": false}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "items1": ["first", "second"],
                    "items2": ["first, second"],
                    "items3": "first, second",
                },
                expressions_=True,
            ),
            {
                "data-signals": (
                    '{"items1": [(first), (second)], "items2": [(first, second)], "items3": (first, second)}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "items1": ("first", "second"),
                    "items2": ("first, second",),
                    "items3": "first, second",
                },
            ),
            {
                "data-signals": (
                    '{"items1": ["first", "second"], "items2": ["first, second"], "items3": "first, second"}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "items1": ("first", "second"),
                    "items2": ("first, second",),
                    "items3": "first, second",
                },
                expressions_=True,
            ),
            {
                "data-signals": (
                    '{"items1": [(first), (second)], "items2": [(first, second)], "items3": (first, second)}'
                )
            },
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "answer1": '{"value": 42}',
                    "answer2": {"value": 42},
                },
                expressions_=True,
            ),
            {"data-signals": ('{"answer1": ({"value": 42}), "answer2": {"value": 42}}')},
        ),
        (
            attributes.attribute_generator.signals(
                {
                    "answer1": '{"value": 42}',
                    "answer2": {"value": 42},
                },
            ),
            {"data-signals": ('{"answer1": "{\\"value\\": 42}", "answer2": {"value": 42}}')},
        ),
    ),
)
def test_expression_apis_parenthesize_ambiguous_values(attribute, expected):
    assert dict(attribute) == expected


@pytest.mark.parametrize(
    ("attribute", "expected"),
    (
        (
            attributes.attribute_generator.attr(title='"hello"', hidden="$closed"),
            {"data-attr": '{"title": ("hello"), "hidden": ($closed)}'},
        ),
        (
            attributes.attribute_generator.class_({"active item": "$selected", "plain": "true"}),
            {"data-class": '{"active item": ($selected), "plain": (true)}'},
        ),
        (
            attributes.attribute_generator.style(width="$width + 'px'"),
            {"data-style": "{\"width\": ($width + 'px')}"},
        ),
        (
            attributes.attribute_generator.signals({"form": {"count": "1 + 1"}}),
            {"data-signals": '{"form": {"count": "1 + 1"}}'},
        ),
        (
            attributes.attribute_generator.signals(
                {"form": {"count": "1 + 1"}}, expressions_=True
            ),
            {"data-signals": '{"form": {"count": (1 + 1)}}'},
        ),
    ),
)
def test_expression_apis_wrap_values_explicitly(attribute, expected):
    assert dict(attribute) == expected


def test_expression_signals_recurse_through_nested_lists():
    assert dict(
        attributes.attribute_generator.signals(
            {
                "form": {
                    "total": "2 * 3",
                    "items": ["$first", "$second"],
                    "groups": [["$third"]],
                }
            },
            expressions_=True,
        )
    ) == {
        "data-signals": (
            '{"form": {"total": (2 * 3), "items": [($first), ($second)], "groups": [[($third)]]}}'
        )
    }


def test_literal_signals_remain_data_and_escape_action_tokens():
    signals = {
        "signal_example": "$otherSignal",
        "action_example": '@post("/sse")',
        "email_example": "person@example.com",
        "expression_example": "1 + 1",
        "quoted_example": 'a "quoted" value',
    }

    rendered = dict(attributes.attribute_generator.signals(signals))["data-signals"]
    assert isinstance(rendered, str)

    assert rendered == "".join(
        [
            '{"signal_example": "$otherSignal", ',
            '"action_example": "@post(\\"/sse\\")", ',
            '"email_example": "person@example.com", ',
            '"expression_example": "1 + 1", ',
            '"quoted_example": "a \\"quoted\\" value"}',
        ]
    )
    assert json.loads(rendered) == signals


def test_mapping_values_serialize_recursively():
    value = {
        "literal": "text",
        "nested": {
            # These Python spellings differ from JavaScript
            # This test can catch accidental fallbacks to str()
            # instead of JSON serialization.
            "items": [True, False, None, 3],
            "expression": attributes.JSExpression("1 + 1"),
        },
    }

    assert attributes.javascript(value) == (
        '{"literal": "text", "nested": {"items": [true, false, null, 3], "expression": (1 + 1)}}'
    )


def test_mapping_keys_are_strings_and_escaped_as_data():
    with pytest.raises(TypeError, match="object keys must be strings"):
        attributes.javascript({1: "value"})

    assert (
        attributes.javascript(
            {
                'quote"\\snow雪': "value",
                '@post("key")': "action-looking key",
            }
        )
        == '{"quote\\"\\\\snow\\u96ea": "value", "@post(\\"key\\")": "action-looking key"}'
    )


@pytest.mark.parametrize("expressions", (False, True))
@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf))
def test_non_finite_signal_values_are_rejected_in_both_modes(expressions, value):
    with pytest.raises(ValueError):
        attributes.attribute_generator.signals({"value": value}, expressions_=expressions)
