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
        location
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
        location
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
the scalar filter `string_filter`.

### Pagination

We also implement a pagination standard. For simplicity, we've decided to implement an offset based pagination, as it allows us to make us
of the Gremlin traversal step `.range(first, offset)`. The stanardised pagination input is defined as follows:
```
input PaginationInput {
  page: Int!
  per_page: Int!
}
```
We then use `page` and `per_page` to compute `first` and `offset` using the function `get_range`, shown below.
```python
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

$util.toJson($context.result)
```
### Usage

TODO
