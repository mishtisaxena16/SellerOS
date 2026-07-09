from retrieve import semantic_search

results = semantic_search(
    "How do I register for GST?"
)

from pprint import pprint
pprint(results)