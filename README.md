# AppSync - Gremlin

## Overview

Through the AppSync-Gremlin, developers can write powerful queries in GraphQL without having to worry
about the underlying database query language in AWS Neptune. The AppSync-Gremlin provides
lambda function code that converts query operation types (from GraphQL) to a gremlin traversal.

Furthermore, the library validates the queries through the user of a GraphQL schema that
specifies the underlying schema of the AWS Neptune database.


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

### Pagination

Not implemented yet - TODO.

### Request Mapping Template

Use the Apache VTL
```
{
  "version" : "2017-02-28",
  "operation": "Invoke",
  "payload": {
    "type_name": String!,
    "field_name": String!,
    "arguments": $util.toJson($context.args),
    "identity": $util.toJson($context.identity),
    "source": $util.toJson($context.source)
  }
}
```

### Usage

TODO
