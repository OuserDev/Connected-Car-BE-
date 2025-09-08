from flask import Blueprint, jsonify, send_file, request, current_app
import os
from datetime import datetime

video_bp = Blueprint('video', __name__, url_prefix='/api')

@video_bp.route('/videos', methods=['GET'])
def get_videos():
    """사용자의 주행 영상 목록 조회"""
    try:
        # 영상 파일들의 정보 (실제 구현에서는 데이터베이스에서 조회)
        videos = [
            {
                "id": 1,
                "filename": "20250905_주행.mp4",
                "display_name": "2025.09.05 주행영상 #1",
                "recorded_at": "2025-09-05T14:23:15",
                "duration_seconds": 754,  # 12분 34초
                "duration_display": "12분 34초",
                "file_size": 47185920,  # bytes
                "file_size_display": "45.2 MB"
            },
            {
                "id": 2,
                "filename": "20250905_주행_2.mp4",
                "display_name": "2025.09.05 주행영상 #2",
                "recorded_at": "2025-09-05T16:45:32",
                "duration_seconds": 497,  # 8분 17초
                "duration_display": "8분 17초",
                "file_size": 30318592,  # bytes
                "file_size_display": "28.9 MB"
            },
            {
                "id": 3,
                "filename": "20250905_주행_3.mp4",
                "display_name": "2025.09.05 주행영상 #3",
                "recorded_at": "2025-09-05T18:12:09",
                "duration_seconds": 921,  # 15분 21초
                "duration_display": "15분 21초",
                "file_size": 55262208,  # bytes
                "file_size_display": "52.7 MB"
            },
            {
                "id": 4,
                "filename": "20250905_주행_4.mp4",
                "display_name": "2025.09.05 주행영상 #4",
                "recorded_at": "2025-09-05T20:08:44",
                "duration_seconds": 412,  # 6분 52초
                "duration_display": "6분 52초",
                "file_size": 25296896,  # bytes
                "file_size_display": "24.1 MB"
            }
        ]

        return jsonify({
            "success": True,
            "data": videos,
            "total_count": len(videos),
            "message": "주행 영상 목록을 성공적으로 조회했습니다"
        })

    except Exception as e:
        current_app.logger.error(f"영상 목록 조회 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "주행 영상 목록을 조회하는 중 오류가 발생했습니다"
        }), 500

@video_bp.route('/videos/<string:filename>/download', methods=['GET'])
def download_video(filename):
    """주행 영상 다운로드"""
    try:
        # 파일 경로 구성
        video_path = os.path.join('static', 'assets', 'videos', filename)
        
        # 파일 전송
        return send_file(
            video_path,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )

    except Exception as e:
        current_app.logger.error(f"영상 다운로드 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "영상 다운로드 중 오류가 발생했습니다"
        }), 500

@video_bp.route('/videos/<string:filename>/stream', methods=['GET'])
def stream_video(filename):
    """주행 영상 스트리밍 (미리보기용)"""
    try:
        # 파일 경로 구성
        video_path = os.path.join('static', 'assets', 'videos', filename)
        
        # 파일 스트리밍 (브라우저에서 재생용)
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"영상 스트리밍 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "영상 스트리밍 중 오류가 발생했습니다"
        }), 500