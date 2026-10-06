# antigravity

Google's Antigravity CLI (`agy`) for one account. Logging in is a person's
job, once, in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

It runs Google's own installer, which puts `agy` in `~/.local/bin`. From
then on `agy` updates itself, so a later sync leaves it alone.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `antigravity` | manual | workspace | yes | `devmachine login antigravity --workspace acme` |

`antigravity`'s login starts `agy`. Over SSH it prints a link instead of
opening a browser: sign in with Google on your own computer and paste the
code back. `agy` keeps the session in the system keyring where there is
one. Where it keeps it on a server without one is not documented: this
package looks for `~/.gemini/antigravity-cli/antigravity-oauth-token`, so
`credentials list` may report the login missing after it succeeded.

A Gemini API key works instead of a login: set `"modelProvider": "gemini"`
in `~/.gemini/antigravity-cli/settings.json` and export `GEMINI_API_KEY`.

## Skills

Antigravity CLI reads skills from `~/.gemini/antigravity-cli/skills`, not
from `~/.agents/skills`. A workspace with this package gets a link there
for every skill a package contributes.

## Add it

```bash
devmachine packages add antigravity --workspace acme
devmachine sync
devmachine login antigravity --workspace acme
```

## Learn more

- [Antigravity CLI as your coding agent](https://mydevmachine.sh/guides/antigravity-cli/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
