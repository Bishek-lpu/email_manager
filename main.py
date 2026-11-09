
import os
from email_manager import EmailManager

USERNAME = os.environ["EMAIL_USERNAME"]
PASSWORD = os.environ["EMAIL_APP_PASSWORD"]

manager = EmailManager(
    username=USERNAME,
    password=PASSWORD,

    imap_host="mail.onionmail.org",
    imap_port=993,

    smtp_host="YOUR_SMTP_HOST",
    smtp_port=465
)


# 1. Read latest 10 emails
with manager:
    emails = manager.get_emails(limit=10)

    for item in emails:
        print("\n-------------------------")
        print("ID:", item["id"])
        print("Sender:", item["from_email"])
        print("Subject:", item["subject"])
        print("Date:", item["date"])
        print("Body:", item["text"])


# 2. Read emails from a specific sender
with manager:
    emails = manager.get_emails_by_sender(
        "security@example.com",
        limit=20
    )

    for item in emails:
        print(item["subject"], item["text"])


# 3. Search by subject
with manager:
    emails = manager.get_emails(
        subject="Verification",
        limit=10
    )


# 4. Get all unique senders
with manager:
    senders = manager.get_all_senders()

    for sender in senders:
        print(sender["name"], sender["email"])


# 5. Extract OTP from a particular sender
with manager:
    result = manager.get_otp(
        sender_email="security@example.com",
        subject="Verification",
        limit=10
    )

    if result:
        print("OTP:", result["otp"])
        print("Received:", result["date"])
    else:
        print("OTP not found")


# 6. Send an email
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="Test Email",
        body="Hello, this is a test email."
    )


# 7. Send HTML email
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="HTML Email",
        body="Your email client does not support HTML.",
        html_body="<h1>Hello!</h1><p>Welcome.</p>"
    )


# 8. Send attachment
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="Document",
        body="Please find attached.",
        attachments=["document.pdf"]
    )


# 9. Download attachments
with manager:
    files = manager.download_attachments(
        email_id="123",
        download_dir="downloads"
    )

    print(files)


# 10. Mark email as read
with manager:
    manager.mark_read("123")


# 11. Mark email as unread
with manager:
    manager.mark_unread("123")


# 12. Delete email
with manager:
    manager.delete_email("123")


# 13. Reply to email
with manager:
    manager.reply_email(
        email_id="123",
        body="Thank you for your email."
    )


# 14. Forward email
with manager:
    manager.forward_email(
        email_id="123",
        recipient="another@example.com"
    )


# 15. List folders
with manager:
    folders = manager.list_folders()

    for folder in folders:
        print(folder)
