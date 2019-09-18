from abc import ABC as Abstract, abstractmethod, abstractproperty
from typing import Dict, Any, List

from gremlin_python.process.graph_traversal import GraphTraversal, unfold
from gremlin_python.process.traversal import T

from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.filter.Filter import apply_filters


def format_key(key: Any) -> Any:
    """

    :param key:
    :return:
    """

    if isinstance(key, T):
        return key.name

    return key


def format_value_map(value_map: Dict) -> Dict:
    """

    :param value_map:
    :return:
    """

    return {
        format_key(k): v for k, v in value_map.items()
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

    def format_response(self, response: List[Dict]) -> List[Dict]:
        """
        Iterates through the response list, applying format_value_map on the value map. This serializes the value map
        into something that can be returned by a AWS Lambda function.

        :param response: (list)
        :return: (list)
        """

        return [format_value_map(value_map) for value_map in response]

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> List[Dict]:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        input_dict = resolver_input.arguments.get("input", {})

        traversal = self.get_traversal(traversal, resolver_input)

        return self.format_response(apply_filters(traversal, input_dict).valueMap().by(unfold()).toList())


class VertexFieldResolver(AbstractResolver):

    def format_response(self, response: Dict) -> Dict:
        """
        Applies the format_value_map function to the response dict (a value map).

        :param response: (dict)
        :return: (dict)
        """

        return format_value_map(response)

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = self.get_traversal(traversal, resolver_input).valueMap().by(unfold())

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
