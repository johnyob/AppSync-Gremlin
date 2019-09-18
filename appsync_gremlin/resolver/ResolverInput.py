from typing import Optional, Dict


class ResolverInput:

    def __init__(self, type_name: str, field_name: str, arguments: Dict, identity: Optional[Dict], source: Optional[Dict]):
        """
        Resolver Input Constructor

        :param type_name: The type name of the enclosing GraphQL type. (str)
        :param field_name: The field name of the field in the enclosing GraphQL type. (str)
        :param arguments: $context.arguments (dict)
        :param identity: $context.identity (dict|None)
        :param source: $context.source (dict|None)
        :returns
        """

        self._type_name = type_name
        self._field_name = field_name
        self._arguments = arguments
        self._identity = identity
        self._source = source

    @property
    def type_name(self) -> str:
        """

        :return:
        """

        return self._type_name

    @property
    def field_name(self) -> str:
        """

        :return:
        """

        return self._field_name

    @property
    def arguments(self) -> Dict:
        """

        :return:
        """

        return self._arguments

    @property
    def identity(self) -> Optional[Dict]:
        """

        :return:
        """

        return self._identity

    @property
    def source(self) -> Optional[Dict]:
        """

        :return:
        """

        return self._source
