#!/usr/bin/env python3
"""
Dynamic attack simulator (TEMPLATE) for a Solana program.

This is the must-reject harness we use ourselves, with the program-specific parts
replaced by placeholders for you -- or your agent -- to fill in. Deploy your
program to a LOCAL validator, fill in the two marked sections (your instruction
builders, then your attack vectors), and run it. It fires REAL transactions and
asserts that the malicious ones REJECT and the honest ones land. Testing that a
program "works when you're honest" is not a security test; proving it *rejects*
every dishonest path is.

    python attack_sim_template.py <PROGRAM_ID> <signer1.json> <signer2.json> [rpc]

Defaults to a LOCAL validator (http://127.0.0.1:8899). Run it against localnet,
not a live network with real funds in an untested program. See the companion
guide and `solana-program-attack-surfaces.md` for the attack classes to cover.

Requires: pip install solders solana
"""
import json, struct, sys, time
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import AccountMeta as AM, Instruction
from solders.message import Message
from solders.transaction import Transaction
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts

# ---- well-known program ids ----
SYS   = Pubkey.from_string("11111111111111111111111111111111")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ATA   = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
CB    = Pubkey.from_string("ComputeBudget111111111111111111111111111111")

# ---- args (rename the roles to suit your program: maker/taker, admin/user, ...) ----
PROG  = Pubkey.from_string(sys.argv[1])
load  = lambda p: Keypair.from_bytes(bytes(json.load(open(p))))
ALICE = load(sys.argv[2])
BOB   = load(sys.argv[3])
RPC   = sys.argv[4] if len(sys.argv) > 4 else "http://127.0.0.1:8899"
c = Client(RPC)

# ---- generic helpers (reuse as-is) ----
def ata(owner, mint): return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]
def pda(*seeds):      return Pubkey.find_program_address([s if isinstance(s, (bytes, bytearray)) else bytes(s) for s in seeds], PROG)[0]
def nonce():          return bytes(Keypair().pubkey())
def soon(secs):       return int(time.time()) + secs
def cu(units):        return Instruction(program_id=CB, data=bytes([2]) + struct.pack("<I", units), accounts=[])

def send(signers, ixs, payer):
    """Submit a transaction. Returns ('ok' | 'rejected' | 'timeout', detail). Never raises."""
    bh = c.get_latest_blockhash().value.blockhash
    tx = Transaction(signers, Message.new_with_blockhash(ixs, payer.pubkey(), bh), bh)
    try:
        sig = c.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)).value
    except Exception as e:
        return ("rejected", str(e).replace("\n", " ")[:120])
    for _ in range(80):
        time.sleep(0.3)
        st = c.get_signature_statuses([sig]).value[0]
        if not st:
            continue
        if st.err:
            return ("rejected", str(st.err)[:120])
        if str(st.confirmation_status).split(".")[-1].lower() in ("confirmed", "finalized"):
            return ("ok", str(sig)[:10])
    return ("timeout", "")

# ---- assertion harness (reuse as-is) ----
res = []
def _expect(kind, label, signers, ixs, payer):
    status, detail = send(signers, ixs, payer)
    good = (status == kind)
    res.append(good)
    print(f"[{'PASS' if good else 'FAIL'}] {label}" + ("" if good else f"   (got {status}: {detail})"))
def ok(label, signers, ixs, payer):     _expect("ok", label, signers, ixs, payer)       # honest path MUST land
def reject(label, signers, ixs, payer): _expect("rejected", label, signers, ixs, payer)  # malicious path MUST revert

# =====================================================================
# FILL IN #1 -- YOUR PROGRAM'S INSTRUCTION BUILDERS
# Encode each instruction as your program expects it: a tag/discriminator, the
# packed args, and the account metas IN ORDER. Generic shape:
# =====================================================================
def your_ix(tag, args_bytes, metas):
    return Instruction(program_id=PROG, data=bytes([tag]) + args_bytes, accounts=metas)

# Example (delete and replace with your real instruction):
# def open_order_ix(n, amount, owner):
#     order = pda(b"order", owner.pubkey(), n)
#     data  = n + struct.pack("<Q", amount)
#     metas = [
#         AM(owner.pubkey(), True,  True),    # signer + writable (pays + authorizes)
#         AM(order,          False, True),    # the PDA the program creates
#         AM(SYS,            False, False),
#     ]
#     return order, your_ix(0, data, metas)

# =====================================================================
# FILL IN #2 -- YOUR ATTACK VECTORS
# Prove the HONEST path lands (ok), then prove each MALICIOUS variant reverts
# (reject). The classes below are the ones worth covering -- see
# solana-program-attack-surfaces.md. Uncomment and adapt to your instructions.
# =====================================================================

print("=== setup: honest positive controls ===")
# ok("honest: open an order", [ALICE], [open_order_ix(nonce(), 1000, ALICE)[1]], ALICE)

print("=== A - account substitution ===")
# Pass a fake or attacker-controlled account where a program-owned one is expected
# (a forged state account, a vault you control). MUST reject.
# reject("fake state account substituted", [BOB], [ix_with_fake_account], BOB)

print("=== B - payment / refund redirection ===")
# Point a payout or refund at an account you control instead of the bound party.
# reject("redirect payout to attacker", [BOB], [ix_redirecting_funds], BOB)

print("=== C - authorization bypass ===")
# Act on someone else's object without their signature.
# reject("act without the owner signing", [BOB], [ix_as_wrong_signer], BOB)

print("=== D - cross-object confusion ===")
# Pair one object's state with an unrelated object's vault / partner account.
# reject("mismatched object pairing", [BOB], [ix_mismatched], BOB)

print("=== E - replay / double-spend / re-init ===")
# Run a finalizing instruction twice; re-initialize a consumed account.
# ok("first settle lands", [ALICE], [settle_ix], ALICE)
# reject("second settle on closed state", [ALICE], [settle_ix], ALICE)

print("=== F - input guards ===")
# Zero amounts, already-expired deadlines, out-of-range values.
# reject("zero amount", [ALICE], [open_order_ix(nonce(), 0, ALICE)[1]], ALICE)

# ---- tally ----
if not res:
    print("\nNo checks ran yet. Fill in the vectors above (uncomment and adapt), then re-run.")
    sys.exit(2)
p = sum(res)
print(f"\n{p}/{len(res)} checks passed " + ("*** ALL GREEN ***" if p == len(res) else "*** FAILURES ABOVE ***"))
sys.exit(0 if p == len(res) else 1)
