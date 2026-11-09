# 📧 Python Email Manager

<p align="center">
  <b>A powerful, reusable Python email management library.</b>
  <br/>
  Read, search, send, organize, and manage emails programmatically using IMAP and SMTP.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Protocol-IMAP%20%2B%20SMTP-green" />
  <img src="https://img.shields.io/badge/Security-TLS-orange" />
  <img src="https://img.shields.io/badge/License-MIT-purple" />
</p>

---

## ✨ Overview

**Python Email Manager** is a feature-rich email client library designed to give developers programmatic control over their email accounts.

Built using Python's standard libraries, it supports email retrieval, sender filtering, OTP extraction, attachment management, email composition, forwarding, and much more.

Whether you're building an automation system, notification service, email processing application, or personal email client, this library provides a simple interface to manage your emails.

## 🚀 Features

| Feature | Description |
|---|---|
| 📥 Email Retrieval | Fetch latest emails from your inbox |
| 🔍 Email Search | Search by sender, subject, keyword, and date |
| 👤 Sender Management | Extract unique sender email addresses |
| 🔐 OTP Extraction | Automatically extract verification codes from specific senders |
| 📤 Email Composition | Compose and send emails |
| ↩️ Reply & Forward | Reply to and forward existing messages |
| 📎 Attachments | Download and send email attachments |
| 📂 Folder Management | List and access email folders |
| 📖 Read Status | Mark emails as read or unread |
| 🗑️ Email Deletion | Delete messages programmatically |
| 🌐 HTML Support | Read and send HTML emails |
| 🔒 Secure Connection | SSL/TLS encrypted IMAP and SMTP connections |

## 📋 Requirements

- Python 3.9+
- An email account with IMAP access enabled
- SMTP access for sending emails
- An application-specific password, if required by your provider

The implementation primarily uses Python standard libraries.

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/USERNAME/python-email-manager.git

cd python-email-manager
```

No additional package installation is required for the core implementation.

## ⚙️ Configuration

Set your email credentials as environment variables.

**Linux / macOS**

```bash
export EMAIL_USERNAME="your_email@onionmail.org"
export EMAIL_APP_PASSWORD="your_app_password"
```

**Windows PowerShell**

```powershell
$env:EMAIL_USERNAME="your_email@onionmail.org"
$env:EMAIL_APP_PASSWORD="your_app_password"
```

## 🏁 Quick Start

Create an `email_manager.py` file containing the `EmailManager` implementation.

Create `main.py`:

```python
import os
from email_manager import EmailManager

manager = EmailManager(
    username=os.environ["EMAIL_USERNAME"],
    password=os.environ["EMAIL_APP_PASSWORD"],
    imap_host="mail.onionmail.org",
    imap_port=993,
    smtp_host="YOUR_SMTP_HOST",
    smtp_port=465
)

with manager:
    emails = manager.get_emails(limit=10)

    for item in emails:
        print("From:", item["from_email"])
        print("Subject:", item["subject"])
        print("Body:", item["text"])
```

Run:

```bash
python main.py
```

## 📖 Usage Examples

### 1. Read Latest Emails

```python
with manager:
    emails = manager.get_emails(limit=20)

    for item in emails:
        print(item)
```

### 2. Read Emails From a Specific Sender

```python
with manager:
    emails = manager.get_emails_by_sender(
        sender_email="security@example.com",
        limit=10
    )

    for item in emails:
        print(item["subject"])
        print(item["text"])
```

### 3. Search Emails by Subject

```python
with manager:
    emails = manager.get_emails(
        subject="Verification",
        limit=10
    )
```

### 4. Extract OTP Automatically

Retrieve an OTP from emails received from a specific sender.

```python
with manager:
    result = manager.get_otp(
        sender_email="security@example.com",
        subject="Verification",
        limit=10
    )

    if result:
        print("OTP:", result["otp"])
    else:
        print("OTP not found")
```

### 5. Get All Unique Senders

```python
with manager:
    senders = manager.get_all_senders()

    for sender in senders:
        print(sender["name"], sender["email"])
```

### 6. Compose and Send Email

```python
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="Hello",
        body="This is a test email."
    )
```

### 7. Send HTML Email

```python
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="Welcome",
        body="Your email client does not support HTML.",
        html_body="<h1>Welcome!</h1><p>Thank you.</p>"
    )
```

### 8. Send Attachments

```python
with manager:
    manager.send_email(
        to="recipient@example.com",
        subject="Documents",
        body="Please find the attached document.",
        attachments=["document.pdf"]
    )
```

### 9. Download Attachments

```python
with manager:
    files = manager.download_attachments(
        email_id="123",
        download_dir="downloads"
    )

    print(files)
```

### 10. Reply and Forward

```python
with manager:
    manager.reply_email(
        email_id="123",
        body="Thank you for your message."
    )

    manager.forward_email(
        email_id="123",
        recipient="another@example.com"
    )
```

### 11. Manage Email Status

```python
with manager:
    manager.mark_read("123")
    manager.mark_unread("123")
```

### 12. Delete Emails

```python
with manager:
    manager.delete_email("123")
```

### 13. List Email Folders

```python
with manager:
    folders = manager.list_folders()

    for folder in folders:
        print(folder)
```

## 📁 Project Structure

```text
python-email-manager/
│
├── email_manager.py
├── main.py
├── README.md
├── .gitignore
└── requirements.txt
```

## 🔐 Security Recommendations

- Never hardcode email credentials in source code.
- Use environment variables or a secure secrets manager.
- Always use encrypted IMAP and SMTP connections.
- Never expose application passwords in GitHub repositories.
- Restrict access to downloaded email attachments.
- Validate sender addresses before processing sensitive messages.
- Treat email content and extracted OTPs as sensitive information.

## ⚠️ Limitations

- IMAP and SMTP functionality depends on your email provider.
- SMTP hostname and authentication requirements vary by provider.
- OTP extraction uses pattern matching and may not recognize every email format.
- Large inboxes can require pagination or more efficient searching.
- Some email providers restrict IMAP/SMTP access.

## 🛠️ Technologies

- **Python** – Core programming language
- **IMAP4 SSL** – Receiving and managing emails
- **SMTP SSL / STARTTLS** – Sending emails
- **Email Package** – Parsing and composing messages
- **Regular Expressions** – OTP detection

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository.
2. Create a new feature branch.
3. Implement your changes.
4. Submit a pull request.

## 📜 License

This project is licensed under the MIT License.

## ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub.

---

<p align="center">
  <b>Built with ❤️ using Python</b>
  <br/>
  <sub>Automate your inbox. Simplify your workflow.</sub>
</p>
