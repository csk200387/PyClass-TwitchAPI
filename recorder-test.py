import datetime, time, os, subprocess, json, requests, sys, pytz, time
tz_korea = pytz.timezone('Asia/Seoul')


# Load config
with open("config.json", "r") as f :
    config = json.loads(f.read())

TWITCH_OAUTH_TOKEN = config['TWITCH_OAUTH_TOKEN'] # 시작/중간 광고 제거용 트위치 OAuth토큰
TWITCH_BEARER_TOKEN = config['TWITCH_BEARER_TOKEN']
TWITCH_CLIENT_ID = config['TWITCH_CLIENT_ID']
GDRIVE_FILE_ID = config['GDRIVE_FILE_ID'] # 구글 드라이브 폴더 ID
DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL'] # 손실정보, 드라이브 업로드 알림을 받을 디스코드 Webhook 주소
PERIOD = config['PERIOD']  # 반복 대기 시간 (초)
PATH = r'./'  # 저장 경로


def main() :
    try :
        username = sys.argv[1]  # 스트리머 ID
    except IndexError :
        print('Usage: python3 recorder.py <username>')
        sys.exit(1)
    processed_path = os.path.join(PATH, username)
    now = datetime.datetime.now(tz_korea).strftime('%Y-%m-%d_%Hh%Mm%Ss')
    # filename = ''.join(x for x in f'{username} - {now}.ts' if x.isalnum() or x in ' -_.')
    filename = username+'.ts'
    recorded_filename = os.path.join(processed_path, filename)
    if not os.path.isdir(processed_path) :
        os.makedirs(processed_path)
    subprocess.call(['streamlink', '--twitch-api-header=Authorization=OAuth '+TWITCH_OAUTH_TOKEN,
                    '--stream-segment-threads', '5', '--stream-segment-attempts', '5',
                    '--stream-segment-timeout', '20.0', '--hls-live-restart', '--twitch-disable-hosting',
                    '--twitch-disable-ads', 'twitch.tv/' + username, 'best', '-o', recorded_filename])
    if os.path.isfile(f'{processed_path}/{filename}') :
        subprocess.call(['python3', 'twitchChecker.pyc', f'{processed_path}/{filename}'])
        checkedfile = filename.replace('.ts', '.txt')
        with open(f'{processed_path}/{checkedfile}', 'r') as f :
            arr = f.readlines()
        content = ''.join(map(str, arr[:8]+arr[9:]))
        sendHook(username, content)
        Nick, streamTitle = getUserID(username)
        date = now.split()[0].replace('-', ' ')
        template = ''.join(x for x in f'비디오 {Nick} {date} {streamTitle}' if x.isalnum() or x in ' -_.')
        new_filename = template.strip()+'.ts'
        new_recorded_filename = os.path.join(processed_path, new_filename)
        os.rename(recorded_filename, new_recorded_filename)
        start_runtime = time.time()
        subprocess.call(['mv', f'{processed_path}/{new_recorded_filename}', './googledrive'])
        # subprocess.call(['gdrive', 'files', 'upload', '--parent', GDRIVE_FILE_ID, new_recorded_filename])
        # subprocess.call(['gdrive', 'files', 'upload', new_recorded_filename])
        runtime = time.time()-start_runtime
        driveAlert(username, new_filename, runtime)
        os.remove(f'{processed_path}/{new_filename}')
        os.remove(f'{processed_path}/{checkedfile}')
        subprocess.call(["screen", "-X", "-S", username, "quit"])
        exit(0)


def sendHook(sender:str, content:str) :
    headers = {'Content-Type' : 'application/json'}
    data = {'content' : f'```{content}```', 'username': sender}
    data = json.dumps(data)
    requests.post(DISCORD_WEBHOOK_URL, headers=headers, data=data)


def driveAlert(user:str, filename:str, runtime:str) :
    time = round(runtime, 2)
    headers = {'Content-Type' : 'application/json'}
    data = {
        'username': user,
        'embeds': [
            {
                'title': 'Upload Success',
                'description': filename,
                'color': 1561838,
                'author': {
                    'name': 'GoogleDrive',
                    'url': 'https://drive.google.com/drive/u/0/my-drive',
                    'icon_url': 'https://play-lh.googleusercontent.com/t-juVwXA8lDAk8uQ2L6d6K83jpgQoqmK1icB_l9yvhIAQ2QT_1XbRwg5IpY08906qEw=w480-h960-rw'
                },
                'footer': {
                    'text': f'Runtime : {time} sec'
                }
            }
        ]
    }
    data = json.dumps(data)
    requests.post(DISCORD_WEBHOOK_URL, headers=headers, data=data)


def getUserID(loginID:str) :
    headers = {'Authorization': 'Bearer '+TWITCH_BEARER_TOKEN, 'Client-ID': TWITCH_CLIENT_ID}
    req = requests.get('https://api.twitch.tv/helix/users?login='+loginID, headers=headers).json()
    id = req['data'][0]['id']
    nick = req['data'][0]['display_name'].strip('_')
    req = requests.get('https://api.twitch.tv/helix/channels?broadcaster_id='+id, headers=headers).json()
    title = req['data'][0]['title']
    return nick, title


if __name__ == '__main__':
    main()