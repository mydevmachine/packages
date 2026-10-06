# codex

OpenAI's Codex CLI for one account, from its standalone release, so it
needs no Node. Logging in is a person's job, once, in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

It runs OpenAI's own installer, which keeps the release under
`~/.codex/packages/standalone` and puts a `codex` link in `~/.local/bin`.
That folder goes on the PATH in `~/.zshenv`. Codex updates itself from then
on, so a later sync leaves it alone.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `codex` | manual | workspace | yes | `devmachine login codex --workspace acme` |

`codex`'s login runs `codex login --device-auth`, a device-code sign-in: it
prints a link and a code, and waits until you approve it in a browser on
any device. Turn on device code sign-in in your ChatGPT security settings
first, or the link refuses you. The tokens are kept at `~/.codex/auth.json`.
An account set to `cli_auth_credentials_store = "keyring"` keeps them
elsewhere, and then `credentials list` calls a working login missing.

## Skills

Codex reads `~/.agents/skills`, where every package's skills already land,
so it needs no link.

## Add it

```bash
devmachine packages add codex --workspace acme
devmachine sync
devmachine login codex --workspace acme
```

## Learn more

- [Codex authentication](https://learn.chatgpt.com/docs/auth)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
