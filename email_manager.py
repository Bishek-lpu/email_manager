
import imaplib
import smtplib
import email
import re
import os
import mimetypes
import html as html_lib

from pathlib import Path
from email import policy
from email.message import EmailMessage
from email.header import decode_header
from email.utils import parseaddr, getaddresses
from datetime import datetime


class EmailManager:

    def __init__(
        self,
        username,
        password,
        imap_host="mail.onionmail.org",
        imap_port=993,
        smtp_host=None,
        smtp_port=465,
        timeout=30
    ):
        self.username = username
        self.password = password

        self.imap_host = imap_host
        self.imap_port = imap_port

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

        self.timeout = timeout
        self.imap = None

    # -----------------------------------------
    # Utility functions
    # -----------------------------------------

    @staticmethod
    def decode_value(value):
        if not value:
            return ""

        decoded = []

        for part, encoding in decode_header(str(value)):
            if isinstance(part, bytes):
                decoded.append(
                    part.decode(encoding or "utf-8", errors="replace")
                )
            else:
                decoded.append(part)

        return "".join(decoded)

    @staticmethod
    def extract_email(address):
        return parseaddr(address)[1]

    # -----------------------------------------
    # IMAP CONNECTION
    # -----------------------------------------

    def connect(self):
        if self.imap is not None:
            try:
                if self.imap.state == "SELECTED":
                    return True
                if self.imap.state == "AUTH":
                    return True
            except Exception:
                self.imap = None

        self.imap = imaplib.IMAP4_SSL(
            self.imap_host,
            self.imap_port,
            timeout=self.timeout
        )

        self.imap.login(self.username, self.password)

        return True

    def disconnect(self):
        if self.imap:
            try:
                self.imap.logout()
            except Exception:
                pass

            self.imap = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _select_folder(self, folder="INBOX", readonly=True):
        self.connect()

        status, data = self.imap.select(
            folder,
            readonly=readonly
        )

        if status != "OK":
            raise RuntimeError(f"Unable to select folder: {folder}")

        return data

    # -----------------------------------------
    # FOLDER MANAGEMENT
    # -----------------------------------------

    def list_folders(self):
        self.connect()

        status, folders = self.imap.list()

        if status != "OK":
            return []

        return [
            item.decode(errors="replace")
            for item in folders
            if item
        ]

    # -----------------------------------------
    # SEARCH EMAILS
    # -----------------------------------------

    def search_emails(
        self,
        sender=None,
        subject=None,
        keyword=None,
        since=None,
        before=None,
        unseen=False,
        seen=False,
        folder="INBOX"
    ):

        self._select_folder(folder)

        criteria = ["ALL"]

        if sender:
            criteria.extend([
                "FROM",
                imaplib.IMAP4._quote(sender)
            ])

        if subject:
            criteria.extend([
                "SUBJECT",
                imaplib.IMAP4._quote(subject)
            ])

        if keyword:
            criteria.extend([
                "BODY",
                imaplib.IMAP4._quote(keyword)
            ])

        if since:
            date = since.strftime("%d-%b-%Y") if isinstance(
                since, datetime
            ) else since

            criteria.extend(["SINCE", date])

        if before:
            date = before.strftime("%d-%b-%Y") if isinstance(
                before, datetime
            ) else before

            criteria.extend(["BEFORE", date])

        if unseen:
            criteria.append("UNSEEN")

        if seen:
            criteria.append("SEEN")

        status, data = self.imap.uid(
            "search",
            None,
            *criteria
        )

        if status != "OK":
            return []

        return data[0].split()

    # -----------------------------------------
    # EMAIL BODY EXTRACTION
    # -----------------------------------------

    @staticmethod
    def extract_body(msg):

        plain_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():

                if part.get_content_disposition() == "attachment":
                    continue

                content_type = part.get_content_type()

                try:
                    content = part.get_content()
                except Exception:
                    continue

                if content_type == "text/plain" and not plain_body:
                    plain_body = content

                elif content_type == "text/html" and not html_body:
                    html_body = content

        else:
            try:
                content = msg.get_content()

                if msg.get_content_type() == "text/html":
                    html_body = content
                else:
                    plain_body = content

            except Exception:
                pass

        # Convert HTML into readable text if plain text is unavailable.
        if not plain_body and html_body:
            text = re.sub(
                r"(?is)<(script|style).*?>.*?</\1>",
                "",
                html_body
            )
            text = re.sub(r"(?i)<br\s*/?>", "\n", text)
            text = re.sub(r"(?i)</p>", "\n", text)
            text = re.sub(r"<[^>]+>", " ", text)

            plain_body = html_lib.unescape(text).strip()

        return {
            "text": plain_body,
            "html": html_body
        }

    # -----------------------------------------
    # FETCH SINGLE EMAIL
    # -----------------------------------------

    def get_email(self, email_id, folder="INBOX", mark_read=False):

        self._select_folder(
            folder,
            readonly=not mark_read
        )

        status, data = self.imap.uid(
            "fetch",
            str(email_id),
            "(RFC822)"
        )

        if status != "OK" or not data:
            return None

        raw_email = next(
            (
                item[1]
                for item in data
                if isinstance(item, tuple)
            ),
            None
        )

        if not raw_email:
            return None

        msg = email.message_from_bytes(
            raw_email,
            policy=policy.default
        )

        body = self.extract_body(msg)

        if mark_read:
            self.imap.uid(
                "store",
                str(email_id),
                "+FLAGS",
                r"(\Seen)"
            )

        return {
            "id": str(email_id),
            "from": self.decode_value(msg["From"]),
            "from_email": parseaddr(str(msg["From"] or ""))[1],
            "to": self.decode_value(msg["To"]),
            "cc": self.decode_value(msg["Cc"]),
            "reply_to": self.decode_value(msg["Reply-To"]),
            "subject": self.decode_value(msg["Subject"]),
            "date": str(msg["Date"] or ""),
            "message_id": str(msg["Message-ID"] or ""),
            "text": body["text"],
            "html": body["html"],
            "attachments": self.get_attachment_names(msg)
        }

    # -----------------------------------------
    # GET LATEST EMAILS
    # -----------------------------------------

    def get_emails(
        self,
        limit=10,
        folder="INBOX",
        sender=None,
        subject=None,
        keyword=None,
        unseen=False
    ):

        ids = self.search_emails(
            sender=sender,
            subject=subject,
            keyword=keyword,
            unseen=unseen,
            folder=folder
        )

        results = []

        for email_id in reversed(ids[-limit:]):

            item = self.get_email(
                email_id,
                folder=folder
            )

            if item:
                results.append(item)

        return results

    # -----------------------------------------
    # SEARCH BY SPECIFIC SENDER
    # -----------------------------------------

    def get_emails_by_sender(
        self,
        sender_email,
        limit=20,
        folder="INBOX"
    ):

        return self.get_emails(
            limit=limit,
            sender=sender_email,
            folder=folder
        )

    # -----------------------------------------
    # GET ALL UNIQUE SENDERS
    # -----------------------------------------

    def get_all_senders(self, folder="INBOX", limit=None):

        ids = self.search_emails(folder=folder)

        if limit:
            ids = ids[-limit:]

        senders = {}

        for email_id in ids:

            item = self.get_email(
                email_id,
                folder=folder
            )

            if not item:
                continue

            address = item["from_email"]

            if address:
                senders[address.lower()] = {
                    "email": address,
                    "name": parseaddr(item["from"])[0]
                }

        return list(senders.values())

    # -----------------------------------------
    # FIND OTP FROM SPECIFIC SENDER
    # -----------------------------------------

    def get_otp(
        self,
        sender_email,
        subject=None,
        limit=10,
        otp_length=(4, 8),
        folder="INBOX"
    ):

        emails = self.get_emails(
            limit=limit,
            sender=sender_email,
            subject=subject,
            folder=folder
        )

        min_len, max_len = otp_length

        # Prefer numbers appearing near OTP-related keywords.
        contextual_pattern = re.compile(
            rf"(?i)(?:otp|verification code|security code|"
            rf"one.time password|authentication code)"
            rf"\D{{0,40}}(\d{{{min_len},{max_len}}})"
        )

        for item in emails:

            content = (
                item["subject"] + "\n" +
                item["text"]
            )

            match = contextual_pattern.search(content)

            if match:
                return {
                    "otp": match.group(1),
                    "sender": item["from_email"],
                    "subject": item["subject"],
                    "date": item["date"],
                    "email_id": item["id"]
                }

        return None

    # -----------------------------------------
    # GET ALL EMAIL ADDRESSES IN A MESSAGE
    # -----------------------------------------

    def get_message_addresses(self, email_id, folder="INBOX"):

        self._select_folder(folder)

        status, data = self.imap.uid(
            "fetch",
            str(email_id),
            "(RFC822)"
        )

        if status != "OK":
            return {}

        raw = next(
            (x[1] for x in data if isinstance(x, tuple)),
            None
        )

        if not raw:
            return {}

        msg = email.message_from_bytes(
            raw,
            policy=policy.default
        )

        return {
            "from": getaddresses([str(msg.get("From", ""))]),
            "to": getaddresses([str(msg.get("To", ""))]),
            "cc": getaddresses([str(msg.get("Cc", ""))]),
            "bcc": getaddresses([str(msg.get("Bcc", ""))])
        }

    # -----------------------------------------
    # ATTACHMENTS
    # -----------------------------------------

    @staticmethod
    def get_attachment_names(msg):

        attachments = []

        for part in msg.walk():

            filename = part.get_filename()

            if filename:
                attachments.append(
                    EmailManager.decode_value(filename)
                )

        return attachments

    def download_attachments(
        self,
        email_id,
        download_dir="attachments",
        folder="INBOX"
    ):

        self._select_folder(folder)

        status, data = self.imap.uid(
            "fetch",
            str(email_id),
            "(RFC822)"
        )

        if status != "OK":
            return []

        raw = next(
            (x[1] for x in data if isinstance(x, tuple)),
            None
        )

        if not raw:
            return []

        msg = email.message_from_bytes(raw, policy=policy.default)

        directory = Path(download_dir)
        directory.mkdir(parents=True, exist_ok=True)

        saved = []

        for part in msg.walk():

            filename = part.get_filename()

            if not filename:
                continue

            filename = Path(
                self.decode_value(filename)
            ).name

            if not filename:
                continue

            filepath = directory / filename

            # Avoid overwriting existing attachments.
            if filepath.exists():
                filepath = directory / (
                    filepath.stem + "_" +
                    str(email_id) + filepath.suffix
                )

            filepath.write_bytes(part.get_payload(decode=True))

            saved.append(str(filepath))

        return saved

    # -----------------------------------------
    # MARK READ / UNREAD
    # -----------------------------------------

    def mark_read(self, email_id, folder="INBOX"):

        self._select_folder(folder, readonly=False)

        return self.imap.uid(
            "store",
            str(email_id),
            "+FLAGS",
            r"(\Seen)"
        )

    def mark_unread(self, email_id, folder="INBOX"):

        self._select_folder(folder, readonly=False)

        return self.imap.uid(
            "store",
            str(email_id),
            "-FLAGS",
            r"(\Seen)"
        )

    # -----------------------------------------
    # DELETE EMAIL
    # -----------------------------------------

    def delete_email(self, email_id, folder="INBOX"):

        self._select_folder(folder, readonly=False)

        status, data = self.imap.uid(
            "store",
            str(email_id),
            "+FLAGS",
            r"(\Deleted)"
        )

        if status == "OK":
            self.imap.expunge()

        return status == "OK"

    # -----------------------------------------
    # SMTP CONNECTION
    # -----------------------------------------

    def _smtp_connect(self):

        if not self.smtp_host:
            raise ValueError("Configure your SMTP host first")

        smtp = smtplib.SMTP_SSL(
            self.smtp_host,
            self.smtp_port,
            timeout=self.timeout
        )

        smtp.login(
            self.username,
            self.password
        )

        return smtp

    # -----------------------------------------
    # COMPOSE AND SEND EMAIL
    # -----------------------------------------

    def send_email(
        self,
        to,
        subject,
        body,
        cc=None,
        bcc=None,
        html_body=None,
        attachments=None
    ):

        msg = EmailMessage()

        msg["From"] = self.username
        msg["To"] = ", ".join(to) if isinstance(to, list) else to
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc) if isinstance(cc, list) else cc

        msg.set_content(body)

        if html_body:
            msg.add_alternative(
                html_body,
                subtype="html"
            )

        for filepath in attachments or []:

            path = Path(filepath)

            if not path.is_file():
                raise FileNotFoundError(filepath)

            content_type, _ = mimetypes.guess_type(str(path))

            if content_type is None:
                content_type = "application/octet-stream"

            maintype, subtype = content_type.split("/", 1)

            msg.add_attachment(
                path.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=path.name
            )

        recipients = []

        for field in (to, cc, bcc):
            if field:
                recipients.extend(
                    field if isinstance(field, list) else [field]
                )

        with self._smtp_connect() as smtp:
            smtp.send_message(
                msg,
                to_addrs=recipients
            )

        return True

    # -----------------------------------------
    # REPLY TO EMAIL
    # -----------------------------------------

    def reply_email(
        self,
        email_id,
        body,
        folder="INBOX"
    ):

        item = self.get_email(email_id, folder)

        if not item:
            raise ValueError("Email not found")

        recipient = item["reply_to"] or item["from"]

        subject = item["subject"]

        if not subject.lower().startswith("re:"):
            subject = "Re: " + subject

        return self.send_email(
            to=parseaddr(recipient)[1] or recipient,
            subject=subject,
            body=body
        )

    # -----------------------------------------
    # FORWARD EMAIL
    # -----------------------------------------

    def forward_email(
        self,
        email_id,
        recipient,
        folder="INBOX"
    ):

        item = self.get_email(email_id, folder)

        if not item:
            raise ValueError("Email not found")

        body = (
            f"---------- Forwarded Message ----------\n"
            f"From: {item['from']}\n"
            f"Date: {item['date']}\n"
            f"Subject: {item['subject']}\n\n"
            f"{item['text']}"
        )

        return self.send_email(
            to=recipient,
            subject="Fwd: " + item["subject"],
            body=body
        )
