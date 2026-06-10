# Attack surfaces in a value-handling Solana program (and the few defenses that close most of them)

When your Solana program moves value — tokens, SOL, anything an attacker would want to steal or redirect — you have to assume every account you're handed is adversarial: the wrong account, an account the attacker controls, a real account paired with the wrong partner. This is the attack-surface map we worked through building [xete](https://xete.net), generalized so you can run it against your own program.

The encouraging part: a *small* set of standing checks, applied everywhere, kills most of these. You don't need a special case per attack; you need a few invariants you never skip.

## The standing defenses

These recur in almost every instruction. Skipping one is where the holes are.

1. **Owner check.** Before you trust *any* stored state in an account, confirm `account.owner() == program_id`. A closed, foreign, or attacker-crafted account fails this. Trusting bytes in an account you don't own is the most common Solana exploit.
2. **PDA re-derivation.** Recompute every PDA (state, vault, config…) with `find_program_address(seeds)` and compare it to the account you were handed. You can't substitute a look-alike account if its address has to match a derivation you control.
3. **Recipient / owner binding.** Before paying out, read the destination token account's **mint and owner** and check them against the party who's supposed to receive. Otherwise an attacker passes their own account and redirects the payout.
4. **`transfer_checked`, not `transfer`.** The checked variants make the SPL Token program itself enforce the mint and decimals of each account, closing a class of decimals/mint-spoofing tricks.
5. **Close, don't flag.** To finalize, *close* the account — zero its data and sweep its lamports — rather than flipping a `status` byte. A second call then fails the owner/length check instead of re-running on stale state.
6. **Atomic or nothing.** Move both legs of an exchange and close the escrow in one instruction. No "settled but still open" state means no stale-state window to exploit.

## The attack classes

| Class | The attack | What stops it |
|-------|-----------|---------------|
| **Account substitution** | Pass a fake program-owned "state" account, or a vault the attacker controls, to fake a settlement or drain funds | Owner check + PDA re-derivation; derive the vault from the *same* seeds as the verified state account |
| **Payment / refund redirection** | Send the payment, or a refund, to the attacker instead of the intended party | Verify the destination's mint **and** owner against the expected recipient |
| **Authorization bypass** | Act as someone you're not — cancel another user's order, accept on their behalf | Require the party to **sign**, and check `stored_authority == signer` |
| **Cross-object confusion** | Pair an object with an unrelated one (pay from order A, release goods from order B) | Bind related accounts: store the partner's address and check it, or derive both from a shared nonce |
| **Double-spend / replay / re-init** | Settle twice, settle-after-cancel, re-initialize the same account | Close (don't flag) on settle; `CreateAccount` reverts if the account already exists |
| **Re-entrancy** | Trigger a callback that re-enters your instruction mid-state | Only CPI to programs that don't call back (e.g. SPL Token). No callback surface, no re-entrancy |
| **Arithmetic** | Overflow a balance or a fee calculation | `checked_*` math; enable `overflow-checks` in the release profile |
| **Griefing / DoS** | Front-run, spam orders, or make an instruction too expensive to land | Atomicity (the loser of a race just reverts, losing only fees); make each actor pay their own rent so no one is forced to interact; keep compute within limits |

## The one idea underneath all of it

Every row above reduces to the same move: **never trust an account's identity or contents without proving them** — owner-checked, address-derived, party-bound — and **never leave a half-finished state** an attacker can re-enter. Get those reflexes, apply them in *every* instruction without exception, and the long list of attacks collapses into a short list of invariants.

## Coming next: a checker you can run

A short heuristic script that scans your program's source for the presence (or worrying absence) of these patterns — signer checks, owner checks, PDA re-derivation, `transfer_checked`, close-vs-flag — is on its way to this repo. It's a first-pass checklist aid, not an audit, and we won't publish it until it's been run against real program source. (Realistically, an agent will run it for you — and an agent that can flag "this instruction never checks the signer" in seconds is a genuinely useful second pair of eyes, even if a human still makes the call.)

---
*Shared by the [xete](https://xete.net) team · CC0. This is hard-won field experience, not a formal audit — treat it as a checklist, and get a real review before mainnet.*
