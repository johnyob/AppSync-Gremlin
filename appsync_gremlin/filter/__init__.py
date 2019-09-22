from gremlin_python.process.traversal import (
    eq, neq, lt, lte, gt, gte, within, without, startingWith, endingWith, containing,
    notStartingWith, notEndingWith, notContaining
)

from appsync_gremlin.filter.Filter import (
    RelationshipDirection, scalar_filter, vertex_filter, relationship_filter,
    TraversalFilterFunction, Relationship, FilterFunction, NameFunction
)


@scalar_filter
def id_filter():
    return {
        "ne": neq,
        "eq": eq,
        "in": within,
        "not_in": without
    }


@scalar_filter
def string_filter():
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


@scalar_filter
def int_filter():
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


@scalar_filter
def float_filter():
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


@scalar_filter
def boolean_filter():
    return {
        "eq": eq,
        "ne": neq
    }


@scalar_filter
def date_time_filter():
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


@scalar_filter
def enum_filter():
    return {
        "eq": eq,
        "neq": neq,
        "in": within,
        "not_in": without
    }
