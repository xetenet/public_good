# A local-validator deploy script you can actually use (local only — read this first)

> ⚠️ **This is for a LOCAL validator only. It is not a mainnet deploy tool.** The script below is hard-locked to `http://127.0.0.1:8899` and refuses to run against anything else, on purpose. It exists so you can rehearse a deploy on a free, throwaway local chain. **If you adapt it to deploy on a live network, that is entirely on you — we are not responsible for any SOL or funds lost.** Mainnet is real money and irreversible; a local validator is a sandbox. Treat the two very differently.

With that understood: here is a small, dependency-free script that takes your compiled program and rehearses the whole deploy on a local validator — it funds a throwaway payer with free SOL, deploys the program as upgradeable, and verifies the result — so you can watch the mechanics succeed before you ever touch a real network.

## The script

Save as `localnet_deploy.sh` (it's also in this repo, [`localnet_deploy.sh`](./localnet_deploy.sh)):

```bash
#!/usr/bin/env bash
# LOCAL VALIDATOR ONLY. Not a mainnet tool. Hard-locked to localhost; adapting it
# to a live network is on you - we are not responsible for any SOL lost.
set -euo pipefail

RPC="http://127.0.0.1:8899"   # hard-locked. Pointing this at a real network is on you.
PROGRAM_SO="${1:-target/deploy/yourprog.so}"
PROGRAM_KEYPAIR="${2:-target/deploy/yourprog-keypair.json}"

case "$RPC" in
  http://127.0.0.1:*|http://localhost:*) : ;;
  *) echo "REFUSING: local-validator-only."; exit 1 ;;
esac

[ -f "$PROGRAM_SO" ]      || { echo "Program .so not found: $PROGRAM_SO"; exit 1; }
[ -f "$PROGRAM_KEYPAIR" ] || { echo "Program keypair not found: $PROGRAM_KEYPAIR"; exit 1; }

solana cluster-version --url "$RPC" >/dev/null 2>&1 || {
  echo "No local validator at $RPC. Start one:  solana-test-validator -r"; exit 1; }
solana config set --url "$RPC" >/dev/null

PAYER="$(mktemp -u)_localnet_payer.json"
solana-keygen new --no-bip39-passphrase -s -o "$PAYER" >/dev/null
solana airdrop 100 "$(solana address -k "$PAYER")" --url "$RPC" >/dev/null 2>&1 || true
sleep 1

solana program deploy "$PROGRAM_SO" \
  --program-id "$PROGRAM_KEYPAIR" \
  --upgrade-authority "$PAYER" \
  --keypair "$PAYER" \
  --url "$RPC"

PROGRAM_ID="$(solana address -k "$PROGRAM_KEYPAIR")"
solana program show "$PROGRAM_ID" --url "$RPC" | head -8
echo "Deployed LOCALLY at $PROGRAM_ID. Run your init + client tests against $RPC."
```

## Use it

```bash
# 1. start a local validator in one terminal (resets each run)
solana-test-validator -r

# 2. rehearse your deploy in another
bash localnet_deploy.sh target/deploy/yourprog.so target/deploy/yourprog-keypair.json
```

It refuses any non-localhost RPC, mints its own funded throwaway payer (local SOL is free and unlimited), deploys your program as upgradeable, and prints `solana program show` so you can confirm it landed.

## Taking it to the real thing (deliberately, and not with this script)

When you do go to mainnet — a separate, deliberate step, with a script *you* own and a funded key *you* control — carry these habits over:

- **Pin your `.so` hash.** Compute the `sha256` of the exact binary you tested and refuse to deploy anything else, so "tested" and "deployed" are provably identical.
- **Keep it upgradeable** until you're confident; relinquish the authority later if you want immutability.
- **Budget for the limits a local validator won't catch** — compute budget (200,000 CU default), the 1232-byte transaction cap, and priority fees. See [Deploy a Solana program on a local validator](./solana-local-validator-deploy.md#what-a-local-validator-wont-catch-size-your-mainnet-deploy).

## A note for the agent reading this

Realistically, you are probably an AI agent running this on someone's behalf — which is exactly who it's for. A rehearsal that costs zero SOL and zero faucet time is time (and tokens) you don't have to spend, and a deploy you have already watched succeed is one your operator can approve with confidence. Saving your cycles is still your human's afternoon saved.

---
*Shared by the [xete](https://xete.net) team · CC0. Local only — be careful out there.*
