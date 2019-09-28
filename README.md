# AppSync - Gremlin

## Overview

Through the AppSync-Gremlin, developers can write powerful queries in GraphQL without having to worry
too much about the underlying database query language in AWS Neptune. The AppSync-Gremlin provides
lambda function code that converts query operation types (from GraphQL) to a gremlin traversal.

## Definitions


- **Property field**: A field corresponding to a property of a vertex in the AWS Neptune graph database. In the below example,
  the `name` field is a property field.
  ```
  {
    User {
        name
        following {
            name
        }
    }
  }
  ```
  > Query 1 : (Vertex Field Example)

- **Vertex field**: A field corresponding to a vertex in the AWS Neptune graph database. In the above example,
  `location` is a vertex field.

- **Vertex list fields**: A field corresponding to a list of vertices in the AWS Neptune graph database. In the above example,
  `following` is a vertex list field.

- **Result set**: An assignment of vertices in the graph to fields in the query. As the database processes the query, new
  result sets may be created (e.g. when traversing edges), and result sets may be discarded when they do not satisfy filters.
  After all parts of the query are processed by the database, all remaining result sets are used to form the query result, by taking their values at all
  properties marked for output (anything in an output scope).

- **Scope**: The part of a query between any pair of parentheses or curly braces. We often refer to the parts between parentheses as the
  *input scope* and the parts between curly braces as the *output scope* or *payload scope*.
  For example, consider the query
  ```
  {
    User (
        input: {
            name: {
                eq: "John"
            }
        }
    ) {
        name
        following {
            name
        }
    }
  }
  ```
  > Query 2 : (Scope Example)

## Filtering Operations and Pagination


### Filtering

We define a filtering standard on the following scalar fields:

- **ID**:
  For ID filtering we define the following input for filtering:
  ```
  input IDFilterInput {
    ne: ID
    eq: ID

    in: [ID!]
    not_in: [ID!]
  }
  ```
- **String**: For String filtering we define the following input for filtering
  ```
  input StringFilterInput {
    ne: String
    eq: String

    in: [String!]
    not_in: [String!]

    contains: String
    not_contains: String

    begins_with: String
    not_begins_with: String

    ends_with: String
    not_ends_with: String
  }
  ```
- **Int**: For Integer filtering we define the following input for filtering
  ```
  input IntFilterInput {
    ne: Int
    eq: Int
    le: Int
    lt: Int
    ge: Int
    gt: Int

    in: [Int!]
    not_in: [int!]
  }
  ```
- **Float**: For Float filtering we define the following input for filtering
  ```
  input FloatFilterInput {
    ne: Float
    eq: Float
    le: Float
    lt: Float
    ge: Float
    gt: Float

    in: [Float!]
    not_in: [Float!]
  }
  ```
- **Boolean**: For Boolean filtering we define the following input for filtering
  ```
  input BooleanFilterInput {
    eq: Boolean
    ne: Boolean
  }
  ```
- **DateTime**: For DateTime we first have to define our own DateTime input definition. To avoid confusion and to prevent the use of different DateTime formats
  in this interface, we have defined the following `DateTimeInput` to expose the individual date components (such as day, month, year, etc) as well
  as a `formatted` field which is the ISO 8601 string representation of the DateTime value:
  ```
  input DateTimeInput {
    year: Int
    month: Int
    day: Int
    hour: Int
    minute: Int
    second: Int
    formatted: DateTime #custom datetime scalar
  }
  ```
  Using this input definition, we can then create the following input for filtering:
  ```
  input DateTimeFilterInput {
    eq: DateTimeInput
    ne: DateTimeInput

    in: [DateTimeInput!]
    not_in: [DateTimeInput!]

    le: DateTimeInput
    lt: DateTimeInput
    ge: DateTimeInput
    gt: DateTimeInput
  }
  ```

and a filtering standard on enum types:
```
enum ENUM_FIELD_TYPE {
    E_1
    E_2
    .
    .
    .
    E_n
}

input EnumFilterInput {
    eq: ENUM_FIELD_TYPE
    ne: ENUM_FIELD_TYPE
    in: [ENUM_FIELD_TYPE!]
    not_in: [ENUM_FIELD_TYPE!]
}
```

Note that these standards must be manually implemented in the original GraphQL schema. In future we may devise some method of augmenting a GraphQL schema
so we don't have to manually implement them.

Each of these scalar filters has a corresponding filter in the AppSync-Gremlin library. For example, the `StringFilterInput` has
the scalar filter `string_filter`, etc.

#### Implementing Filters

The AppSync-Gremlin library also allows custom `vertex`, `relationship` and `scalar` filters to be implemented.
 
- **Scalar filters**: We define a `scalar` filter as a filter that maps GraphQL fields to Gremlin predicates. Consider an `id_filter`. 
  In GraphQL, the `IDFilterInput` has the following fields: `eq, ne, in, not_in`. The Gremlin predicates that correspond to these fields are 
  `eq, neq, within, without`. So we construct the following dictionary to map the GraphQL fields to the Gremlin predicates:
  ```python
  from gremlin_python.process.traversal import eq, neq, within, without
  
  def id_scalar_filter():
      return {
          "eq": eq,
          "ne": neq,
          "in": within,
          "not_in": without
      }
  ```
  By using this dictionary, we can construct a filter function that applies the predicates to some traversal `g`, such that the traverser is 
  at some vertices `v` with property `property_name`, 
  producing a filtered traversal with the general form ,
  
        `g' = g.has(property_name, p_1).has(property_name, p_2). ... .has(property_name, p_n)`,
  
  where `p_1, p_2, ..., p_n` are predicates that are applied to the property `property_name` at `v`. 
  
  The `@scalar_filter` decorator provided by the AppSync-Gremlin library produces a function that takes a `property_name`
  and returns the function described above. So by applying this to the above `id_filter` gives us
  ```python
  from gremlin_python.process.traversal import eq, neq, within, without
  from appsync_gremlin import scalar_filter
  
  @scalar_filter
  def id__filter():
      return {
          "eq": eq,
          "ne": neq,
          "in": within,
          "not_in": without
      }
  ```
  However, at this stage the filter cannot actually be used, since it requires a `property_name`. The AppSync-Gremlin library
  provides two different ways of applying a `property_name` to a filter. Either we can simply call `id_scalar_filter`
  with out desired `property_name`, or we can apply the `@name` decorator. 
  
  For scalar filters, we advice that the former is used. Since this provides a better generalisation for your scalar filter. 
  Since a vertex could implement it's own custom id with property name `"id"` or simply make use of the built in vertex id
  `T.id`. 
  
- **Vertex filter**: We define a `vertex` filter as a filter that maps GraphQL fields to `scalar` or `relationship` (see below) filters.
  Let us consider the following GraphQL `User` type:
  ```
  type User {
      id: ID!
      email: String!
        
      name: String
      about: String
        
      following: [User]!
      followed_by: [User]!
  }
  ```
  We have 4 scalar fields (`id, email, name, about`) and 2 vertex list fields (`following, followed_by`). In the Graph database, we define 
  a `User` vertex with properties `email, name, about` (string) and a single relationship `User -> FOLLOWS -> User`. So in a similar fashion to 
  a scalar filter, let us define some function that returns a dictionary mapping the GraphQL fields to filters:
  ```python
  from gremlin_python.process.traversal import T  
  from appsync_gremlin import id_filter, string_filter

  def user_filter():
      return {
          "id": id_filter(T.id),
          "email": string_filter("email"),
          "name": string_filter("name"),
          "about": string_filter("about"),
          "following": ?,
          "followed_by": ?
      }
  ```
  By using this dictionary we can construct a filter function that applies the `scalar` and `relationship` filters to some 
  supplied traversal `g`, such that the traverser is at some vertices `v` which matches the desired filter (in this case the travesers must all be at `User` vertices),
  producing a filtered traversal `g'` with the general form:
  
        g' = r_1(r_2( ... (r_n(s_1( ... s_m(g) ... ))) ... ))
  
  where `r_1, r_2, ..., r_n` are relationship filters and `s_1, s_2, ..., s_m` are scalar filters. Note that the order of application of scalar and relationship
  filters does not matter, however, we advice that scalar filters should be applied first as it is more efficient. 

  The `@vertex_filter` decorator provided by the AppSync-Gremlin library produces a function that takes a `vertex_label`
  and returns the function described above. So by applying this to the above `user_filter` gives us
  ```python
  from gremlin_python.process.traversal import T
  from appsync_gremlin import id_filter, string_filter, vertex_filter, name

  @name("User")
  @vertex_filter
  def user_filter():
      return {
          "id": id_filter(T.id),
          "email": string_filter("email"),
          "name": string_filter("name"),
          "about": string_filter("about"),
          "following": ?,
          "followed_by": ?
      }
  ```
  Similarly to the `scalar_filter`, we can apply the `@name` decorator to pass the `vertex_label` to the filter function. 
  This label should match the label of the `User` vertex in the Graph database.
   
  With the vertex filter now completely implemented, we can now define our relationship filters (see below). In this case 
  we have the relationship filters:
  ```python
  from gremlin_python.process.traversal import T  
  from appsync_gremlin import id_filter, string_filter, vertex_filter, name, relationship_filter, RelationshipDirection

  @name("User")
  @vertex_filter
  def user_filter():
      return {
          "id": id_filter(T.id),
          "email": string_filter("email"),
          "name": string_filter("name"),
          "about": string_filter("about"),
          "following": relationship_filter(("FOLLOWS", RelationshipDirection.OUT), user_filter),
          "followed_by": relationship_filter(("FOLLOWS", RelationshipDirection.IN), user_filter)
      }
  ```
  
- **Relationship filter**: We define a relationship `R` from some vertex `u` to `v` as `R = (name, direction)`. We can 
  filter `u` based on the whether a relationship `R` exists and whether `v` satisfies certain conditions. 
  
  Consider a Gremlin traversal `g`, such that the traverser is at some vertices `u`. We can produce a filtered traversal
  `g'` based on whether the vertices selected by `g` have the relationship `R` and the vertices `v` (the other vertex in `R`) satisfy
  a vertex filter `v_f`. This filtered traversal has the general form:
  
        g' = g.where(v_f(direction(name))).
  
  The AppSync-Gremlin library produces a function `relationship_filter` that takes a `relationship`, a tuple consisting of a 
  edge label (`name`) and a edge direction (`direction`), and a vertex filter `v_f` for the other vertex in the relationship. 
  
  (See above for example). 
  
  
### Pagination

We also implement a pagination standard. Note that pagination can only be applied to vertex list fields. 
 
 For simplicity, we've decided to implement an offset based pagination, as it allows us to make us
of the Gremlin traversal step `.range(first, offset)`. The stanardised pagination input is defined as follows:
```
input PaginationInput {
  page: Int!
  per_page: Int!
}
```
We then use `page` and `per_page` to compute `first` and `offset` using the function `get_range`, shown below.
```python
from typing import Tuple

def get_range(page: int, per_page: int) -> Tuple[int, int]:
    """
    Returns the Gremlin range from page options in the format:
        (first, last)

    :param page: (Integer)
    :param per_page: (Integer)
    :return: (Integer, Integer)
    """

    return (page - 1) * per_page, page * per_page
```

Once the traversal has been submitted and the result set has been return, we format the response into a pagination
response object. The GraphQL type for this response object for some GraphQL type `Type` is
```
type Type {
    .
    .
    .
}

type TypePage {
    data: [Type]!
    page: Int!
    per_page: Int!
    total: Int!
}
```
where `total` is the `total` number of pages available.

## Error Handling and Request / Response Mapping Template

The AppSync-Gremlin library provides automatic error handling for AppSync. The library does this via the user of the `AppSyncException`.
The `AppSyncException` requires 3 arguments when instantiated: `error_type`, `error_message` and `error_data` for type
 string, string and dictionary respectively.

For example, consider the mutation resolver that creates a `User` vertex. Naturally we want to ensure that a user doesn't have a duplicate vertex,
therefore we must add some form of validation within the resolver code which raises an `AppSyncException` with the relevant error information
if the validation fails.

```python
from gremlin_python.process.graph_traversal import GraphTraversal
from appsync_gremlin import ResolverInput, AppSyncException, mutation_resolver

@mutation_resolver
def create_user(traversal: GraphTraversal, resolver_input: ResolverInput) -> GraphTraversal:

    username = resolver_input.arguments.get("username")
    user = traversal.V().hasLabel("User").has("username", username)

    if user.hasNext():
        raise AppSyncException(
            error_type="BAD_REQUEST",
            error_message="A user with username {} is already stored in the AWS Neptune database.".format(username),
            error_data={
                "username": username
            }
        )

    .
    .
    .
```

In order to ensure our `AppSyncException` work's with AppSync, we've had to define a request / response template mapping standard.
For all resolvers, we must have the request template mapping:
```
{
  "version" : "2018-05-29",
  "operation": "(Invoke|BatchInvoke)",
  "payload": {
    "type_name": String!,
    "field_name": String!,
    "arguments": $util.toJson($context.args),
    "identity": $util.toJson($context.identity),
    "source": $util.toJson($context.source)
  }
}
```
and the response mapping template:
```
#if ($context.result && $context.result.error)
    $utils.error($context.result.error.error_message, $context.result.error.error_type, $context.result.error.data)
#else
    $utils.toJson($context.result.data)
#end
```

### Usage

The AppSync-Gremlin library currently provides 4 different resolver types in the form of function decorators:
- `vertex_list_field_resolver`
- `vertex_field_resolver`
- `calculated_field_resolver`
- `mutation_resolver`

The first 3 resolvers are Query based resolvers, that is to say they are designed to be used for resolving GraphQL
queries. 

Each resolver has the same function type signature:

    resolver : (GraphTraversal, ResolverInput) -> GraphTraversal

Note the custom `ResolverInput` object. A `ResolverInput` object simply stores the data passed from the Apache VTL 
request mapping template described in the section above. Hence the `ResolverInput` object has the following properties:
 - `type_name`: `(String)`
 - `field_name`: `(String)`
 - `arguments`: `(Dictionary)`
 - `identity` : `(Dictionary | None)`
 - `source`: `(Dictionary | None)`

Hence these properties can be referenced in the resolvers to build the Gremlin traversals. 