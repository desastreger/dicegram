# Privacy Policy

**Applies to:** the hosted Dicegram service at
[dicegram.desastreger.cloud](https://dicegram.desastreger.cloud)

**Last updated:** 5 August 2026

> This policy covers the *hosted* service only. If you self-host Dicegram from
> this repository, you are the data controller for your own instance and this
> policy does not apply to you.

---

## 1. Who we are

**Nacho De Saeger**, trading as **Desastreger Studio** (“we”, “us”), is the data
controller for personal data processed through dicegram.desastreger.cloud.

- **Contact:** privacy@desastregerstudio.com
- **Security reports:** security@desastregerstudio.com (see [SECURITY.md](./SECURITY.md))
- **Postal address:** `[POSTAL ADDRESS — REQUIRED, see note below]`

> **Two things still to fill in before this is relied upon:** the postal
> address above, and the data-centre location in §5. A UK privacy notice must
> give a real contact address for the controller, and must state where personal
> data is held. Both are facts only you can supply.

We are not required to appoint a Data Protection Officer.

This policy is written to meet the UK GDPR and the Data Protection Act 2018.

## 2. What we collect, and why

| Data | When | Why | Lawful basis |
|---|---|---|---|
| Username | You create an account | Identifies your account and is the name you sign in with. Shown alongside your work | Contract |
| Password | You create an account | Authentication. Stored only as an Argon2 hash — we never hold the password itself | Contract |
| Password hint (optional) | You choose to set one | The only account-recovery prompt we offer. **Stored as plain text** — see below | Consent |
| Your dicegrams | You save work | To store and show you your diagrams | Contract |
| Share records | You create a share link | To serve a diagram you chose to publish | Contract |
| Colour/branding preferences | You change them | To render your diagrams as you configured | Contract |
| Account creation date | Automatically | Account administration and abuse handling | Legitimate interests |
| Truncated IP address, URL, timestamp, status code, referrer, browser user-agent | Every request | Security, abuse prevention, and counting roughly how many people use the service | Legitimate interests |

**We do not** use advertising, third-party analytics, tracking pixels,
behavioural profiling, or automated decision-making. We do not sell or rent
personal data to anyone, ever.

**We do not ask for an email address, and we do not send email.** The service
has no email subsystem at all, so there is nothing to send a reset link to and
no way for us to contact you. Accounts created before August 2026 still have an
email on record, used only as a legacy sign-in identifier; it is never used to
contact anyone and is scheduled for deletion.

**There is no password reset.** If you lose your password, the account and its
contents cannot be recovered by us or by anyone else.

### About the password hint

If you set a password hint, it is stored **unencrypted** and is shown after a
failed sign-in attempt for your username — so anyone who guesses your username
and enters a wrong password can read it. It is a memory aid, not a secret. **Do
not put anything sensitive in it, and do not make it something that reveals your
password.** Setting a hint is entirely optional.

## 3. Access logs and visitor counting

Our web server records a line per request. Before anything is written to disk,
your IP address is **truncated** — the last octet of an IPv4 address is
discarded (`203.0.113.x`), and IPv6 addresses are cut to their first 48 bits.

This means we can see roughly how many distinct networks visit, but we cannot
identify you from these logs or single you out as an individual. Session cookies
and authorisation headers are stripped from log entries before they are written.

Logs are rotated and deleted automatically after **90 days**.

## 4. Cookies

We set exactly one cookie:

| Cookie | Purpose | Lifetime |
|---|---|---|
| `dicegram_session` | Keeps you signed in | 14 days |

It is `httpOnly`, `sameSite=lax` and `secure`. It contains only a signed
reference to your session — no personal data, no tracking identifier.

This is a **strictly necessary** cookie: it exists solely to deliver a service
you asked for (staying signed in). Under PECR that means we do not need, and do
not show, a cookie consent banner. We set no other cookies.

If you use the no-signup demo, your work is kept in your browser’s
`localStorage`. That is not a cookie, is never sent to us as stored data, and is
cleared when you clear site data.

### What the demo does send

The demo runs in your browser, but **diagram layout is computed on our server**.
The text of the diagram you are editing is sent to us to be laid out. It is
processed in memory to produce a response and is **not stored**, but it does
leave your machine. Please do not put confidential information into the demo.

## 5. Who your data is shared with

| Who | What for |
|---|---|
| Hostinger (hosting provider) | Runs the server the service is deployed on |

That is the entire list. Hostinger acts as a processor on our behalf. Beyond
that we share personal data with nobody, except where we are legally required
to.

**Where your data is held:** `[DATA CENTRE COUNTRY — CONFIRM IN THE HOSTINGER
PANEL]`. If it is outside the UK, transfers rely on the UK adequacy
regulations where they apply, or on an International Data Transfer Addendum
with Hostinger where they do not.

## 6. How long we keep things

| Data | Retention |
|---|---|
| Account and dicegrams | Until you delete them, or you ask us to delete your account |
| Share links | Until you revoke the share or delete the diagram |
| Access logs | 90 days, then deleted automatically |
| Demo work | Only in your browser; we never receive it as stored data |

## 7. Your rights

Under UK GDPR you have the right to:

- **access** the personal data we hold about you
- **rectify** anything inaccurate
- **erase** your data (“right to be forgotten”)
- **restrict** or **object to** our processing
- **portability** — receive your data in a machine-readable form
- **withdraw consent** where consent is the basis (the password hint)

To exercise any of these, email privacy@desastregerstudio.com. We will respond within one
month. You will not be charged.

You can export your own diagrams at any time from inside the app (SVG, PNG, PDF,
HTML, CSV) without asking us.

If you are unhappy with how we handle your data, you can complain to the
Information Commissioner’s Office:

- **Web:** [ico.org.uk/make-a-complaint](https://ico.org.uk/make-a-complaint/)
- **Phone:** 0303 123 1113

We would appreciate the chance to resolve it first, but you can go to the ICO
directly.

## 8. Security

- Passwords are hashed with **Argon2**. We cannot read them.
- All traffic is served over **HTTPS** with HSTS.
- Session cookies are signed, `httpOnly` and `secure`.
- A Content-Security-Policy restricts what the page may load.
- Rate limiting protects against brute force and scraping.

No service can promise perfect security. If you believe you have found a
vulnerability, please report it as described in
[SECURITY.md](./SECURITY.md).

## 9. Children

This service is not directed at children and we do not knowingly collect data
from anyone under 13. If you believe a child has created an account, contact us
and we will delete it.

## 10. Changes to this policy

If we change this policy materially we will update the date at the top and note
the change in [CHANGELOG.md](./CHANGELOG.md). Continued use after a change means
you accept the updated policy.

## 11. Contact

Questions about this policy or your data: privacy@desastregerstudio.com
