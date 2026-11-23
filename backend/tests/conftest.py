"""Keep unit tests isolated from the developer's local .env services."""
import os

# The developer .env may point the API at a live Neo4j instance. Graph API
# tests use fixture CSV data; Neo4j query behavior is covered by mocked driver
# tests that explicitly select the neo4j adapter. Never import/write live data
# as a side effect of the ordinary unit suite.
os.environ["GRAPH_SOURCE"] = "csv"
