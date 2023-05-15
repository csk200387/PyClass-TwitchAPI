import json
import requests
# import subprocess


"""
트위치 생방송 녹화 프로그램용 모듈 제작

TODO:
    - 토큰값 입력 후 토큰값 저장
    - BEARER 토큰 기한 체크 & 자동 갱신
    - 방송 제목 불러오기
    - 디스코드 웹훅 보내기
    - rclone으로 구글드라이브에 업로드

"""


class PTRecorder:
    def __init__(self, oauth_token:str, bearer_token:str, client_id:str):
        self.oauth_token = oauth_token
        self.bearer_token = bearer_token
        self.client_id = client_id
        self.headers = {'Authorization': 'Bearer '+self.bearer_token, 'Client-ID': self.client_id}

    def getNickname(self, login_id:str) -> str:
        headers = self.headers
        req = requests.get('https://api.twitch.tv/helix/users?login='+login_id, headers=headers).json()
        id = req['data'][0]['id']
        nick = req['data'][0]['display_name'].strip('_')
        req = requests.get('https://api.twitch.tv/helix/channels?broadcaster_id='+id, headers=headers).json()
        title = req['data'][0]['title']
        return nick, title