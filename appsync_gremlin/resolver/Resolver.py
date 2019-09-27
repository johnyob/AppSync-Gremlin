from typing import Dict, Any, List, Tuple, Optional, Callable
from datetime import datetime
from math import ceil
import functools

from gremlin_python.process.graph_traversal import GraphTraversal, unfold, __
from gremlin_python.process.traversal import T

from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.filter.Filter import TraversalFilterFunction


### Helpers

GREMLIN_KEY_MAP = {
    T.label: "__typename"
}


def format_gremlin_keys(key: T) -> str:

    if key in GREMLIN_KEY_MAP:
        return GREMLIN_KEY_MAP.get(key)

    return key.name


def format_key(key: Any) -> Any:
    """

    :param key:
    :return:
    """

    if isinstance(key, T):
        return format_gremlin_keys(key)

    return key


def format_value(value: Any) -> Any:
    """

    :param value:
    :return:
    """

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def format_value_map(value_map: Dict) -> Dict:
    """

    :param value_map:
    :return:
    """

    return {
        format_key(k): format_value(v) for k, v in value_map.items()
    }


def get_range(page: int, per_page: int) -> Tuple[int, int]:
    """
    Returns the Gremlin range from page options in the format:
        (first, last)

    :param page: (Integer)
    :param per_page: (Integer)
    :return: (Integer, Integer)
    """

    return (page - 1) * per_page, page * per_page


def paginate(response: List[Dict], page: int, per_page: int, total: int) -> Dict:

    return {
        "data": response,
        "page": page,
        "per_page": per_page,
        "total": ceil(total/per_page)
    }


def select_current_vertex(traversal: GraphTraversal) -> GraphTraversal:

    return traversal.valueMap(True).by(unfold())

### Types


TraversalResolverFunction = Callable[[GraphTraversal, ResolverInput], GraphTraversal]
VertexListFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Dict]
VertexFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Optional[Dict]]
CalculatedFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Any]
ResolverFunction = Callable[[GraphTraversal, ResolverInput], Any]
FormatFunction = Callable[[Dict], Dict]
TraversalSelectionFunction = Callable[[GraphTraversal], GraphTraversal]

### Resolvers


def vertex_list_field_resolver(
        filter: TraversalFilterFunction,
        select: TraversalSelectionFunction = select_current_vertex,
        format: FormatFunction = format_value_map
) -> Callable:
    """

    :param filter_func:
    :return:
    """

    def wrapper(traversal_func: TraversalResolverFunction) -> VertexListFieldResolverFunction:
        """

        :param traversal_func:
        :return:
        """

        @functools.wraps(traversal_func)
        def handler(traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:
            """

            :param traversal:
            :param resolver_input:
            :return:
            """

            input_dict = resolver_input.arguments.get("input", {})
            pagination_info = resolver_input.arguments.get("pagination", {
                "page": 1,
                "per_page": 10
            })

            page, per_page = pagination_info.get("page"), pagination_info.get("per_page")
            first, last = get_range(page, per_page)

            traversal = traversal_func(traversal, resolver_input)
            traversal = filter(traversal, input_dict)
            traversal = select(traversal)

            response_and_total = traversal.fold().project("data", "total").select("data", "total").\
                by(__.unfold().range(first, last).fold()).by(__.unfold().count()).next()

            response = [format(value_map) for value_map in response_and_total.get("data")]

            return paginate(response, page, per_page, response_and_total.get("total"))

        return handler

    return wrapper


def vertex_field_resolver(
        format: FormatFunction = format_value_map,
        select: TraversalSelectionFunction = select_current_vertex
) -> Callable:

    def wrapper(traversal_func: TraversalResolverFunction) -> VertexFieldResolverFunction:
        """

        :param traversal_func:
        :return:
        """

        @functools.wraps(traversal_func)
        def handler(traversal: GraphTraversal, resolver_input: ResolverInput) -> Optional[Dict]:
            """

            :param traversal:
            :param resolver_input:
            :return:
            """

            traversal = traversal_func(traversal, resolver_input)
            traversal = select(traversal)

            if traversal.hasNext():
                return format(traversal.next())

            return None

        return handler

    return wrapper


def calculated_field_resolver(traversal_func: TraversalResolverFunction) -> CalculatedFieldResolverFunction:
    """

    :param traversal_func:
    :return:
    """

    @functools.wraps(traversal_func)
    def handler(traversal: GraphTraversal, resolver_input: ResolverInput) -> Any:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = traversal_func(traversal, resolver_input)
        return traversal.next()

    return handler


def mutation_resolver(
        format: FormatFunction = format_value_map,
        select: TraversalSelectionFunction = select_current_vertex
) -> Callable:

    def wrapper(traversal_func: TraversalResolverFunction) -> ResolverFunction:

        @functools.wraps(traversal_func)
        def handler(traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:

            traversal = traversal_func(traversal, resolver_input)
            traversal = select(traversal)

            return format(traversal.next())

        return handler

    return wrapper
