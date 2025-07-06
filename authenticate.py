import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]

def authenticate_gmail():
    """Gmail APIの認証を行い、token.jsonを生成します"""
    creds = None
    
    # token.jsonが存在する場合は読み込み
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 有効なクレデンシャルがない場合
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.jsonが必要
            if not os.path.exists('credentials.json'):
                print("credentials.jsonファイルが見つかりません。")
                print("Google Cloud Consoleからcredentials.jsonをダウンロードして、このディレクトリに配置してください。")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # token.jsonに保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("認証が完了しました！token.jsonが作成されました。")
        return True
    
    print("既存の認証トークンが有効です。")
    return True

if __name__ == '__main__':
    authenticate_gmail()
