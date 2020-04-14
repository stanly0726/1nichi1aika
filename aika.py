import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import json

def hello_world():
	env=os.environ
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	r = requests.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r2 = requests.get('https://fc.kobayashiaika.jp/s/n85/lot/top_uranai', cookies=r.cookies)
	r3 = requests.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list', cookies=r.cookies)

	soup_uranai = BeautifulSoup(r2.text, 'html.parser')
	soup = BeautifulSoup(r3.text, 'html.parser')

	date = soup.find("div",class_="textBox").find_all('p')[0].string.replace(' ','').replace('\n','')

	content = soup.find("div",class_="textBox").find_all('p')[1].text.replace(' ','')#.replace('\n','')

	image_or_movie = soup.find("li",class_="item").find_all('div')[1].get('class')[0]

	if image_or_movie == 'image':
		image = str(soup.find("li",class_="item").find('div',class_='image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')
	elif image_or_movie == 'movie':
		account = soup.find("li",class_="item").find('video')['data-account']
		vid = soup.find("li",class_="item").find('video')['data-video-id']
		header = {'Accept': 'application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr'}
		j = json.loads(requests.get('https://edge.api.brightcove.com/playback/v1/accounts/'+account+'/videos/'+vid, headers=header).text)
		image = j['sources'][5]['src']
	point = soup_uranai.find('p', class_='point').string.replace('！\n', '')

	uranai_gif = str(soup_uranai.find('p', class_='image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')

	header = {'Authorization': env.get('line_notify_bearer')}
	telegram_param_point = {'chat_id': '1024110161', 'text': point}
	telegram_param_content = {'chat_id': '1024110161', 'text': date+'\n'+content}

	requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': point})
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param_point)
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param_content)
	#client.sendRemoteFiles(uranai_gif, message=None, thread_id=100003783918607, thread_type=ThreadType.USER)
	#requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': date+'\n'+content})


	if image_or_movie == 'image':
		requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+date+'\n'+content,'imageFullsize':image, 'imageThumbnail':image})

		image = image.replace('https', 'http')
		telegram_param_photo = {'chat_id': '1024110161', 'photo': image}
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendPhoto', params = telegram_param_photo)
		#client.sendRemoteFiles(image, message=None, thread_id=100003783918607, thread_type=ThreadType.USER)
	elif image_or_movie == 'movie':
		requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': date+'\n'+content})
		requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message':image})

		image = image.replace('https', 'http')
		telegram_param_video = {'chat_id': '1024110161', 'video': image}
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = telegram_param_video)
		#client.send(Message(text=image), thread_id=100003783918607, thread_type=ThreadType.USER)

	return date+'\n'+content+'\n'+image

def radio():
	env=os.environ
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	r = requests.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r2 = requests.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_radioand/list', cookies=r.cookies)

	soup = BeautifulSoup(r2.text, 'html.parser')
	object_ = soup.find('ul', class_='radioList').find_all('li')[0]
	account = object_.find('video')['data-account']
	vid = object_.find('video')['data-video-id']
	name = object_.find_all('div')[1].p.string.replace(' ','').replace('\n', '') + ' ' + object_.find_all('div')[1].find_all('p')[1].string.replace(' ','').replace('\n', '')
	header = {'Accept': 'application/json;pk=BCpkADawqM3T47dRzTl5mbQrsSen6Irw0V0_IJkbfWomd5pq9d-QFF9qEEqIx8riJ1F93W8T74JPmcI3J_Mb1vRFbx3kjvIVhoJnjaSu9J3z7FhaSSgoChrjoZu63Wf_q3j4XfYoi5dJOZKr'}
	j = json.loads(requests.get('https://edge.api.brightcove.com/playback/v1/accounts/'+account+'/videos/'+vid, headers=header).text)
	if len(j['sources']) == 8:
		message = j['sources'][2]['src']
	elif len(j['sources']) == 2:
		message = j['sources'][1]['src']
	header = {'Authorization': env.get('line_notify_bearer')}
	requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+name})
	requests.post('https://notify-api.line.me/api/notify', headers = header, data = {'message': '\n'+message})

	message = message.replace('https', 'http')
	telegram_param = {'chat_id': '1024110161', 'text': name}
	telegram_param_video = {'chat_id': '1024110161', 'video': message}
	requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendMessage', params = telegram_param)
	sendVideo = requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = telegram_param_video)
	print(sendVideo)
	print(sendVideo.content)
	print(json.loads(sendVideo.content))
	if json.loads(sendVideo.content)['ok'] == 'False':
		print('false')
		file = requests.get(message)
		open('./video.mp4','wb').write(file.content)
		requests.post('https://api.telegram.org/' + env.get('telegram_bot_token') + '/sendVideo', params = {'chat_id': '1024110161'},files={'video': open('./video.mp4', 'rb')})
	return name+'\n'+message

app = Flask(__name__)

@app.route('/')
def twitter():
	tweet = request.args.get("tweet")
	if "『1日1愛香』更新いたしました！" in tweet:
		return hello_world()
	elif "RADIO AND 更新！" in tweet:
		return radio()

@app.route('/line')
def line():
	env=os.environ
	my_data = {'idpwLgid': env.get('email'),  'idpwLgpw': env.get('pw'), 'mode': 'LOGIN'}
	r = requests.post("https://fc.kobayashiaika.jp/s/n85/login",data=my_data)
	r2 = requests.get('https://fc.kobayashiaika.jp/s/n85/diary/fc_1nichi1aika/list', cookies=r.cookies)

	soup = BeautifulSoup(r2.text, 'html.parser')

	date = soup.find("div",class_="textBox").find_all('p')[0].string.replace(' ','').replace('\n','')

	content = soup.find("div",class_="textBox").find_all('p')[1].string.replace(' ','').replace('\n','')

	image = str(soup.find("li",class_="item").find('div',class_='image').img).replace('<img src="','https://fc.kobayashiaika.jp').replace('"/>','')

	return date+'\n'+content+'\n'+image

#@app.route('/radio')


if __name__ == '__main__':
#Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
