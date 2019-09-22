from typing import Dict, Any, Callable, Optional, Union, List, Tuple
from logging import Logger

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversal
from gremlin_python.process.anonymous_traversal import traversal

from appsync_gremlin.resolver.Resolver import ResolverFunction
from appsync_gremlin.resolver.ResolverInput import ResolverInput
from appsync_gremlin.helpers.Exceptions import AppSyncException


class AppSync:

    def __init__(self, connection_config: Dict, logger: Optional[Logger] = None):
        """

        """

        self._connection_method = connection_config.get("connection_method")
        self._neptune_cluster_endpoint = connection_config.get("neptune_cluster_endpoint")
        self._neptune_cluster_port = connection_config.get("neptune_cluster_port")
        self._logger = logger

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

    def add_resolver(self, resolver_identifier: Tuple[str, str], resolver: ResolverFunction) -> None:
        """

        :param resolver:
        :return:
        """

        self._resolvers[resolver_identifier] = resolver

    def _handle_resolver(self, resolver_input: ResolverInput) -> Any:

        if self._logger:
            self._logger.info("The resolver input is {}".format(str(resolver_input)))

        resolver = self._resolvers[(resolver_input.type_name, resolver_input.field_name)]
        try:
            response = resolver(self._get_traversal(), resolver_input)
        except Exception as error:
            raise AppSyncException(error) from error

        if self._logger:
            self._logger.info("The resolver response is {}".format(str(response)))

        return response

    def lambda_handler(self) -> Callable:
        """

        :return:
        """

        def handler(payload: Union[Dict,List], context: Any) -> Any:
            """
            The handler for an AppSync application using AWS Lambda either takes a
            payload dictionary or a payload list.

            The payload is a dictionary <=> the operation "Invoke" is used on the Lambda function.
            The payload is a list <=> the operation "BatchInvoke" is used on the Lambda function.

            We will use these two cases to decide how we handle our resolvers.

            :param payload: (list|dict)
            :param context: (Any)
            :return: (Any)
            """

            # If the BatchInvoke operation is used.
            if isinstance(payload, list):

                return [
                    self._handle_resolver(ResolverInput(
                        type_name=resolver_input.get("type_name"),
                        field_name=resolver_input.get("field_name"),
                        arguments=resolver_input.get("arguments"),
                        identity=resolver_input.get("identity"),
                        source=resolver_input.get("source")
                    ))
                    for resolver_input in payload
                ]

            # If the Invoke operation is used
            return self._handle_resolver(ResolverInput(
                type_name=payload.get("type_name"),
                field_name=payload.get("field_name"),
                arguments=payload.get("arguments"),
                identity=payload.get("identity"),
                source=payload.get("source")
            ))

        return handler
