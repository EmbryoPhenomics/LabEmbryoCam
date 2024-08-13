import cv2
import re
from tqdm import tqdm
import glob
import json
import multiprocessing as mp
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

class Emails:
    def __init__(self):
        self.server = None
        self.username = None
        self.password = None
        self.isLoggedIn = False

    def login(self, username, password):
        self.server = smtplib.SMTP("smtp.gmail.com:587")
        self.server.starttls()

        self.username = username
        self.password = password
        self.server.login(username, password)
        self.isLoggedIn = True

    def send(self, subject, content, attachments):
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = self.username
        msg["Subject"] = subject

        msg.attach(MIMEText(content, "plain"))

        def pack_attachment(att):
            ctype, encoding = mimetypes.guess_type(att)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"

            maintype, subtype = ctype.split("/", 1)

            if maintype == "text":
                fp = open(att)
                # Note: we should handle calculating the charset
                attachment = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "image":
                fp = open(att, "rb")
                attachment = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "audio":
                fp = open(att, "rb")
                attachment = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(att, "rb")
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(fp.read())
                fp.close()
                encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", "attachment", filename=att)
            msg.attach(attachment)

        if attachments is not None:
            if isinstance(attachments, list):
                for att in attachments: pack_attachment(att)
            else:
                pack_attachment(attachments)

        self.server.sendmail(self.username, self.username, msg.as_string())

    def close(self):
        if self.isLoggedIn:
            self.server.quit()
