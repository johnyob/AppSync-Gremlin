from typing import Any, Dict

from gremlin_python.process.traversal import (
    eq, neq, lt, lte, gt, gte, within, without, startingWith, endingWith, containing,
    notStartingWith, notEndingWith, notContaining, P
)
from gremlin_python.process.graph_traversal import GraphTraversal


PREDICATE_MAP = {
    "eq": eq,
    "ne": neq,
    "lt": lt,
    "le": lte,
    "gt": gt,
    "gte": gte,
    "in": within,
    "not_in": without,
    "begins_with": startingWith,
    "not_begins_with": notStartingWith,
    "ends_with": endingWith,
    "not_ends_with": notEndingWith,
    "contains": containing,
    "not_contains": notContaining
}


def filter_input_to_predicate(predicate_name: str, value: Any) -> P:
    """

    :param predicate_name:
    :param value:
    :return:
    """

    return PREDICATE_MAP[predicate_name](value)


def apply_filters(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
    """

    :param traversal:
    :param input_dict:
    :return:
    """

    for field_name, filter_input in input_dict.items():
        for predicate_name, value in filter_input.items():
            traversal = traversal.has(field_name, filter_input_to_predicate(predicate_name, value))

    return traversal

