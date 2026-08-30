# Test instructions

Tests must exercise observable behavior, not empty assertions or file existence alone. Fault injection must demonstrate a meaningful failure condition. Tests are offline, never mutate real `state/`, use temporary directories/fixtures, and assert stable error identifiers or specific diagnostics.
