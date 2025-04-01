from pymongo import MongoClient
from datetime import datetime

# MongoDB 연결 설정
def connect_to_db():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["sensitive_info_db"]
        collection = db["analysis"]
        print("MongoDB 연결 성공")
        return collection
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        return None

# 데이터 저장
def save_detection_result(collection, filename, file_path, raw_result):
    def convert_to_string(data):
        """ 리스트, 튜플 및 중첩 구조를 문자열로 변환하는 재귀 함수 """
        if isinstance(data, list):
            return [convert_to_string(item) for item in data]
        elif isinstance(data, tuple):
            return str(data)
        elif isinstance(data, dict):
            return {key: convert_to_string(value) for key, value in data.items()}
        else:
            return str(data)

    # 데이터를 변환하여 문자열로 처리
    processed_result = {key: convert_to_string(value) for key, value in raw_result.items()}
    print("Processed Result for Debugging:", processed_result)

    # MongoDB에 저장할 데이터 구조
    detection_record = {
        "filename": filename,
        "file_path": file_path,
        "detection_result": processed_result,
        "timestamp": datetime.utcnow()
    }

    try:
        collection.insert_one(detection_record)
        print("데이터 저장 성공")
    except Exception as e:
        print(f"데이터 저장 실패: {e}")