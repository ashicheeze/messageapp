from flask import Flask, render_template, request, jsonify
import json
import os
from schedule_from_email import fetch_seen_emails, extract_structured_events, create_calendar_events
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/fetch_emails', methods=['POST'])
def fetch_emails():
    """メールを取得してイベントを抽出"""
    try:
        emails = fetch_seen_emails()
        events = extract_structured_events(emails)
        
        # イベントにIDを追加
        for i, event in enumerate(events):
            event['id'] = i
            
        return jsonify({
            'success': True,
            'events': events,
            'total_emails': len(emails)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/create_events', methods=['POST'])
def create_events():
    """選択されたイベントをGoogle Calendarに作成"""
    try:
        data = request.get_json()
        selected_event_ids = data.get('selected_events', [])
        
        # すべてのイベントを再取得
        emails = fetch_seen_emails()
        all_events = extract_structured_events(emails)
        
        # 選択されたイベントのみを抽出
        selected_events = []
        for event_id in selected_event_ids:
            if 0 <= event_id < len(all_events):
                selected_events.append(all_events[event_id])
        
        if not selected_events:
            return jsonify({
                'success': False,
                'error': 'No events selected'
            })
        
        # カレンダーイベントを作成（dry_run=False）
        created_events = create_calendar_events(selected_events, dry_run=False)
        
        return jsonify({
            'success': True,
            'created_count': len(created_events),
            'events': [{'title': event['title']} for event in selected_events]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
