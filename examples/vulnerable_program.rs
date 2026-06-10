//! vulnerable_program.rs - a DELIBERATELY INSECURE example, for demonstration only.
//! It exists so `solana_program_check.py` has something to flag. DO NOT DEPLOY THIS.
//! Every "BUG:" note below is a real attack surface the checker should catch.

use pinocchio::{account::AccountView, address::Address, error::ProgramError, ProgramResult};
use pinocchio_token::instructions::Transfer;

/// withdraw: pay `amount` out of a vault to a destination token account.
fn withdraw(program_id: &Address, accounts: &mut [AccountView], data: &[u8]) -> ProgramResult {
    let [authority, vault, dest_token, _token_program] = accounts else {
        return Err(ProgramError::NotEnoughAccountKeys);
    };

    // BUG: `vault` is trusted without `vault.owner() == program_id`, and its PDA
    //      is never re-derived -- a caller can pass any account they control.
    // BUG: short `data` panics here instead of returning an error.
    let amount = u64::from_le_bytes(data[0..8].try_into().unwrap());

    // BUG: "finalize" by flipping a status flag instead of closing the account,
    //      which leaves a re-entrant "withdrawn but still open" state.
    let mut state = vault.try_borrow_mut().unwrap();
    state.status = 1;

    // BUG: raw Transfer (not TransferChecked) -- mint and decimals are unverified.
    // BUG: `dest_token`'s owner is never bound to the intended recipient.
    Transfer { from: &*vault, to: &*dest_token, authority: &*authority, amount }.invoke()?;

    Ok(())
}

/// admin_only: included so the checker reports a realistic *mix* -- this handler
/// does verify a signer.
fn admin_only(accounts: &mut [AccountView]) -> ProgramResult {
    let [admin, _config] = accounts else {
        return Err(ProgramError::NotEnoughAccountKeys);
    };
    if !admin.is_signer() {
        return Err(ProgramError::MissingRequiredSignature);
    }
    Ok(())
}
