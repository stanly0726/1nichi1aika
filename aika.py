import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, redirect, url_for
import json
import datetime
import re
app = Flask(__name__)
env=os.environ

@app.route('/1nichi1aika')
def _1nichi1aika():
	#設定club帳密
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	#發出requests
	s = requests.session()
	s.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r = s.get('https://fc.kobayashiaika.jp/s/n85/lot/top_uranai')
	r2 = s.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list')
	#用bs處理網頁
	soup_uranai = BeautifulSoup(r.text, 'html.parser')
	soup = BeautifulSoup(r2.text, 'html.parser')
	#取得日期
	date = soup.find("div",class_="textBox").find_all('p')[0].string.replace(' ','').replace('\n','')
	#取得文字內容
	content = soup.find("div",class_="textBox").find_all('p')[1].text.replace(' ','')#.replace('\n','')
	#判斷媒體類別
	image_or_movie = soup.find("li",class_="item").find_all('div')[1].get('class')[0]
	#根據媒體類別取得網址
	if image_or_movie == 'image':
		image = str(soup.find("li",class_="item").find('div',class_='image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')
	elif image_or_movie == 'movie':
		account = soup.find("li",class_="item").find('video')['data-account']
		vid = soup.find("li",class_="item").find('video')['data-video-id']
		header = {'Accept': 'application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr'}
		j = json.loads(requests.get('https://edge.api.brightcove.com/playback/v1/accounts/'+account+'/videos/'+vid, headers=header).text)
		image = j['sources'][5]['src']
	#取得占卜點數和gif
	point = soup_uranai.find('p', class_='point').string.replace('\n', '')
	uranai_gif = str(soup_uranai.find('p', class_ = 'image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')
	#取得占卜語音
	account = soup_uranai.find('div', class_ = 'voice').video['data-account']
	vid = soup_uranai.find('div', class_ = 'voice').video['data-video-id']
	header = {'Accept': 'application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr'}
	j = json.loads(requests.get('https://edge.api.brightcove.com/playback/v1/accounts/'+account+'/videos/'+vid, headers=header).text)
	uranai_voice = j['sources'][2]['src']

	#傳送訊息(line,占卜點數)
	#header = {'Authorization': env.get('line_notify_bearer')}
	#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': point})
	#傳送訊息(telegram)占卜點數
	telegram_param_point = {'chat_id': '1024110161', 'text': point}
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param_point)
	#傳送訊息(telegram)占卜語音
	file = requests.get(uranai_voice)
	open('./voice.mp4','wb').write(file.content)
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVoice', params = {'chat_id': '1024110161'}, files = {'voice': open('./voice.mp4', 'rb')})

	
	#gif部分

	# #每月重置
	# if datetime.date.today().day == 1:
	# 	open('gif_record.txt', 'w').write('')
	# #檢查該月以傳送過的占卜gif
	# gif_record = open('gif record.txt', 'r').read()
	# today_point = point[0]
	# if today_point not in gif_record:
	# 	telegram_param_gif = {'chat_id': '1024110161', 'animation': uranai_gif}
	# 	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendAnimation', params = telegram_param_gif)
	# 	open('gif record.txt', 'a').write(today_point)
	# 	print(open('gif record.txt', 'r').read())

	r = requests.get(uranai_gif)
	open('uranai.gif', 'wb').write(r.content)
	telegram_param_gif = {'chat_id': '1024110161'}
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendAnimation', params = telegram_param_gif, files = {'animation': open('uranai.gif', 'rb')})

	#傳送訊息(telegram)文字
	telegram_param_content = {'chat_id': '1024110161', 'text': date+'\n'+content}
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param_content)
	#client.sendRemoteFiles(uranai_gif, message=None, thread_id=100003783918607, thread_type=ThreadType.USER)
	#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': date+'\n'+content})

	#傳送照片或影片
	if image_or_movie == 'image':
		#line(文字 媒體)
		#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+date+'\n'+content,'imageFullsize':image, 'imageThumbnail':image})
		#image = image.replace('https', 'http')
		#telegram(媒體)
		telegram_param_photo = {'chat_id': '1024110161', 'photo': image}
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendPhoto', params = telegram_param_photo)
	elif image_or_movie == 'movie':
		#line(文字 媒體)
		#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': date+'\n'+content})
		#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message':image})
		#telegram(媒體)
		image = re.sub(r'\?pubId=\d*&videoId=\d*','',image)
		telegram_param_video = {'chat_id': '1024110161', 'video': image}
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = telegram_param_video)
	#返回結果(網頁)
	return date+'\n'+content+'\n'+image

@app.route('/radio')
def radio():
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	s = requests.Session()
	s.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r = s.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_radioand/list')

	soup = BeautifulSoup(r.text, 'html.parser')
	object_ = soup.find('ul', class_='radioList').find_all('li')[0]
	account = object_.find('video')['data-account']
	vid = object_.find('video')['data-video-id']
	name = object_.find_all('div')[1].p.string.replace(' ','').replace('\n', '') + ' ' + object_.find_all('div')[1].find_all('p')[1].string.replace(' ','').replace('\n', '')
	header = {'Accept': 'application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr'}
	j = json.loads(requests.get('https://edge.api.brightcove.com/playback/v1/accounts/'+account+'/videos/'+vid, headers=header).text)
	if len(j['sources']) == 8:
		message = j['sources'][1]['src']
		width = j['sources'][1]['width']
		height = j['sources'][1]['height']
	# elif len(j['sources']) == 2:
	# 	message = j['sources'][1]['src']
	header = {'Authorization': env.get('line_notify_bearer')}
	#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+name})
	#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+message})

	telegram_param = {'chat_id': '1024110161', 'text': name}
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param)

	file = requests.get(message)
	open('./video.mp4','wb').write(file.content)
	sendVideo = requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = {'chat_id': '1024110161', 'width': width, 'height': height},files={'video': open('./video.mp4', 'rb')})
	try:
		if json.loads(sendVideo.content)['description'] == 'Request Entity Too Large':
			message = j['sources'][4]['src']
			file = requests.get(message)
			open('./video.mp4','wb').write(file.content)
			sendVideo = requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = {'chat_id': '1024110161', 'width': width, 'height': height},files={'video': open('./video.mp4', 'rb')})
			try:
				if json.loads(sendVideo.content)['description'] == 'Request Entity Too Large':
					size = str(round(os.stat('./video.mp4').st_size/(1024*1024),2))+'MB'
					requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = {'chat_id': '1024110161', 'text': size})
					requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = {'chat_id': '1024110161', 'text': message})
			except KeyError:
				pass
	except KeyError:
		pass
	return name+'\n'+message

@app.route('/')
def twitter():
	#取得推文
	tweet = request.args.get("tweet")
	#根據推文重新導向網頁
	if "『1日1愛香』更新いたしました！" in tweet:
		return redirect(url_for('_1nichi1aika'))
	elif "RADIO AND 更新！" in tweet:
		return redirect(url_for('radio'))
	else:
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token_tweet') + '/sendMessage', params = {'chat_id': '1024110161', 'text': tweet})
		return 'ok'

@app.route('/line')
def line():
	env=os.environ
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	s = requests.session()
	s.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r = s.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list')

	soup = BeautifulSoup(r.text, 'html.parser')

	date = soup.find("div",class_="textBox").find_all('p')[0].string.replace(' ','').replace('\n','')

	content = soup.find("div",class_="textBox").find_all('p')[1].string.replace(' ','').replace('\n','')

	image = str(soup.find("li",class_="item").find('div',class_='image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')

	return date+'\n'+content+'\n'+image


if __name__ == '__main__':
#Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)