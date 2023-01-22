import json
import logging
import os
import re
from urllib.parse import urlparse

import ffmpy
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, redirect, request, url_for
from videoprops import get_video_properties

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)
load_dotenv()

app = Flask(__name__)
env = os.environ
telegram_bot_token = env.get("telegram_bot_token")
debugging = False


def get_media_url(account, vid):
    header = {
        "Accept": "application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr"
    }
    j = json.loads(
        requests.get(
            "https://edge.api.brightcove.com/playback/v1/accounts/"
            + account
            + "/videos/"
            + vid,
            headers=header,
        ).text
    )
    try:
        return j["sources"][5]["src"]
    except:
        return j["sources"][1]["src"]


def download_m3u8(m3u8, filename):
    ff = ffmpy.FFmpeg(
        global_options="-y -hide_banner -loglevel warning",
        inputs={m3u8: None},
        outputs={filename: "-c copy"},
    )
    ff.run()


def send_telegram(input, type, bot=telegram_bot_token, notification=False):
    global debugging
    if debugging == True:
        return
    notification = not notification
    if type == "text":
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendMessage",
            params={
                "chat_id": "1024110161",
                "text": input,
                "disable_notification": notification,
            },
        )
    elif type == "voice":
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendVoice",
            params={"chat_id": "1024110161", "disable_notification": notification},
            files={"voice": open(input, "rb")},
        )
    elif type == "animation":
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendAnimation",
            params={"chat_id": "1024110161", "disable_notification": notification},
            files={"animation": open(input, "rb")},
        )
    elif type == "photo":
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendPhoto",
            params={
                "chat_id": "1024110161",
                "photo": input,
                "disable_notification": notification,
            },
        )
    elif type == "video_file":
        width = get_video_properties(input)["width"]
        height = get_video_properties(input)["height"]
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendVideo",
            params={
                "chat_id": "1024110161",
                "width": width,
                "height": height,
                "disable_notification": notification,
            },
            files={"video": open(input, "rb")},
        )
    elif type == "video_url":
        r = requests.post(
            "https://api.telegram.org/" + bot + "/sendVideo",
            params={
                "chat_id": "1024110161",
                "video": input,
                "disable_notification": notification,
            },
        )
    return r


@app.route("/1nichi1aika")
def _1nichi1aika():
    # 發出登入requests
    session = requests.session()
    session.post(
        "https://fc.kobayashiaika.jp/s/n85/login",
        data={"idpwLgid": env.get("email"), "idpwLgpw": env.get("pw"), "mode": "LOGIN"},
    )
    r = session.get("https://fc.kobayashiaika.jp/s/n85/lot/top_uranai")
    r2 = session.get("https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list")

    # 用beautifulsoup處理網頁
    uranai_page = BeautifulSoup(r.text, "html.parser")
    diary_page = BeautifulSoup(r2.text, "html.parser")

    # 取得日期
    date = (
        diary_page.find("div", class_="textBox")
        .find_all("p")[0]
        .string.replace(" ", "")
        .replace("\n", "")
    )

    # 取得文字內容
    diary = (
        diary_page.find("div", class_="textBox").find_all("p")[1].text.replace(" ", "")
    )  # .replace('\n','')

    # 判斷媒體類別
    image_or_movie = (
        diary_page.find("li", class_="item").find_all("div")[1].get("class")[0]
    )

    # 根據媒體類別取得網址
    if image_or_movie == "image":
        content_url = (
            str(diary_page.find("li", class_="item").find("div", class_="image").img)
            .replace('<img src="', "https://fc.kobayashiaika.jp")
            .replace('"/>', "")
        )
    elif image_or_movie == "movie":
        account = diary_page.find("li", class_="item").find("video")["data-account"]
        vid = diary_page.find("li", class_="item").find("video")["data-video-id"]
        content_url = get_media_url(account, vid)

    # 取得占卜點數和gif
    point = uranai_page.find("p", class_="point").string.replace("\n", "")
    uranai_gif = (
        str(uranai_page.find("p", class_="image").img)
        .replace('<img src="', "https://fc.kobayashiaika.jp")
        .replace('"/>', "")
    )

    # 取得占卜語音
    account = uranai_page.find("div", class_="voice").video["data-account"]
    vid = uranai_page.find("div", class_="voice").video["data-video-id"]
    uranai_voice = get_media_url(account, vid)
    download_m3u8(uranai_voice, "voice.mp4")

    # 傳送訊息(telegram)占卜點數
    send_telegram(point, "text")

    # 傳送訊息(telegram)占卜語音
    send_telegram("voice.mp4", "voice")

    # 傳送訊息(telegram)占卜gif
    open("uranai.gif", "wb").write(requests.get(uranai_gif).content)
    send_telegram("uranai.gif", "animation")

    # 傳送訊息(telegram)文字
    send_telegram(date + "\n" + diary, "text", notification=True)

    # 傳送照片或影片
    if image_or_movie == "image":
        send_telegram(content_url, "photo")
    elif image_or_movie == "movie":
        parse = urlparse(content_url)
        if parse.path[parse.path.find(".") + 1 :] == "m3u8":
            download_m3u8(content_url, "video.mp4")
            send_telegram("video.mp4", "video_file")
        else:
            # cleanup url
            content_url = re.sub(r"\?pubId=\d*&videoId=\d*", "", content_url)
            send_telegram(content_url, "video_url")
    # 返回結果(網頁)
    return date + "\n" + diary + "\n" + content_url


@app.route("/radio")
def radio():
    # login 
    session = requests.Session()
    session.post(
        "https://fc.kobayashiaika.jp/s/n85/login",
        data={"idpwLgid": env.get("email"), "idpwLgpw": env.get("pw"), "mode": "LOGIN"},
    )
    r = session.get("https://fc.kobayashiaika.jp/s/n85/diary/fc_radioand/list")

    # parse html
    radio_soup = BeautifulSoup(r.text, "html.parser")
    object_ = radio_soup.find("ul", class_="radioList").find_all("li")[0]

    # get title
    name = (
        object_.find_all("div")[1].p.string.replace(" ", "").replace("\n", "")
        + " "
        + object_.find_all("div")[1]
        .find_all("p")[1]
        .string.replace(" ", "")
        .replace("\n", "")
    )

    # get video url
    account = object_.find("video")["data-account"]
    vid = object_.find("video")["data-video-id"]
    radio_url = get_media_url(account, vid)

    # download video
    parse = urlparse(radio_url)
    if parse.path[parse.path.find(".") + 1 :] == "m3u8":
        download_m3u8(radio_url, "video.mp4")
    else:
        file = requests.get(radio_url)
        open("./video.mp4", "wb").write(file.content)

    # send message
    send_telegram(name + " #radio_and", "text")
    sendVideo = send_telegram("video.mp4", "video_file")
    # if video size is too large, send url instead
    try:
        if json.loads(sendVideo.content)["description"] == "Request Entity Too Large":
            size = str(round(os.stat("./video.mp4").st_size / (1024 * 1024), 2)) + "MB"
            send_telegram(size, "text")
            send_telegram(radio_url, "text")
    except:
        pass

    return name + "\n" + radio_url


@app.route("/")
def twitter():
    # 取得推文
    tweet = request.args.get("tweet")
    # check if debugging
    global debugging
    try:
        debugging = True if request.args.get("debugging") == "true" else False
    except TypeError:
        debugging = False
    # 根據推文重新導向網頁
    if "『1日1愛香』更新いたしました" in tweet:
        return redirect(url_for("_1nichi1aika"))
    elif "RADIO AND 更新" in tweet:
        return redirect(url_for("radio"))
    else:
        send_telegram(tweet, "text", env.get("telegram_bot_token_tweet"))
        return "ok"


@app.route("/line")
def line():
    env = os.environ
    my_data = {"idpwLgid": env.get("email"), "idpwLgpw": env.get("pw"), "mode": "LOGIN"}
    s = requests.session()
    s.post("https://fc.kobayashiaika.jp/s/n85/login", data=my_data)
    r = s.get("https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list")

    soup = BeautifulSoup(r.text, "html.parser")

    date = (
        soup.find("div", class_="textBox")
        .find_all("p")[0]
        .string.replace(" ", "")
        .replace("\n", "")
    )

    content = (
        soup.find("div", class_="textBox")
        .find_all("p")[1]
        .string.replace(" ", "")
        .replace("\n", "")
    )

    image = (
        str(soup.find("li", class_="item").find("div", class_="image").img)
        .replace('<img src="', "https://fc.kobayashiaika.jp")
        .replace('"/>', "")
    )

    return date + "\n" + content + "\n" + image


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get("PORT", 5000))
    if env.get("MODE") != "production":
        app.run(host="0.0.0.0", port=port)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
