from typing import Dict, Tuple, Callable
from enum import Enum
import functools

from gremlin_python.process.graph_traversal import GraphTraversal, out, in_, inV, outV, label


###


class RelationshipDirection(Enum):
    """
    Edge relationship direction.
    Supported options are IN and OUT.
    """

    IN = 0
    OUT = 1

class EdgeDirection(Enum):
    """
    Direction of edge -> vertex when traverser is on the edge.
    """

    IN = 0
    OUT = 1


RELATIONSHIP_DIRECTION_MAP = {
    RelationshipDirection.IN: in_,
    RelationshipDirection.OUT: out
}

EDGE_DIRECTION_MAP = {
    EdgeDirection.IN: inV,
    EdgeDirection.OUT: outV
}


### Types


TraversalFilterFunction = Callable[[GraphTraversal, Dict], GraphTraversal]
Relationship = Tuple[str, RelationshipDirection]
FilterFunction = Callable[[],Dict[str, Callable]]
NameFunction = Callable[[str], TraversalFilterFunction]


### Filters


def scalar_filter(filters_func: FilterFunction) -> NameFunction:
    """
    Scalar filter decorator. This decorator decorates a function that returns a dictionary
    that maps GraphQL fields to predicates.

    Using this dictionary we construct a filter_func that applies the predicates to the supplied traversal g,
    producing a traversal with the general form:

        g' = g.has(field_name, p_1).has(field_name, p_2). ... .has(field_name, p_n)

    where p_1, p_2, ..., p_n are predicates.

    We then wrap this filter_func in a name_func that requires a string field_name and returns the filter_func.
    This is so we can create scalar filters as

        id_scalar_filter(T.id)

        or

        @name(T.id)
        @scalar_filter
        def id_scalar_filter():
            return {
                .
                .
                .
            }

    We also use this interface as it also generalises to vertex_filters as well.

    :param filters_func: The filter function that returns the dictionary that maps
                         GraphQL field names to predicates. (FilterFunction)
    :return: The name function that requires a field_name and will return the filter_func. (NameFunction)
    """

    @functools.wraps(filters_func)
    def name_func(field_name: str) -> TraversalFilterFunction:
        """
        This is the name_func wrapper. It is designed to take a field name and apply it to a scalar
        filter. This completes the filter_func, thus producing a TraversalFilterFunction (A function
        that when applied to a traversal, applies the desired filters to the traversal).

        :param field_name: The Gremlin property / field name that the scalar filter is applied too. (str)
        :return: (TraversalFilterFunction)
        """

        def filter_func(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
            """
            This is the filter_func for a scalar filter.
            For a scalar property f on some vertex list V, we can apply a series of predicates that filter
            V based on f. The traversal that produces vertex list V is g and the filtered traversal has the form

                g' = g.has(f, p_1).has(f, p_2). ... .has(f, p_n),

            where p_1, p_2, ..., p_n are predicates generated based on the input_dict.

            :param traversal: (GraphTraversal)
            :param input_dict: (Dict)
            :return: (GraphTraversal)
            """

            filters = filters_func()

            for predicate_name, value in input_dict.items():
                predicate = filters.get(predicate_name)
                traversal = traversal.has(field_name, predicate(value))

            return traversal

        return filter_func

    return name_func


def vertex_filter(filters_func: FilterFunction) -> NameFunction:
    """
    Vertex filter decorator. This decorator decorates a function that returns a dictionary
    that maps GraphQL fields to relationship filters / scalar filters.

    Using this dictionary we construct a filter_func that applies the relationship_filters / scalar_filters in the
    supplied traversal g, thus producing a traversal with the general form:

        g' = r_f_1(r_f_2( ... (r_f_n(s_f_1( ... s_f_m(g) ... ))) ... ))

    where r_f_1, ..., r_f_n and s_f_1, ..., s_f_m are relationship and scalar filters respectively.
    Note that the order of application of scalar and relationship filters does not matter, however, it is advisable
    to apply scalar filters first (as I believe it more efficient).

    We then wrap this filter_func in a name_func that requires a string vertex_name and returns the filter_func.
    This is so we can create vertex filters as

        users_filter("User")

        or

        @name("User")
        @vertex_filter
        def users_filter():
            return {
                .
                .
                .
            }

    :param filters_func: The filter function that returns the dictionary that maps GraphQL
                         field names to relationship filters / scalar filters. (FilterFunction)
    :return: The name function that requires a field_name and will return the filter_func. (NameFunction)
    """

    @functools.wraps(filters_func)
    def name_func(vertex_name: str) -> TraversalFilterFunction:
        """
        This is the name_func wrapper. It is designed to take a vertex name and apply it to a vertex
        filter. This completes the filter_func, thus producing a TraversalFilterFunction (A function
        that when applied to a traversal, applies the desired filters to the traversal).

        :param vertex_name: The vertex label that the vertex filter is applied too. (str)
        :return: (TraversalFilterFunction)
        """

        def filter_func(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
            """
            This is the filter_func for a vertex filter.

            For some vertex list V produced by traversal g, we can apply a series of scalar and relationship filters
            on V. Using the filters dictionary and the input_dic we construct a Gremlin traversal g'
            that applies the relationship_filters / scalar_filters to g.

            The general form of g' is

                g' = r_f_1(r_f_2( ... (r_f_n(s_f_1( ... s_f_m(g) ... ))) ... ))

            where r_f_1, ..., r_f_n and s_f_1, ..., s_f_m are relationship and scalar filters respectively.

            :param traversal: (GraphTraversal)
            :param input_dict: (Dict)
            :return: (GraphTraversal)
            """

            filters = filters_func()

            traversal = traversal.filter(label().is_(vertex_name))

            for field_name, filter_input in input_dict.items():
                traversal = filters.get(field_name)(traversal, filter_input)

            return traversal

        return filter_func

    return name_func


def relationship_filter(relationship: Relationship, vertex_filter_func: TraversalFilterFunction) -> TraversalFilterFunction:
    """
    The relationship filter construction function. This function takes a relationship and a vertex filter
    and produces a gremlin traversal that filters vertices based on having the relationship and then
    filtering the vertices based on whether the other vertex in the relationship satisfies the vertex filter.

    Using the relationship R = (NAME, DIR), we can construct a Gremlin traversal g' that filters the traversal
    g based on whether the vertices in g have the relationship R. This traversal has the form:

        g' = g.where(DIR(NAME))

    However, we can then also apply filters to the other vertex in the relationship. Suppose we have a vertex
    filter v_f, then traversal g' has the form:

        g' = g.where(v_f(DIR(NAME))

    This allows us to form some interesting queries.

    :param relationship: A tuple in the form (relationship_name, relationship_direction) (Relationship)
    :param vertex_filter_func: (TraversalFilterFunction)
    :return: (TraversalFilterFunction)
    """

    relationship_name, relationship_direction = relationship

    def filter_func(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:

        traversal_ = RELATIONSHIP_DIRECTION_MAP[relationship_direction](relationship_name)

        traversal_ = vertex_filter_func(traversal_, input_dict)

        return traversal.where(traversal_)

    return filter_func


def edge_filter(edge_direction: EdgeDirection, vertex_filter_func: TraversalFilterFunction) -> TraversalFilterFunction:
    """
    The edge filter construction function. This function takes a edge direction and a vertex filter
    and produces a gremlin traversal that filters edges based on the vertex endpoints.

    Using the edge direction E, E \in {IN, OUT}, we can construct a Gremlin traversal g' that filters
    the traversal g (where all traversers of g are on edges) based on whether the endpoint vertex
    of the edge in direction E satisfies the filters applied to the endpoint vertex.
    This traversal has the general form:

        g' = g.where(v_f(E()))

    where v_f is some vertex filter.

    :param edge_direction: (EdgeDirection)
    :param vertex_filter_func: (TraversalFilterFunction)
    :return: (TraversalFilterFunction)
    """

    def filter_func(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:

        traversal_ = EDGE_DIRECTION_MAP[edge_direction]

        traversal_ = vertex_filter_func(traversal_, input_dict)

        return traversal.where(traversal_)

    return filter_func


def name(name: str) -> Callable[[NameFunction], TraversalFilterFunction]:
    """
    Name function decorator. This function is used to decorate a filter. For example, could have

        @name("User")
        @vertex_filter
        def users_filters():
            return {
                .
                .
                .
            }

    The name function decorator supplies the field_name / vertex_name to the scalar / vertex filters respectively.

    :param name: (str)
    :return:
    """

    def decorator(name_func: NameFunction) -> TraversalFilterFunction:

        @functools.wraps(name_func)
        def wrapper(traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:

            return name_func(name)(traversal, input_dict)

        return wrapper

    return decorator


