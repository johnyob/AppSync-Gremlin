from abc import ABC as Abstract, abstractmethod, abstractproperty
from typing import Dict, Any, List

from gremlin_python.process.graph_traversal import GraphTraversal, unfold

from appsync_gremlin.resolver.ResolverInput import ResolverInput


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

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> List[Dict]:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        input_dict = resolver_input.arguments.get("input", {})

        traversal = self.get_traversal(traversal, resolver_input)

        return apply_filters(traversal, input_dict).valueMap().by(unfold()).toList()


class VertexFieldResolver(AbstractResolver):

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Dict:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = self.get_traversal(traversal, resolver_input).valueMap().by(unfold())

        if traversal.hasNext():
            return traversal.next()

        return None


class CalculatedFieldResolver(AbstractResolver):

    def handle(self, traversal: GraphTraversal, resolver_input: ResolverInput) -> Any:
        """

        :param traversal:
        :param resolver_input:
        :return:
        """

        traversal = self.get_traversal(traversal, resolver_input)

        return traversal.next()