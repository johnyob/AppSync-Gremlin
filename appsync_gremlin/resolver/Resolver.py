from typing import Dict, Any, List, Tuple, Optional, Callable
from datetime import datetime
from math import ceil
import functools

from gremlin_python.process.graph_traversal import GraphTraversal, unfold, __
from gremlin_python.process.traversal import T

from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.filter.Filter import TraversalFilterFunction


### Helpers


def format_key(key: Any) -> Any:
    """

    :param key:
    :return:
    """

    if isinstance(key, T):
        return key.name

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


### Types


TraversalResolverFunction = Callable[[GraphTraversal, ResolverInput], GraphTraversal]
VertexListFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Dict]
VertexFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Optional[Dict]]
CalculatedFieldResolverFunction = Callable[[GraphTraversal, ResolverInput], Any]
ResolverFunction = Callable[[GraphTraversal, ResolverInput], Any]


### Resolvers


def vertex_list_field_resolver(filter_func: TraversalFilterFunction) -> Callable:
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

            response_and_total = filter_func(traversal, input_dict).valueMap(True).\
                by(unfold()).fold().project("data", "total").select("data", "total").\
                by(__.unfold().range(first, last).fold()).by(__.unfold().count()).next()

            response = [format_value_map(value_map) for value_map in response_and_total.get("data")]

            return paginate(response, page, per_page, response_and_total.get("total"))

        return handler

    return wrapper


def vertex_field_resolver(traversal_func: TraversalResolverFunction) -> VertexFieldResolverFunction:
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

        traversal = traversal_func(traversal, resolver_input).valueMap(True).by(unfold())

        if traversal.hasNext():
            return format_value_map(traversal.next())

        return None

    return handler


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


def mutation_resolver(traversal_func: TraversalResolverFunction) -> ResolverFunction:

    @functools.wraps(traversal_func)
    def handler(traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:

        traversal = traversal_func(traversal, resolver_input).valueMap(True).by(unfold())

        return format_value_map(traversal.next())

    return handler
