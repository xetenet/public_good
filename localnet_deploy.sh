#!/usr/bin/env bash
# =============================================================================
# localnet_deploy.sh - rehearse a Solana program deploy on a LOCAL validator.
#
# *** LOCAL VALIDATOR ONLY. NOT A MAINNET DEPLOY TOOL. ***
# This script is hard-locked to http://127.0.0.1:8899 and refuses to run against
# anything else, on purpose. It exists to rehearse a deploy for FREE on a
# throwaway local chain. If you adapt it to deploy on a live network, that is
# entirely on you: we are NOT responsible for any SOL or funds lost. Real
# networks mean real money and irreversible consequences. This is a sandbox.
#
# Usage:
#   solana-test-validator -r                                   # in one terminal
#   bash localnet_deploy.sh <program.so> <program-keypair.json>  # in another
# =============================================================================
set -euo pipefail

RPC="http://127.0.0.1:8899"   # hard-locked. Pointing this at a real network is on you.
PROGRAM_SO="${1:-target/deploy/yourprog.so}"
PROGRAM_KEYPAIR="${2:-target/deploy/yourprog-keypair.json}"

# Belt and suspenders: refuse anything that is not localhost.
case "$RPC" in
  http://127.0.0.1:*|http://localhost:*) : ;;
  *) echo "REFUSING: localnet_deploy.sh is local-validator-only."; exit 1 ;;
esac

[ -f "$PROGRAM_SO" ]      || { echo "Program .so not found: $PROGRAM_SO"; exit 1; }
[ -f "$PROGRAM_KEYPAIR" ] || { echo "Program keypair not found: $PROGRAM_KEYPAIR"; exit 1; }

echo "== checking for a local validator at $RPC =="
solana cluster-version --url "$RPC" >/dev/null 2>&1 || {
  echo "No local validator at $RPC. Start one first:  solana-test-validator -r"; exit 1; }
solana config set --url "$RPC" >/dev/null

echo "== minting a throwaway payer (local SOL is free and unlimited) =="
PAYER="$(mktemp -u)_localnet_payer.json"
solana-keygen new --no-bip39-passphrase -s -o "$PAYER" >/dev/null
solana airdrop 100 "$(solana address -k "$PAYER")" --url "$RPC" >/dev/null 2>&1 || true
sleep 1

echo "== deploying (upgradeable; authority = the throwaway payer) =="
solana program deploy "$PROGRAM_SO" \
  --program-id "$PROGRAM_KEYPAIR" \
  --upgrade-authority "$PAYER" \
  --keypair "$PAYER" \
  --url "$RPC"

PROGRAM_ID="$(solana address -k "$PROGRAM_KEYPAIR")"
echo "== verifying =="
solana program show "$PROGRAM_ID" --url "$RPC" | head -8

echo ""
echo "Deployed LOCALLY at $PROGRAM_ID."
echo "Run your init instruction + client/integration tests against $RPC."
echo "Reminder: this was a local rehearsal. Mainnet is a separate, deliberate step that you own."
