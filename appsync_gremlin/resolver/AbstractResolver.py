from abc import ABC as Abstract, abstractmethod, abstractproperty
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from gremlin_python.process.graph_traversal import GraphTraversal, unfold, __
from gremlin_python.process.traversal import T

from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.filter.AbstractFilter import AbstractFilter


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


class AbstractResolver(Abstract):

    @abstractproperty
    def type_name(self) -> str:
        """
        Returns the GraphQL type name of the enclosing GraphQL type.
        E.g. If the resolver is for the property email_address in the following GraphQL type:
            type User {
                id: ID
                email_address: String
            }
        then the type_name should be User

        :return: (String)
        """

        pass

    @abstractproperty
    def field_name(self) -> str:
        """
        Returns the GraphQL field name of the field in the enclosing GraphQL type.
        E.g. If the resolver is for the property email_address in the following GraphQl type:
            type User {
                id: ID
                email_address: String
            }
        then the field_name should be email_address

        :return: (String)
        """

        pass

    @abstractmethod
    def format_response(self, response: Any) -> Any:
        """
        This method is used for GremlinPython to JSON serialization. For example, when retrieving vertex
        id, GremlinPython returns a dict with an enum -> Any mapping. The enum cannot be serialized (in
        AWS Lambda) so we use this method to implement the required serialization.

        :param response: (Any)
        :return: (Any)
        """

        pass

    @abstractmethod
    def get_traversal(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> GraphTraversal:
        """
        Returns the Gremlin graph traversal for the resolver. This is implemented by the concrete class.

        :param traversal: This should be the initial traversal object returned by AppSync._get_traversal. (GraphTraversal)
        :param resolver_input: The resolver input object, used in creating the traversal as it
                               the arguments(ResolverInput)
        :return: (GraphTraversal)
        """

        pass

    @abstractmethod
    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Any:
        """
        Returns response from resolver. This is implemented by the concrete class or the abstract subclasses:
            - VertexFieldListResolver
            - VertexFieldResolver
            - CalculatedFieldResolver

        :param traversal:
        :param resolver_input: (ResolverInput)
        :return: (Any)
        """

        pass


class VertexListFieldResolver(AbstractResolver):

    def get_filter(self) -> AbstractFilter:
        """

        :return:
        """

        pass



    def _get_range(self, page: int, per_page: int) -> Tuple[int, int]:
        """
        Returns the Gremlin range from page options in the format:
            (first, last)

        :param page: (int)
        :param per_page: (int)
        :return: (int, int)
        """

        return (page - 1) * per_page, page * per_page

    def paginate(self, response: List[Dict], page: int, per_page: int, total: int) -> Dict:
        """

        :param response:
        :param page:
        :param per_page:
        :param total:
        :return:
        """

        return {
            "data": response,
            "page": page,
            "per_page": per_page,
            "total": total
        }

    def format_response(self, response: List[Dict]) -> List[Dict]:
        """
        Iterates through the response list, applying format_value_map on the value map. This serializes the value map
        into something that can be returned by a AWS Lambda function.

        :param response: (Dict)
        :return: (list)
        """

        return [format_value_map(value_map) for value_map in response]

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:
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

        first, last = self._get_range(page, per_page)

        traversal = self.get_traversal(traversal, resolver_input)

        response_and_total = self.get_filter().apply_filter(traversal, input_dict).valueMap(True).\
            by(unfold()).fold().project("data", "total").select("data", "total").\
            by(__.unfold().range(first, last).fold()).by(__.unfold().count()).next()

        response = self.format_response(response_and_total.get("data"))

        return self.paginate(response, page, per_page, response_and_total.get("total"))


class VertexFieldResolver(AbstractResolver):

    def format_response(self, response: Dict) -> Dict:
        """
        Applies the format_value_map function to the response dict (a value map).

        :param response: (dict)
        :return: (dict)
        """

        return format_value_map(response)

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Optional[Dict]:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = self.get_traversal(traversal, resolver_input).valueMap(True).by(unfold())

        if traversal.hasNext():
            return self.format_response(traversal.next())

        return None


class CalculatedFieldResolver(AbstractResolver):

    def format_response(self, response: Any) -> None:
        """
        No formatting required for calculated fields.

        :param response: (Any)
        :return: (None)
        """

        return None

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Any:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = self.get_traversal(traversal, resolver_input)

        return traversal.next()
