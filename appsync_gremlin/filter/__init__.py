from typing import Dict, Callable

from gremlin_python.process.traversal import (
    eq, neq, lt, lte, gt, gte, within, without, startingWith, endingWith, containing,
    notStartingWith, notEndingWith, notContaining
)

from appsync_gremlin.filter.AbstractFilter import (
    AbstractFilter, ScalarFilter, VertexFilter, RelationshipDirection, RelationshipFilter
)


class IDScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "ne": neq,
            "eq": eq,
            "in": within,
            "not_in": without
        }


class StringScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "ne": neq,
            "eq": eq,
            "in": within,
            "not_in": without,
            "contains": containing,
            "not_contains": notContaining,
            "begins_with": startingWith,
            "not_begins_with": notStartingWith,
            "ends_with": endingWith,
            "not_ends_with": notEndingWith
        }


class IntScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "ne": neq,
            "eq": eq,
            "le": lte,
            "lt": lt,
            "ge": gte,
            "gt": gt,
            "in": within,
            "not_in": without
        }


class FloatScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "ne": neq,
            "eq": eq,
            "le": lte,
            "lt": lt,
            "ge": gte,
            "gt": gt,
            "in": within,
            "not_in": without
        }


class BooleanScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "eq": eq,
            "ne": neq
        }


class DateTimeScalarFilter(ScalarFilter):

    @property
    def sub_filters(self) -> Dict[str, Callable]:

        return {
            "ne": neq,
            "eq": eq,
            "le": lte,
            "lt": lt,
            "ge": gte,
            "gt": gt,
            "in": within,
            "not_in": without
        }
