"""
Utils functions to send an email via Gmail, extended to accept embedded files. Most of the code is due to
https://github.com/jeremyephron/simplegmail/blob/66e776d5211042b2868664ca800bdfc45323732c/simplegmail/gmail.py
"""

from typing import Optional, List
import base64
import mimetypes
import pathlib

from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http
from oauth2client import client, file, tools
from oauth2client.clientsecrets import InvalidClientSecretsError


class Message:
    """Class representing a message, ready to be sent
    """

    def __init__(
        self,
        sender: str,
        recipient: str,
        subject: str = '',
        msg_html: str = '',
        msg_plain: str = '',
        cc: List[str] = None,
        bcc: List[str] = None
    ):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.msg_plain = msg_plain
        self.msg_html = msg_html
        self.cc = [] if cc is None else cc
        self.bcc = [] if bcc is None else bcc

        self.html_attachments: List[MIMEBase] = []
        self.extra_attachments: List[MIMEBase] = []

    def add_attachment(self, path: pathlib.Path) -> None:
        """Attach a file as a normal attachment"""

        attachment = Message.create_attachment_from_file(path)
        self.extra_attachments.append(attachment)

    def add_html_attachment(self, path: pathlib.Path, cid: str = None) -> None:
        """Add a HTML inline attachment (to be embedded).

        If `cid` is `None`, the `cid` is taken as the file basename.
        """

        if cid is None:
            cid = path.name

        attachment = Message.create_attachment_from_file(path, 'inline', cid)
        self.html_attachments.append(attachment)

    @staticmethod
    def create_attachment_from_file(path: pathlib.Path, disposition: str = 'attachment', cid: str = None) -> MIMEBase:
        """Create an attachment from a file"""

        content_type, encoding = mimetypes.guess_type(path)
        name = path.name

        # backup to octet-stream if any
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        # create attachment
        main_type, sub_type = content_type.split('/', 1)
        with path.open('rb') as f:
            raw_data = f.read()
            if main_type == 'text':
                attachment = MIMEText(raw_data.decode('UTF-8'), _subtype=sub_type)
            elif main_type == 'image':
                attachment = MIMEImage(raw_data, _subtype=sub_type)
            elif main_type == 'audio':
                attachment = MIMEAudio(raw_data, _subtype=sub_type)
            elif main_type == 'application':
                attachment = MIMEApplication(raw_data, _subtype=sub_type)
            else:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(raw_data)

        # add info
        attachment.add_header('Content-Disposition', disposition, filename=name)

        if cid is not None:
            attachment.add_header('Content-ID', '<{}>'.format(cid))

        return attachment

    def prepare(self) -> dict:
        """
        Get the message in a form that the Gmail API understand
        """

        has_attachments = len(self.extra_attachments) != 0 or len(self.html_attachments) != 0

        # create the message
        msg = MIMEMultipart('mixed' if has_attachments else 'alternative')
        msg['To'] = self.recipient
        msg['From'] = self.sender
        msg['Subject'] = self.subject

        if len(self.cc) > 0:
            msg['Cc'] = ', '.join(self.cc)

        if len(self.bcc) > 0:
            msg['Bcc'] = ', '.join(self.bcc)

        # attach the text(s) to the message correctly
        attachments = []
        attach_plain = MIMEText(self.msg_plain, 'plain')
        attach_html = MIMEText(self.msg_html, 'html')

        if not has_attachments:
            if self.msg_plain:
                attachments.append(attach_plain)
            if self.msg_html:
                attachments.append(attach_html)
        else:
            attachment_alt = MIMEMultipart('alternative')
            attach_related = MIMEMultipart('related')

            if self.msg_plain:
                attachment_alt.attach(attach_plain)

            if self.msg_html:
                attach_related.attach(attach_html)

                # add the HTML attachments to the related part
                for attachment in self.html_attachments:
                    attach_related.attach(attachment)

            attachment_alt.attach(attach_related)
            attachments.append(attachment_alt)

        # add other attachments
        attachments.extend(self.extra_attachments)

        # attach
        for attachment in attachments:
            msg.attach(attachment)

        # get dict
        return {
            'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()
        }


class Gmail:
    """
    The Gmail object, used as entry point for the Gmail API.
    """

    # Allow Gmail to read and write emails, and access settings like aliases.
    _SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.settings.basic'
    ]

    def __init__(
            self,
            client_secret_file: str = 'client_secret.json',
            creds_file: str = 'gmail_token.json',
            _creds: Optional[client.Credentials] = None
    ) -> None:
        self.client_secret_file = client_secret_file
        self.creds_file = creds_file

        try:
            if _creds:
                self.creds = _creds
            else:
                store = file.Storage(self.creds_file)
                self.creds = store.get()

            if not self.creds or self.creds.invalid:
                # Will ask you to authenticate an account in your browser.
                flow = client.flow_from_clientsecrets(self.client_secret_file, self._SCOPES)
                self.creds = tools.run_flow(flow, store)

            self.service = build('gmail', 'v1', http=self.creds.authorize(Http()), cache_discovery=False)

        except InvalidClientSecretsError:
            raise FileNotFoundError(
                "Your 'client_secret.json' file is nonexistent. Make sure "
                'the file is in the root directory of your application. If '
                "you don't have a client secrets file, go to https://"
                'developers.google.com/gmail/api/quickstart/python, and '
                'follow the instructions listed there.'
            )

    def send(self, message: Message, user_id: str = 'me') -> None:
        """Send a message
        """

        msg = message.prepare()

        try:
            req = self.service.users().messages().send(userId=user_id, body=msg)
            req.execute()

        except HttpError as error:
            # Pass along the error
            raise error
