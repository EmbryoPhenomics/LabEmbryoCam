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

try:
    with open('../app_config.json', 'r') as conf:
        app_conf = json.load(conf)
        red_fact = app_conf['reduction_factor']
        cores = app_conf['compress_cores']
except FileNotFoundError:
    with open('./app_config.json', 'r') as conf:
        app_conf = json.load(conf)
        red_fact = app_conf['reduction_factor']
        cores = app_conf['compress_cores']
except:
    raise

# Declared here so it's not constantly created whenever a writer is made below
fourcc = cv2.VideoWriter_fourcc(*'MPEG')
def compress_video(file):
    video = cv2.VideoCapture(file)

    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)*red_fact)
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)*red_fact)
    outpath = re.sub('.avi', '_mp.avi', file)

    writer = cv2.VideoWriter(outpath, fourcc, fps, (width, height))

    while video.isOpened():
        success, frame = video.read()
        if success == False:
            break

        frame = cv2.resize(frame, (width, height))            
        writer.write(frame)

    video.release()
    writer.release()

    return outpath

def compress_video_par(files):
    print('LabEP: Compressing video for sending over email...')
    pool = mp.Pool(processes=cores)
    out_files = list(tqdm(pool.imap(compress_video, files), total=len(files)))
    pool.close()

    return out_files

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

        if isinstance(attachments, list):
            for att in attachments: pack_attachment(att)
        else:
            pack_attachment(attachments)

        self.server.sendmail(self.username, self.username, msg.as_string())

    def close(self):
        if self.isLoggedIn:
            self.server.quit()

# # Test
# import time
# import os
# import vuba

# files = glob.glob('/home/z/github/heartcv/validate/video/ciona/*.avi')
# t1 = time.time()

# file = files[0]

# video = vuba.Video(file)
# img = video.read(0, grayscale=False)
# cv2.imwrite(re.sub('.avi', '.png', file), img)
# video.close()

# file = re.sub('.avi', '.png', file)

# text = """\
# LabEP update: Timepoint 1:

# Timepoint: 1
# No. of embryos: 60
# No. of images acquired: 36000
# Next acquisition in: 1 hr"""

# emails = Emails()
# emails.login('ziadibbini@gmail.com', 'htrsrsuvhgcidvzl')
# emails.send('Test', text, file)
# os.remove(file)
# emails.close()

# t2 = time.time()
# print(t2 - t1)