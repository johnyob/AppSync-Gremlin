from abc import ABC as Abstract, abstractmethod, abstractproperty
from typing import Dict, Any
from enum import Enum

from gremlin_python.process.graph_traversal import GraphTraversal, out, in_


class RelationshipDirection(Enum):
    """
    Edge relationship direction. Supported options are IN and OUT.
    """

    IN = 0
    OUT = 1


RELATIONSHIP_DIRECTION_MAP = {
    RelationshipDirection.IN: in_,
    RelationshipDirection.OUT: out
}


class AbstractFilter(Abstract):

    @abstractproperty
    def sub_filters(self) -> Dict[str, Any]:
        """
        Returns the sub-filters of a given filter. Consider the FilterInput:
            input UsersFilterInput {
                id: IDFilterInput
                email_address: StringFilterInput

                name: StringFilterInput
                phone: StringFilterInput
                about: StringFilterInput

                deleted: BooleanFilterInput
                disabled: BooleanFilterInput
            }

        This class would implement the application of the UserFilterInput input type and
        has the sub-filters:
            - id
            - email_address
            - name
            - phone
            - about
            - deleted
            - disabled

        Each with their own AbstractFilter implementation. The application of sub filters is key for our
        recursive design of filter application.

        :return: (Dict)
        """

        pass

    @abstractmethod
    def apply_filter(self, traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
        """
        This is the method that the filter uses to apply itself onto a given Gremlin traversal with data provided by
        the input dictionary. At this stage we can simply apply predicates to the traversal, or we can apply more
        AbstractFilters depending on the structure of the related input type in the GraphQL Schema.

        :param traversal: (GraphTraversal)
        :param input_dict: (Dict)
        :return: (GraphTraversal)
        """

        pass


class ScalarFilter(AbstractFilter):

    def __init__(self, field_name: str):
        """
        This method instantiates a scalar filter instance. We define a scalar filter as a filter who's sub-filters
        are predicates.

        :param field_name: (str)
        """

        self._field_name = field_name

    def apply_filter(self, traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
        """
        This method applies the predicates to the traversal using data from the input dictionary.
        We use the .has traversal set, so our traversal g will be in the form:

            g.has(field_name, p_1).has(field_name, p_2). ... .has(field_name, p_n)


        :param traversal: (GraphTraversal)
        :param input_dict: (Dict)
        :return: (GraphTraversal)
        """

        for predicate_name, value in input_dict.items():
            predicate = self.sub_filters.get(predicate_name)
            traversal = traversal.has(self._field_name, predicate(value))

        return traversal


class VertexFilter(AbstractFilter):
    """
    The VertexFilter class is designed to implement the sub filters of a given vertex input type such as:
        input UsersFilterInput {
            id: IDFilterInput
            email_address: StringFilterInput

            name: StringFilterInput
            phone: StringFilterInput
            about: StringFilterInput

            deleted: BooleanFilterInput
            disabled: BooleanFilterInput
        }

    The apply_filter method of this class applies the ScalarFilters / RelationshipFilters to the traversal.
    """

    @abstractproperty
    def vertex_label(self) -> str:
        """
        Returns the Vertex label of the vertex that the filter implements. For example the UsersFilterInput would
        implement a filter on vertices with vertex label "User".

        :return: (str)
        """

        pass

    def apply_filter(self, traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
        """
        This method applies the various relationship and scalar filters to the traversal.

        :param traversal: (GraphTraversal)
        :param input_dict: (Dict)
        :return: (GraphTraversal)
        """

        for field_name, filter_input in input_dict.items():
            traversal = self.sub_filters.get(field_name).apply_filter(traversal, filter_input)

        return traversal


class RelationshipFilter(VertexFilter):
    """
    This RelationshipFilter class is designed to implement filters on given relationships. When implementing these
    relationship filters we must inherit the RelationshipFilter class along with the related VertexFilter implementation.

    For example consider the following input type on Users:
        input UsersFilterInput {
            id: IDFilterInput
            following: UsersFilterInput
        }

    We implement the UsersVertexFilter as
        class UsersVertexFilter(VertexFilter):

            @property
            def sub_filters(self):
                return {
                    "id": IDScalarFilter("id"),
                    "following": FollowingRelationshipFilter()
                }

    we then implement the FollowingRelationshipFilter as

        class FollowingRelationshipFilter(RelationshipFilter, UsersVertexFilter):

            @property
            def relationship_direction(self):
                return RelationshipDirection.OUT

            @property
            def relationship_name(self):
                return "FOLLOWING"

    """

    @abstractproperty
    def relationship_direction(self) -> RelationshipDirection:
        """
        Returns the relationship direction of the relationship that the RelationshipFilter implements.

        :return: (RelationshipDirection)
        """

        pass

    @abstractproperty
    def relationship_name(self) -> str:
        """
        Returns the relationship name of the relationship that the RelationshipFilter implements.

        :return: (str)
        """

        pass

    def apply_filter(self, traversal: GraphTraversal, input_dict: Dict) -> GraphTraversal:
        """
        This method first creates a traversal in the form:
            g' = (out|in)(relationship_name).hasLabel
        We then apply the respective vertex filter to this traversal.
        Using our original traversal g, we then return

            g.where(g')

        :param traversal: (GraphTraversal)
        :param input_dict: (Dict)
        :return: (GraphTraversal)
        """

        traversal_ = RELATIONSHIP_DIRECTION_MAP[self.relationship_direction](self.relationship_name).\
            hasLabel(self.vertex_label)
        traversal_ = super().apply_filter(traversal_, input_dict)

        return traversal.where(traversal_)


