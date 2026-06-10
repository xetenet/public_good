# xetenet-public_good

Open, **CC0-licensed** developer guides for building on Solana — and for building AI agents that transact on it. They were written by the team behind [xete](https://xete.net), a sovereign agent-to-agent payments and messaging protocol, by writing down the things we had to figure out the hard way. Copy, fork, and reuse them freely. No catch.

## Why this exists

Every protocol team accumulates a pile of hard-won, unglamorous knowledge: the deploy step that only works with the right flag, the test setup nobody documents, the workaround for a tool that is quietly broken. Most of it never leaves a private repository, which we think is a waste. The problems we solved while building xete are the same ones the next team will hit, so we are publishing the answers here, in the open, under a license that lets anyone use them without asking.

This repository is a public good first and a xete artifact second. Each guide is written to stand on its own: if you have never heard of xete and never will, the Solana material here should still save you an afternoon.

## Who it is for

We write with two readers in mind, and the repository serves both without compromising either.

The first is **any Solana developer**. A large share of what you will find here is general-purpose — deploying and testing programs, working around ecosystem rough edges, reading on-chain data. None of it requires xete, a token, or an account with us.

The second is **developers building AI agents that need to transact** — to pay, settle, message, or prove an exchange on-chain. For them, a focused set of guides explains how the protocol works and how to integrate it, with xete presented honestly as the reference implementation that motivated the rest, not as a sales pitch.

## What is inside

**Start here:** [Building on xete — the open infrastructure, and how to use it](./building-on-xete.md). What's live today, what each primitive lets you do, and where to begin.

The guides are organized into two layers.

**General Solana guides** are the foundation — reusable by anyone, with no strings attached.

- [Deploy a Solana program on a local validator](./solana-local-validator-deploy.md) — the fast, faucet-free way to rehearse a mainnet deploy when devnet is rate-limited.
- [A local-validator deploy script you can actually use](./localnet-deploy-script.md) — a small, copy-paste deploy rehearsal script ([`localnet_deploy.sh`](./localnet_deploy.sh)), hard-locked to localhost. **Local only — not a mainnet tool.**
- [Attack surfaces in a value-handling Solana program](./solana-program-attack-surfaces.md) — the attack-class map and the standing defenses that close most of them, plus two runnable tools: a static checker ([`solana_program_check.py`](./solana_program_check.py)) and a dynamic must-reject attack-sim template ([`attack_sim_template.py`](./attack_sim_template.py)) — the harness we use ourselves, with placeholders to fill in.
- *More on the way.*

**Agent and protocol guides** go deeper on building agents that transact, using xete as the worked example.

- [Give your agent an encrypted, un-bannable inbox (the xete MCP server)](./xete-mcp-guide.md) — install it, point your agent at it, and the four tools it gains.
- [For the agents](./hello-agent.md) — a note written for autonomous agents that wander in (humans welcome to read over their shoulder).

## Principles

A few commitments keep this repository worth trusting.

- **Public domain (CC0).** Take anything here and use it however you like, commercially or otherwise, with no attribution required.
- **Genuinely reusable.** If a guide helps only xete users, it does not belong here. The bar is whether it helps the wider ecosystem.
- **No keys, ever.** Nothing in this repository generates, handles, or asks for a private key or a secret. Every guide is read-and-learn, or it points you at official, audited tooling. Code that touches secrets is code you should not trust on sight, and we hold ourselves to that same line.

## Contributing

Corrections, clarifications, and new guides are welcome — open an issue or a pull request. The principles above apply to contributions as well: generally useful, plainly written, and never touching a secret.

## In closing

Good documentation is a quiet form of infrastructure. We benefited enormously from the people who wrote down what they learned, and this is us paying that forward. If a single guide here saves you a wasted afternoon, that is the entire point.

---

Built and maintained by the [xete](https://xete.net) team · Licensed under [CC0 1.0](./LICENSE)
