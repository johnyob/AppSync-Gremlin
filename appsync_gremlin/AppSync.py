from typing import Dict, Any, Callable

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.anonymous_traversal import traversal

from appsync_gremlin.resolver.AbstractResolver import AbstractResolver
from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.helpers.Exceptions import AppSyncException



class AppSync:

    def __init__(self, connection_config: Dict):
        """

        """

        self._connection_method = connection_config.get("connection_method")
        self._neptune_cluster_endpoint = connection_config.get("neptune_cluster_endpoint")
        self._neptune_cluster_port = connection_config.get("neptune_cluster_port")

        self._resolvers = {}

    def _get_traversal(self) -> GraphTraversal:
        """

        :return:
        """

        remote_connection = DriverRemoteConnection("{0}://{1}:{2}/gremlin".format(
            self._connection_method,
            self._neptune_cluster_endpoint,
            self._neptune_cluster_port
        ), "g")

        return traversal().withRemote(remote_connection)

    def add_resolver(self, resolver: AbstractResolver):
        """

        :param resolver:
        :return:
        """

        self._resolvers[(resolver.type_name, resolver.field_name)] = resolver

    def lambda_handler(self) -> Callable:
        """

        :return:
        """

        def handler(event: Dict, context: Any) -> Any:

            resolver_input = ResolverInput(
                type_name=event.get("type_name"),
                field_name=event.get("field_name"),
                arguments=event.get("arguments"),
                identity=event.get("identity"),
                source=event.get("source")
            )

            resolver = self._resolvers[(resolver_input.type_name, resolver_input.field_name)]
            try:
                response = resolver.handle(self._get_traversal(), resolver_input)
            except Exception as error:
                raise AppSyncException(error) from error

            return response

        return handler
