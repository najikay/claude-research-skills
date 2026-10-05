# Privacy

Research Desk is a set of instructions (skills) for Claude, plus a small reference checker that runs on your own machine. This page says what that means for your data.

## What Research Desk collects

Nothing. There is no tracking and no account. Its author receives no data from your use of it: not your drafts, not your references, not your conversations, not the fact that you used it.

## What it reads

When you use a skill, Claude reads what you put into the conversation: your draft, your bibliography, the papers and notes you share. Research Desk only tells Claude how to work with them.

## What leaves your machine or your conversation

- **Your conversation** is handled by Anthropic under the terms and privacy policy of the Claude product you are using. Research Desk does not change that.
- **The reference checker** (Claude Code and Cowork only) sends a reference's title, DOI or arXiv id, or a few search words, to two public, keyless services: OpenAlex (`api.openalex.org`) and arXiv (`export.arxiv.org`). They see your IP address and the query, as with any request. The checker never receives your draft; it stores nothing and writes no files.
- **In the Claude apps**, where the checker does not run, the citation skill looks references up through Claude's web search: the same kind of query (a title, a DOI, an arXiv id) goes to the search provider. The related-work skill may search a topic phrase for a missing citation.
- The skills instruct Claude never to put sentences from your draft, or a description of your unpublished work, into a search.

## What you can do

- Use the skills without web search and without the checker: references are then marked `unchecked` and nothing is looked up.
- Delete a conversation in Claude to remove it, under the terms of your Claude product.

## Contact

Questions or concerns: open an issue at https://github.com/najikay/claude-research-skills/issues

Last updated: 2026-10-06.
