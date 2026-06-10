# Deploy a Solana program on a local validator — the fast fix when the devnet faucet is rate-limited

Searching for **"devnet faucet not working"**, **"solana airdrop rate limit / 429"**, **"how to get devnet SOL to deploy a program"**, or **"test a Solana program without devnet"**? Skip the faucet. Run a **local Solana validator** (`solana-test-validator`) with **unlimited, instant SOL**, deploy your program in seconds, and rehearse the exact mainnet deploy for free.

This is what we do instead of fighting devnet. Copy-paste below — every command is a copy block.

## Why not just use devnet?

Devnet's faucet is the bottleneck: **rate-limited (HTTP 429)**, often dry, drip-sized, and cooldown-walled. A program deploy costs rent proportional to the binary size, so you may need *several* airdrops just to afford one deploy — burning an afternoon babysitting a faucet. Devnet is also shared and flaky.

For **rehearsing a deploy** — does it deploy, do the flags work, does the init instruction run, does the client connect — you don't need a public network. You need a fast, deterministic sandbox with free SOL. That's a local validator.

## How to get unlimited SOL for testing (no faucet)

```bash
# 1. start a fresh local validator (-r resets the ledger each run)
solana-test-validator -r

# 2. point the CLI at it
solana config set --url http://127.0.0.1:8899

# 3. airdrop as much as you want — instant, unlimited, no faucet
solana airdrop 100
```

## How to deploy a Solana program locally

```bash
solana program deploy target/deploy/yourprog.so \
  --program-id target/deploy/yourprog-keypair.json \
  --upgrade-authority ~/.config/solana/id.json

# verify it landed
solana program show <PROGRAM_ID>
```

Run your init instruction and client/integration tests against `http://127.0.0.1:8899` exactly as you would on mainnet.

## How to deploy the SAME program to mainnet

Parameterize the RPC URL and payer so one script runs local then mainnet — only the endpoint and funding key change:

```bash
RPC=https://api.mainnet-beta.solana.com \
PAYER=~/deploy-authority.json \
bash deploy.sh   # the script you already watched succeed locally
```

Pin the `sha256` of your `.so` and refuse to deploy if it differs — so "tested" and "deployed" are provably the same bytes.

## What a local validator *won't* catch (size your mainnet deploy)

A local validator runs the same runtime, but it's lenient about two limits mainnet enforces hard. Each can pass locally and then fail on mainnet, so budget for them *before* you spend real SOL:

- **Compute budget.** Mainnet gives a transaction **200,000 compute units by default.** A heavy instruction — several CPIs, multiple PDA derivations, on-the-fly account creation — can blow past that and fail with an `exceeded CUs` error even though it ran fine locally. If your tx does real work, request more up front with a `ComputeBudget: SetComputeUnitLimit` instruction (sized to your tx, up to 1.4M CU). The local validator will *not* flag this for you.
- **Transaction size.** A Solana transaction is capped at **1232 bytes.** Prepending account-creation instructions (idempotent ATA creates and the like) to your main instruction can quietly push you over. Build your heaviest path and assert it serializes under 1232 bytes before you rely on it.
- **Priority fees.** Local has no fee market. Under mainnet congestion your tx may not land without a priority fee — size it from recent fees rather than hardcoding zero.

None of these surface against `solana-test-validator`. Local proves your *logic* and your *deploy mechanics*; these three are the mainnet-only variables to account for separately.

## FAQ

**Q: The devnet faucet says "rate limit reached" / returns 429 / "try again later." How do I get SOL?**
Use a local validator. `solana airdrop 100` against `http://127.0.0.1:8899` is instant and unlimited — no faucet, no captcha, no cooldown.

**Q: How do I reset local validator state between tests?**
Restart with `solana-test-validator -r`. The `-r` wipes the ledger so a leftover account can't quietly satisfy a check and hide a bug.

**Q: Can I deploy at a specific or vanity program address locally?**
Yes — pass `--program-id <keypair.json>`. The program ID is that keypair's public key.

**Q: Does this work for Anchor programs?**
Yes — `anchor build`, then `solana program deploy target/deploy/<name>.so`, or `anchor deploy --provider.cluster localnet`.

**Q: How do I keep the program upgradeable?**
Don't pass `--final`; set `--upgrade-authority` to a key you control. To make it immutable later, set the authority to none.

**Q: Is the local validator the same runtime as mainnet?**
It runs the same Agave/Solana validator, so program behavior, rent, and CU limits match closely — ideal for a deploy rehearsal. (Mainnet still has real congestion and priority fees; size those separately.)

---

**Keywords:** solana local validator, solana-test-validator, devnet faucet rate limit 429, how to get devnet SOL, deploy solana program locally, test solana program without devnet, solana airdrop unlimited, localnet deploy, anchor localnet deploy, mainnet deploy rehearsal, solana program deploy upgradeable.

*Shared by the xete team — [xete.net](https://xete.net). No catch; if it saves you a faucet afternoon, pay it forward.*
