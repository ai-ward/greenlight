# Greenlight — Day 5 notes

## Two different problems, not one

"Make this go viral" is actually two separate questions: can people find
it, and is there a real reason for them to care once they do. Spent
today on both, deliberately not on more speculative features.

## Discoverability (cheap, done)

* GitHub topics: `mcp`, `model-context-protocol`, `cli`, `debugging`,
  `developer-tools`, `proxy`. Repo had none set -- meant it wouldn't
  surface at all for someone browsing by topic, regardless of quality.
* README badges: PyPI version, Python version, license. Small, but it's
  the first-three-seconds credibility signal for a stranger landing on
  the repo cold.

Neither of these took more than a few minutes. Worth doing before
spending more time on code, since a good repo nobody can find gets the
same number of stars as a mediocre one: zero.

## The actual feature: `greenlight stats`

The real "evergreen useful" work. Message counts, latency (min/median/max,
per-method), and a pass/fail verdict -- and critically, an exit code that
reflects that verdict. That last part is what makes this more than a
prettier `tail`: it means Greenlight can sit in a CI pipeline
(`greenlight stats || exit 1`) and fail a build when an MCP server's
tool calls are actually broken, not just when a human happens to be
watching a live trace.

That's the difference between a tool people watch and a tool people can
build automation around -- CI-usability is timeless in a way a slick demo
GIF isn't tied to any particular hype cycle.

## Verified both directions, not just the happy path

`tests/test_stats.py` checks the exit code against two real sessions: the
existing demo session (has a known tool failure -- asserts exit 1) and a
freshly recorded clean session (asserts exit 0). A stats command whose
exit code is only tested on the passing case isn't actually trustworthy
for CI use -- the whole point is the failing case, so that's the one that
had to be proven, not assumed.

## Explicitly not done today, on purpose

HTTP/SSE transport. Still no real signal (a user request, or hitting a
real HTTP/SSE server myself) that it's the right next scope. Distribution
and a genuinely useful CI-facing feature both mattered more than adding
transport support nobody's asked for yet.
