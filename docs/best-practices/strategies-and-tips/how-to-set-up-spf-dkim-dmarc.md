---
icon: '1'
---

# How To Set Up SPF, DKIM, DMARC

{% embed url="https://youtu.be/yuhOgyz1cXs" %}

Here's a quick guide to setting up email authentication protocols:

1. [SPF](https://www.techtarget.com/searchsecurity/definition/Sender-Policy-Framework): Checks if sending server is allowed to send emails for your domain
2. [DKIM](https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail): Adds a digital signature to your emails
3. [DMARC](https://en.wikipedia.org/wiki/DMARC): Uses SPF and DKIM to handle suspicious emails

Why bother? These protocols:

* Boost email deliverability
* Build trust with email providers
* Protect your domain reputation

Setting up is straightforward:

1. SPF: Add a TXT record to your DNS listing approved IP addresses
2. DKIM: Generate key pair, add public key to DNS, configure email server
3. DMARC: Create policy, add TXT record to DNS, set up reporting

| Protocol | Function             | Analogy          |
| -------- | -------------------- | ---------------- |
| SPF      | Checks sender's IP   | Guest list       |
| DKIM     | Adds signature       | Wax seal         |
| DMARC    | Manages SPF and DKIM | Security manager |

> _Remember: Start with lenient policies, then tighten over time. Regular checks and updates are key._



***

## Email Authentication Basics

Email authentication is your inbox's bouncer. It checks if emails are legit. Let's look at the three main bouncers: SPF, DKIM, and DMARC.

#### What is[ SPF](https://www.techtarget.com/searchsecurity/definition/Sender-Policy-Framework)?

![SPF](https://lh7-rt.googleusercontent.com/docsz/AD_4nXe6ZKh2ihnA2aqE5vuc8VdSKF945KlgnBD_ARTtvGVwRkfEY3LjoXMfjq80mFXwZkz_nHFuOsbvgoC5no7NOAqruvhm6GYig8DPWV5stnATS-zyXpT5eJwmHx0iqSr_OrIgC2z7df7n-26OTizjzw?key=ZhXuwRCLHfnRb2BYW6fMY8Vw)

SPF (Sender Policy Framework) is like a guest list for your domain's emails. Here's how it works:

1. You make an SPF record in your DNS.
2. This record lists approved IP addresses for sending emails.
3. Receiving servers check if the sending IP is on the list.

If it's not listed? The email might end up in spam or get rejected.

#### What is[ DKIM](https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail)?

![DKIM](https://lh7-rt.googleusercontent.com/docsz/AD_4nXebQ62LkBkWILWgz9Hui7G-aTSgL-duBDVJpfwfJNTik5Z0T2-asKa7aPgghflYsc4hn5sBy_T_zuIE5sIQ_GHLQu7M1YID6NrEadaMQcKp-IwlEooeD_GSkrR98cf0aw-PrBhMMlUKCbMK8Xd4xA?key=ZhXuwRCLHfnRb2BYW6fMY8Vw)

DKIM (DomainKeys Identified Mail) is like a wax seal for your emails. It works like this:

1. Your server adds a unique signature to outgoing emails.
2. The receiving server checks this signature against your DNS.
3. A valid signature proves the email wasn't messed with in transit.

#### What is[ DMARC](https://en.wikipedia.org/wiki/DMARC)?

![DMARC](https://lh7-rt.googleusercontent.com/docsz/AD_4nXfTK2E0lRY6JMCg9UMpB-o51anVLJ9jNfQfXHhLy9UutU1oGzuWDUMce8fsMWTV4A-8D43D14Dh0YMXNoOyjSzDNMNPi_voUVKxIcDaGcIbAW5xRspIH7Xzk7QFc6ojA3p-N9zNcGo4NhlFLzj2Mg?key=ZhXuwRCLHfnRb2BYW6fMY8Vw)

DMARC manages SPF and DKIM. It tells servers what to do with emails that fail these checks. DMARC:

1. Checks if SPF and DKIM passed
2. Verifies if the "From" address matches the domain that passed SPF/DKIM
3. Tells the server how to handle failed emails

#### How They Work Together

These three team up to protect your email:

| Protocol | Function             | Analogy          |
| -------- | -------------------- | ---------------- |
| SPF      | Checks sender's IP   | Guest list       |
| DKIM     | Adds signature       | Wax seal         |
| DMARC    | Manages SPF and DKIM | Security manager |

When an email arrives, servers:

1. Check SPF to verify the sender's IP
2. Verify DKIM to ensure the email's intact
3. Follow DMARC policy to decide what to do

This triple-check makes it tough for scammers to fake your domain. It's not perfect, but it's solid protection against email fraud.



***

## Before You Start

You need a few things in place before setting up SPF, DKIM, and DMARC. Here's what you'll need:

#### Domain Control

You must own your domain. This means:

* A registered domain (like yourbusiness.com)
* Access to manage DNS records

Free email services won't work. You need a custom domain.

#### DNS Record Access

You'll be adding TXT records to your DNS. To do this:

1. Log into your domain provider's control panel
2. Find DNS management or settings
3. Look for the option to add new DNS records

Can't find it? Check your provider's help docs or contact support.

#### Email Provider Information

Your email service has crucial info you'll need:

* DKIM keys
* Authorized IP addresses for SPF
* Recommended DMARC settings

Most providers have a page for this. If not, ask their support team.

| Provider                                                    | Authentication Info Location                                         |
| ----------------------------------------------------------- | -------------------------------------------------------------------- |
| [Mailchimp](https://mailchimp.com/)                         | Account dashboard > Domains section                                  |
| [Google Workspace](https://workspace.google.com/)           | Admin console > Apps > Google Workspace > Gmail > Authenticate email |
| [Office 365](https://www.microsoft.com/en-us/microsoft-365) | Admin center > Setup > Domains                                       |

> _Heads up: From February 2024, Gmail and Yahoo will require these authentications for bulk senders (over 5,000 emails/day). It's smart to set this up now._



***

## Setting up SPF

SPF (Sender Policy Framework) helps protect your domain from email spoofing. Here's how to set it up:

#### Finding DNS Settings

Log into your domain provider's control panel and look for "DNS Management" or "DNS Settings". You'll need to add new DNS records here.

Can't find it? Check your provider's help docs or contact support.

#### Making an SPF Record

To create an SPF record:

1. Choose "Add new record" in DNS settings
2. Select "TXT" as the record type
3. Set the host to "@" or your domain name
4. Enter your SPF record in the TXT value field

#### SPF Record Structure

A basic SPF record looks like this:

```
v=spf1 [mechanisms] [all]

```

* v=spf1: Always starts the SPF record
* mechanisms: List of approved servers/IPs
* all: How to handle non-matching servers

#### Common SPF Settings

Here's a quick look at common SPF mechanisms:

| Mechanism | Description                  | Example                          |
| --------- | ---------------------------- | -------------------------------- |
| ip4       | Allows specific IPv4 address | ip4:192.0.2.0                    |
| ip6       | Allows specific IPv6 address | ip6:2001:db8:85a3::8a2e:370:7334 |
| a         | Allows domain's A record     | a                                |
| mx        | Allows domain's MX records   | mx                               |
| include   | Allows another domain's SPF  | include:thirdpartydomain.com     |

#### Checking SPF Setup

After setting up your SPF record:

1. Wait 24-48 hours for DNS changes to spread
2. Use an SPF record checker tool
3. Send a test email and check the headers



***

## Setting up DKIM

DKIM adds a digital signature to your emails. Here's how to set it up:

#### Creating DKIM Keys

1. Log into your email provider's settings
2. Find DKIM or email authentication options
3. Generate a new DKIM key pair

In Google Workspace:

* Go to Apps -> Google Workspace -> Gmail -> Authenticate email
* Click "Generate new record"

#### Adding DKIM to DNS

1. Access your domain's DNS settings
2. Create a new TXT record
3. Use this format: selector.\_domainkey.yourdomain.com
4. Paste the public key in the record value

Example DKIM record:

| Type | Host                  | Value                                   |
| ---- | --------------------- | --------------------------------------- |
| TXT  | selector1.\_domainkey | k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4G... |

#### Setting Up Email Server for DKIM

1. Save the private key to your email server
2. Configure your server to use DKIM signing

For Microsoft 365:

* Go to Home -> Policy -> DKIM
* Select your domain
* Enable DKIM signatures

#### Testing DKIM

After setup:

1. Wait 24-48 hours for DNS changes
2. Send a test email to an external address
3. Check the email headers for a DKIM-Signature field

Use online DKIM checkers to verify your setup. If something's off, double-check your DNS records and server config.\


***

## Setting up DMARC

DMARC adds another security layer to your email setup. Here's how to do it:

#### Create a DMARC Policy

1\. Pick a policy level:

* p=none: Watch without affecting delivery
* p=quarantine: Send iffy emails to spam
* p=reject: Block emails that fail DMARC

2\. Start with p=none. It lets you gather data without messing up legit emails.

#### Add DMARC to DNS

1. Get into your domain's DNS settings
2. Make a new TXT record
3. Use this host format: \_dmarc.yourdomain.com
4. Pop in the DMARC policy as the value

Here's what a DMARC record looks like:

| Type | Host    | Value                                                     |
| ---- | ------- | --------------------------------------------------------- |
| TXT  | \_dmarc | v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com |

#### DMARC Settings Breakdown

* v=DMARC1: DMARC version
* p=: How to handle failed checks
* rua=: Where to send reports
* pct=: % of messages under policy

#### Set Up DMARC Reports

1. Make an email just for DMARC reports
2. Add rua= to your DMARC record
3. Optional: Use ruf= for detailed failure reports

DMARC reports show you:

* Source IP addresses
* SPF and DKIM results
* How many messages were sent



***

## Tips for SPF, DKIM, and DMARC

#### Keep Your Settings Sharp

Don't let your email authentication get rusty:

* Check SPF records every few months
* Rotate DKIM keys yearly
* Set up alerts for DMARC changes

#### Ramp Up DMARC Slowly

Start small, then crank it up:

1\. p=none: Watch and learn

2\. p=quarantine: Spam-folder the sketchy stuff

3\. p=reject: Block all bad emails

| Policy       | What It Does             | When to Use         |
| ------------ | ------------------------ | ------------------- |
| p=none       | Just watches             | Day one             |
| p=quarantine | Spam-folders iffy emails | After some watching |
| p=reject     | Blocks bad emails        | When you're sure    |

#### Handle Outside Senders

Be smart with third-party emails:

* Use subdomains for external folks
* Make them send through your servers
* Test their emails often

"Tell vendors about DMARC Alignment, DKIM Domains, and email headers", says Josh Stein from Proofpoint.



***

## Fixing Common Problems

Email authentication can be a pain. Let's tackle the big issues.

#### SPF Record Mistakes

SPF records often cause headaches. Watch out for:

* Multiple SPF records
* Too many lookups
* Syntax errors

How to fix:

1\. Audit your SPF record

* Use[ MXToolbox](https://mxtoolbox.com/SuperTool.aspx) to spot errors.

2\. Simplify

* Ditch hard-coded IPs. Use include: statements instead.

3\. Test

* Send test emails after changes.

#### DKIM Key Issues

DKIM problems can sneak up on you. Look for:

* Mismatched keys
* Expired keys
* Incorrect syntax

The fix:

1\. Check your keys

* Use a DKIM validator to make sure they're set up right.

2\. Set a reminder

* Rotate keys yearly.

3\. Double-check syntax

* Small errors = big problems.

#### DMARC Policy Conflicts

DMARC ties it all together, but it can cause trouble:

* Overly strict policies
* Misconfigured reporting
* Alignment issues

How to solve:

1\. Start slow

Use p=none to monitor without blocking emails.

2\. Set up reporting

Use both rua and ruf tags in your DMARC record.

3\. Check alignment

Make sure your "From" domain matches your SPF and DKIM domains.

| DMARC Policy | What It Does        | When to Use      |
| ------------ | ------------------- | ---------------- |
| p=none       | Monitor only        | Starting out     |
| p=quarantine | Send to spam folder | After monitoring |
| p=reject     | Block emails        | When confident   |

Email authentication isn't a set-it-and-forget-it deal. Keep checking and tightening your policies.

> _"Almost 1 million internet domains have misconfigured DMARC records, posing significant email security risks", reports a recent study. Don't be one of them._



***

## Helpful Tools

Setting up SPF, DKIM, and DMARC can be a headache. But don't worry - there are tools to make it easier.

#### DNS Record Checkers

These tools help you spot issues in your setup:

* MXToolbox's[ SuperTool](https://mxtoolbox.com/SuperTool.aspx): Checks SPF, DKIM, and DMARC records
* [DMARCLY](https://dmarcly.com/): Email check@[dmarcly](https://dmarcly.com/).com for a full report

#### Email Authentication Tests

Want to test your setup? Try these:

* DKIM Validator: Makes sure your public DKIM key works
* SPF Surveyor: Finds problems in your SPF record
* DMARC Inspector: Checks your DMARC policy for issues

#### DMARC Report Tools

DMARC reports can be a pain to read. These tools help:

* XML-to-human Converter: Makes complex XML readable
* DMARC Report Analyzer: Breaks down aggregate XML and forensic reports

| Tool                                                  | Free Plan       | Paid Plan Starts At      | Features                                 |
| ----------------------------------------------------- | --------------- | ------------------------ | ---------------------------------------- |
| [MailerCheck](https://www.mailercheck.com/)           | Yes (1 domain)  | $125/month (10 domains)  | DMARC recommendations, email auth check  |
| [Dmarcian](https://dmarcian.com/dmarc-saas-platform/) | Yes (2 domains) | $24/month                | Forensic reports, phishing scorecard     |
| DMARCLY                                               | No              | $17.99/month (2 domains) | Blocklist monitoring, forensic reporting |
| [EasyDMARC](https://easydmarc.com/)                   | Yes (1 domain)  | $39.99/month (2 domains) | Hosted DMARC and BIMI                    |

These tools can save you time and headaches. Pick the one that fits your needs and budget.



***

## Conclusion

SPF, DKIM, and DMARC aren't just tech jargon. They're your secret weapons for protecting your real estate domain and keeping your lead communication on point.

Here's the lowdown:

1. Spam is everywhere: 84% of global emails are junk. These protocols are your shield.
2. Inbox, not spam folder: Get your emails where they belong.
3. ISPs will love you: Build trust and boost your domain's street cred.
4. Get ready for 2024: Gmail and Yahoo are upping their game. You should too.
5. Stay on top of it: This isn't a set-it-and-forget-it deal. Keep checking and updating.

But don't stop there. To keep your domain reputation sparkling:

* Keep spam complaints under 0.1%
* Aim for 0.5% unsubscribe rates
* Use double opt-in for new subscribers
* Clean your list regularly



