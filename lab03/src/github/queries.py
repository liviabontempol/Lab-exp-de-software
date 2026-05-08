"""GraphQL queries used by the data collectors."""

SEARCH_REPOSITORIES_QUERY = """
query($query: String!, $first: Int!, $after: String) {
  search(type: REPOSITORY, query: $query, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        owner { login }
        url
        stargazerCount
        primaryLanguage { name }
        pullRequests(states: [MERGED, CLOSED]) { totalCount }
      }
    }
  }
  rateLimit {
    remaining
    resetAt
    cost
  }
}
"""

PULL_REQUESTS_QUERY = """
query($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [MERGED, CLOSED], first: $first, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        state
        createdAt
        closedAt
        mergedAt
        changedFiles
        additions
        deletions
        bodyText
        participants { totalCount }
        comments { totalCount }
        reviews { totalCount }
      }
    }
  }
  rateLimit {
    remaining
    resetAt
    cost
  }
}
"""
