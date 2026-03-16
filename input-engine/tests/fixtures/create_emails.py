"""
Generate test fixture .eml files for Phase 1 validation.
Run: uv run python input-engine/tests/fixtures/create_emails.py
Uses only Python stdlib — no dependencies needed.
"""

import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def create_plain_email():
    """Plain text email — no HTML."""
    msg = MIMEText(
        "Hi there,\n\n"
        "Just wanted to follow up on our meeting yesterday. Here are the key takeaways:\n\n"
        "1. We agreed to move forward with the new architecture\n"
        "2. The deadline is set for March 30th\n"
        "3. Each team member should review the PRD by Friday\n\n"
        "Let me know if you have any questions.\n\n"
        "Best regards,\n"
        "Alice Johnson",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "Follow-up: Architecture Meeting Notes"
    msg["From"] = "Alice Johnson <alice@example.com>"
    msg["To"] = "Bob Smith <bob@example.com>"
    msg["Cc"] = "Charlie Davis <charlie@example.com>, Diana Lee <diana@example.com>"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")

    path = FIXTURES_DIR / "sample_plain.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


def create_html_email():
    """HTML newsletter-style email with formatting, links, images."""
    html_content = """\
<html>
<head>
<style>
  body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
  .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
  .content { padding: 20px; }
  .footer { background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; }
  h2 { color: #1e40af; }
  .cta { background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }
</style>
</head>
<body>
<div class="header">
  <h1>Weekly Tech Digest</h1>
  <p>Issue #42 — March 16, 2026</p>
</div>
<div class="content">
  <h2>Top Stories This Week</h2>
  <p>Welcome to this week's edition of the Tech Digest! Here are the highlights:</p>

  <h3>1. New Python Release</h3>
  <p>Python 3.14 has been released with exciting new features including:</p>
  <ul>
    <li><strong>Pattern matching improvements</strong> — better ergonomics for complex patterns</li>
    <li><strong>Performance boost</strong> — 15% faster on average</li>
    <li><a href="https://python.org/downloads">Download now</a></li>
  </ul>

  <h3>2. AI in Production</h3>
  <p>A comprehensive guide to deploying AI models in production environments.
  Learn about <em>model serving</em>, <em>monitoring</em>, and <em>cost optimization</em>.</p>

  <img src="https://example.com/images/ai-production.jpg" alt="AI in Production diagram" width="560">

  <h3>3. Open Source Spotlight</h3>
  <p>This week we're highlighting <a href="https://github.com/example/project">FastExtract</a>,
  a new library for content extraction from any source.</p>

  <p style="text-align: center; margin-top: 30px;">
    <a href="https://example.com/subscribe" class="cta">Subscribe for More</a>
  </p>
</div>
<div class="footer">
  <p>You're receiving this because you signed up at example.com</p>
  <p><a href="https://example.com/unsubscribe">Unsubscribe</a> | <a href="https://example.com/preferences">Preferences</a></p>
</div>
</body>
</html>"""

    plain_content = (
        "Weekly Tech Digest — Issue #42\n\n"
        "Top Stories This Week:\n\n"
        "1. New Python Release — Python 3.14 with pattern matching and 15% performance boost\n"
        "2. AI in Production — Guide to deploying AI models\n"
        "3. Open Source Spotlight — FastExtract library\n\n"
        "Subscribe: https://example.com/subscribe\n"
        "Unsubscribe: https://example.com/unsubscribe"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Weekly Tech Digest #42"
    msg["From"] = "Tech Digest <newsletter@techdigest.example.com>"
    msg["To"] = "subscriber@example.com"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="techdigest.example.com")
    msg["List-Unsubscribe"] = "<https://example.com/unsubscribe>"

    msg.attach(MIMEText(plain_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    path = FIXTURES_DIR / "sample_html.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


def create_attachment_email():
    """Email with a small text file attachment."""
    msg = MIMEMultipart()
    msg["Subject"] = "Q1 Report Attached"
    msg["From"] = "Finance Team <finance@example.com>"
    msg["To"] = "management@example.com"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")

    body = MIMEText(
        "Hi team,\n\n"
        "Please find the Q1 financial report attached.\n\n"
        "Key highlights:\n"
        "- Revenue up 12% YoY\n"
        "- Operating costs reduced by 5%\n"
        "- New customer acquisition exceeded targets\n\n"
        "Let's discuss at the next board meeting.\n\n"
        "Regards,\n"
        "Finance Team",
        "plain",
        "utf-8",
    )
    msg.attach(body)

    # Attach a small text file
    report_content = (
        "Q1 2026 Financial Summary\n"
        "========================\n\n"
        "Revenue: $2,450,000\n"
        "Expenses: $1,890,000\n"
        "Net Income: $560,000\n"
        "Growth: 12% YoY\n"
    ).encode("utf-8")

    attachment = MIMEApplication(report_content, Name="q1-report.txt")
    attachment["Content-Disposition"] = 'attachment; filename="q1-report.txt"'
    msg.attach(attachment)

    # Attach a fake PDF (small binary blob)
    fake_pdf = b"%PDF-1.4 fake pdf content for testing attachment detection"
    pdf_attachment = MIMEApplication(fake_pdf, Name="q1-detailed.pdf")
    pdf_attachment["Content-Disposition"] = 'attachment; filename="q1-detailed.pdf"'
    msg.attach(pdf_attachment)

    path = FIXTURES_DIR / "sample_attachment.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


def create_forwarded_email():
    """Forwarded email with FW: prefix and quoted original."""
    msg = MIMEText(
        "FYI — see the original message below. I think we should consider this for our roadmap.\n\n"
        "- Alice\n\n"
        "---------- Forwarded message ---------\n"
        "From: External Partner <partner@external.com>\n"
        "Date: Mon, Mar 14, 2026 at 2:30 PM\n"
        "Subject: Partnership Opportunity\n"
        "To: Alice Johnson <alice@example.com>\n\n"
        "Hi Alice,\n\n"
        "We'd love to explore a partnership between our companies. We've been working on "
        "a complementary product that could integrate well with your platform.\n\n"
        "Key benefits:\n"
        "1. Shared user base of 50K+ developers\n"
        "2. Technical synergy in content extraction\n"
        "3. Co-marketing opportunities\n\n"
        "Would you be available for a call next week?\n\n"
        "Best,\n"
        "External Partner",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "Fwd: Partnership Opportunity"
    msg["From"] = "Alice Johnson <alice@example.com>"
    msg["To"] = "Bob Smith <bob@example.com>, Charlie Davis <charlie@example.com>"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")

    path = FIXTURES_DIR / "sample_forwarded.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


def create_reply_chain_email():
    """Reply chain with RE: prefix and quoted previous messages."""
    msg = MIMEText(
        "Sounds good, let's go with Option B. I'll set up the migration for Thursday.\n\n"
        "On Mon, Mar 15, 2026 at 10:15 AM, Bob Smith <bob@example.com> wrote:\n"
        "> I've reviewed both options. Here's my take:\n"
        ">\n"
        "> Option A: Simpler but doesn't scale well past 100K users\n"
        "> Option B: More complex upfront but handles our growth projections\n"
        ">\n"
        "> I'd lean toward Option B. What do you think?\n"
        ">\n"
        "> On Mon, Mar 15, 2026 at 9:00 AM, Alice Johnson <alice@example.com> wrote:\n"
        "> > Hey Bob,\n"
        "> >\n"
        "> > We need to decide on the database migration strategy by EOD.\n"
        "> > I've outlined two options in the doc:\n"
        "> > https://docs.example.com/migration-options\n"
        "> >\n"
        "> > Can you review and share your thoughts?\n"
        "> >\n"
        "> > Thanks,\n"
        "> > Alice\n",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "Re: Re: Database Migration Strategy"
    msg["From"] = "Alice Johnson <alice@example.com>"
    msg["To"] = "Bob Smith <bob@example.com>"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")
    msg["In-Reply-To"] = "<reply-msg-id@example.com>"
    msg["References"] = "<original-msg-id@example.com> <reply-msg-id@example.com>"

    path = FIXTURES_DIR / "sample_reply_chain.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


def create_unicode_email():
    """Email with non-ASCII characters and emoji."""
    msg = MIMEText(
        "Hey team! \U0001f680\n\n"
        "Just shipped the new feature! Here's a quick summary:\n\n"
        "\u2705 Authentication flow — complete\n"
        "\u2705 User dashboard — complete\n"
        "\u26a0\ufe0f Rate limiting — needs testing\n"
        "\u274c Admin panel — deferred to v2\n\n"
        "Special thanks to our international contributors:\n"
        "- M\u00fcller (Germany) \U0001f1e9\U0001f1ea\n"
        "- Tanaka \u7530\u4e2d (Japan) \U0001f1ef\U0001f1f5\n"
        "- Garc\u00eda (Spain) \U0001f1ea\U0001f1f8\n"
        "- \u041f\u0435\u0442\u0440\u043e\u0432 (Russia) \U0001f1f7\U0001f1fa\n\n"
        "Caf\u00e9 celebration at 5pm! \u2615\U0001f389\n\n"
        "Cheers,\nThe \u00dcber Team",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "=?utf-8?q?=F0=9F=9A=80_Feature_shipped!_=E2=9C=85?="
    msg["From"] = "=?utf-8?q?=C3=9Cber_Team?= <team@example.com>"
    msg["To"] = "all-hands@example.com"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")

    path = FIXTURES_DIR / "sample_unicode.eml"
    path.write_text(msg.as_string())
    print(f"Created: {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    print("Generating email test fixtures...")
    print(f"Output directory: {FIXTURES_DIR}")
    print()
    create_plain_email()
    create_html_email()
    create_attachment_email()
    create_forwarded_email()
    create_reply_chain_email()
    create_unicode_email()
    print("\nDone! All fixtures created.")
