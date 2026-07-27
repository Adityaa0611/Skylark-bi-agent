# Decision Log

## Key Assumptions
- "This quarter" and similar relative time phrases are interpreted using the
  calendar quarter unless the user clarifies otherwise; the agent asks for
  clarification when a question is ambiguous.
- Missing Masked Deal Value is treated as "unknown," not zero — excluded from
  sum/average calculations rather than counted as $0.
- Deal Stage's lettered prefixes (A–O) represent an ordered sales funnel; stage
  order is derived from these letters.
- Owner Code and Client Code are treated as opaque identifiers, not names, since
  no lookup table was provided.

## Trade-offs
- **Direct GraphQL API over MCP**: chosen for transparency and debuggability
  within a limited time window; MCP adds an abstraction layer that's harder to
  demo and inspect live during evaluation.
- **Groq (Llama 3.3 70B) over a paid LLM API**: chosen to keep the project free
  to run and reproduce, while Llama 3.3 70B is still strong enough for tool-use
  based query understanding at this scale.
- **Streamlit over a custom frontend**: prioritizes shipping a working, hosted
  conversational UI over visual polish, given the time constraint.
- **Tool-use based query understanding over a rules-based intent parser**: lets
  one mechanism handle ambiguity detection, clarifying questions, and filtering
  without separate bespoke logic for each question type.

## What I'd do differently with more time
- Build a small evaluation set of realistic founder questions to systematically
  test query understanding accuracy.
- Add a proper caching/sync layer instead of re-fetching monday.com data on
  every new session.
- Replace the static sector/category normalization dictionary with fuzzy
  matching to handle spelling variants automatically.
- Add unit tests for the `normalize.py` functions.
- Extend cross-board querying so questions spanning both Deals and Work Orders
  (e.g. win-rate, or delivery performance by sector) are fully supported end to end.

## Interpretation of "leadership updates"
Implemented as an on-demand executive summary generator: pulling top-line
pipeline value by sector, funnel stage distribution, and notable data gaps,
then asking the LLM to draft a short prose summary a founder could paste into
a leadership update — rather than a scheduled/automated report, given the
project's time constraints.