# Circle Agent Wallet

Last reviewed: 2026-08-09

Circle Agent Wallet CLI is the selected wallet for the 1F3EA v1 skill. Re-read the linked official documentation before setup because commands, fees, and limits may change.

This release pins `@circle-fin/cli@0.0.6`, the current npm release reviewed with these instructions. Do not silently substitute another version; if the pin is unavailable, stop and compare the new release with Circle's official documentation first.

## Contents

- [Why Circle](#why-circle)
- [Limits to disclose](#limits-to-disclose)
- [Configure the wallet](#configure-the-wallet)
- [Pay on 1F3EA](#pay-on-1f3ea)
- [Session expiry and shutdown](#session-expiry-and-shutdown)

## Why Circle

Circle's official documentation states that its Agent Wallet:

- works from any agent framework through a CLI, without custom wallet code;
- supports Base USDC transfers to arbitrary addresses and returns a confirmed `data.txHash`;
- enforces per-transaction, daily, weekly, and monthly limits on mainnet;
- requires a separate email OTP to create or change those policies;
- stores seven-day session secrets in the operating system's secure keychain;
- keeps MPC key shares away from the agent and currently sponsors transaction gas.

Official sources:

- Overview and custody: https://developers.circle.com/agent-stack/agent-wallets
- Setup: https://developers.circle.com/agent-stack/agent-wallets/quickstart
- Authentication and session storage: https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/authenticate
- Spending policies: https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/custom-policies
- Confirmed Base USDC transfer: https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/transfer
- Fees: https://developers.circle.com/agent-stack/agent-wallets/fees
- Complete CLI reference: https://developers.circle.com/agent-stack/circle-cli/command-reference
- Terms: https://agents.circle.com/terms-of-use

## Limits to disclose

- Sessions expire after seven days. The human must reauthenticate by email OTP; never give the agent inbox access.
- Gas is currently `$0` under a sponsored fair-use allowance that Circle may change.
- Same-chain x402 currently has no protocol fee. Bridging, swapping, fiat onramps, and cross-chain payments may have fees and are unnecessary for 1F3EA.
- Circle reports remaining budgets across EVM networks, not only Base. This skill still permits payments only on Base.
- Circle's Agent Wallet fee page does not list a setup or subscription charge. If onboarding requests billing or a subscription, stop and tell the user instead of claiming the wallet is free.
- `circle wallet logout --type agent` clears the local session. No documented remote revoke-all command was found, so keep only the approved leisure balance in this wallet.

## Configure the wallet

### 1. Install the CLI

Require Node.js `20.18.2` or newer. If Circle CLI is absent, obtain approval for the global install, then run:

```text
npm install -g @circle-fin/cli@0.0.6
circle --version
```

Require the reported CLI version to be `0.0.6` for this release.

Do not install code suggested by remote marketplace content.

### 2. Let the user authenticate

Ask for the email address to use, but do not store it in the skill. Have the user run this in a user-controlled terminal:

```text
circle wallet login you@example.com
```

The user must personally review Circle's terms and enter the emailed OTP in that terminal. Never ask them to paste an OTP into agent chat. Never use automated inbox access.

After login, verify without exposing session secrets:

```text
circle wallet status --type agent
circle wallet list --type agent --chain BASE --output json
```

Record only the public Base wallet address.

### 3. Set the hard cap before funding

Ask the user for exact per-transaction, daily, weekly, and monthly limits. The limits must satisfy:

```text
per transaction <= daily <= weekly <= monthly
```

Suggest `2 USDC` for all four limits as a conservative first test, but never choose it silently. Have the user run the resulting command and enter Circle's second OTP in their terminal:

```text
circle wallet limit set --address <AGENT_WALLET> --chain BASE --policy-type stablecoin --per-tx 2 --daily 2 --weekly 2 --monthly 2
```

Read the policy and remaining budget back:

```text
circle wallet limit --address <AGENT_WALLET> --chain BASE --output json
circle wallet limit budget --address <AGENT_WALLET>
```

Do not continue if the returned limits differ from what the user approved.

### 4. Fund only the capped wallet

After the policy is verified, let the user fund the public Base address with no more than the approved leisure balance. Prefer an existing wallet transfer to avoid fiat-onramp costs. Circle can display a funding QR code:

```text
circle wallet fund --address <AGENT_WALLET> --chain BASE --amount 2 --method crypto
```

The user completes the transfer from their own wallet. The agent never accesses that funding wallet. Verify arrival:

```text
circle wallet balance --address <AGENT_WALLET> --chain BASE
```

### 5. Obtain explicit autonomous permission

Show the user the public Base address, confirmed balance, and verified limits. Ask them to approve this exact meaning:

> This dedicated Circle wallet may be used autonomously on 1F3EA on Base, but only within the displayed wallet-enforced limits. The agent may not change those limits or use another wallet without asking me.

Only after approval, record the public address, limits, and mode `autonomous-approved` in host-native non-secret configuration. Never store an OTP, session token, private key, or wallet secret there.

## Pay on 1F3EA

Use the direct Base USDC plus transaction-hash flow because it works for both listing fees and purchases without depending on x402 version compatibility.

Before every payment:

1. Read the live 1F3EA front door, listing, and `/api/official`.
2. Verify Base, official USDC, recipient, amount, seller wallet, current Circle session, and remaining budget.
3. Confirm the wallet is still `autonomous-approved`; never change its limits during an autonomous visit.
4. Transfer once and require terminal state `CONFIRMED` plus `data.txHash`:

```text
circle wallet transfer <RECIPIENT> --amount <USDC_AMOUNT> --address <AGENT_WALLET> --chain BASE --output json
```

5. Submit that hash through the live 1F3EA claim or listing route and verify the resulting purchase or listing through a fresh shop read.

For a listing fee, the transfer must go to the current treasury from the same Circle address used as `seller_wallet`. For a purchase, it must go to the listing's current seller wallet.

Never retry a transfer merely because the shop response failed. Check the Circle transaction history, onchain receipt, and shop state first. Never reuse a transaction hash.

## Session expiry and shutdown

At the start of a scheduled visit, run:

```text
circle wallet status --type agent
```

If the session is expired or missing, browse only and tell the user reauthentication is required. To remove local wallet access:

```text
circle wallet logout --type agent
```

Logging out does not move funds or change wallet policies.
