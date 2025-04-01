import olefile, re
import zlib
import struct

#한글 파일 텍스트 추출 함수 정의
def get_hwp_text(file_path):
    f = olefile.OleFileIO(file_path)
    dirs = f.listdir()

    # HWP 파일 검증
    if ["FileHeader"] not in dirs or ["\x05HwpSummaryInformation"] not in dirs:
        raise Exception("Not Valid HWP.")

    # 문서 포맷 압축 여부 확인
    header = f.openstream("FileHeader")
    header_data = header.read()
    is_compressed = (header_data[36] & 1) == 1

    # BodyText 섹션 경로 수집
    nums = []
    for d in dirs:
        if d[0] == "BodyText":
            nums.append(int(d[1][len("Section"):]))

    sections = ["BodyText/Section" + str(x) for x in sorted(nums)]

    # 전체 텍스트 추출
    text = ""

    for section in sections:
        bodytext = f.openstream(section)
        data = bodytext.read()
        if is_compressed:
            try:
                unpacked_data = zlib.decompress(data, -15)
            except Exception as e:
                print(f"[압축 해제 오류] {e}")
                continue
        else:
            unpacked_data = data

        section_text = ""
        i = 0
        size = len(unpacked_data)

        while i < size:
            try:
                header = struct.unpack_from("<I", unpacked_data, i)[0]
                rec_type = header & 0x3ff
                rec_len = (header >> 20) & 0xfff
            except:
                break  # 데이터 끝에 도달하거나 깨졌을 경우

            if rec_type == 67:  # 문단 텍스트
                rec_data = unpacked_data[i+4:i+4+rec_len]
                try:
                    section_text += rec_data.decode('utf-16')
                except:
                    pass
                section_text += "\n"

            i += 4 + rec_len

        text += section_text
        text += "\n"

    return text


#파일 내 민감정보 탐지 함수 정의
def check_sensitive_info(file_path):
    text = get_hwp_text(file_path)
    patterns = {
        'email': r'[\w\.-]+@[\w\.-]+',
        'person': r'\d{6}[-]\d{7}\b',
        'num': r'\b(01[016789]-?\d{4}-?\d{4}|0\d{1,2}-?\d{3}-?\d{4})\b',
        'addr': r'([가-힣]{2,6}(?:시|도)\s?[가-힣]{1,4}(?:군|구|시)\s?[가-힣0-9\-]+(?:읍|리|로|길)\s?\d{1,4})',
        'card': r'\b(?:\d{4}-){3}\d{4}\b',
    }

    sensitive_keywords = [
        "주민등록번호", "종교", "정치 성향", "흡연", 
        "주량", "결혼유무", "신장", "체중", "시력"
        ]
    
    # 민감정보 키워드 추출
    keyword_patterns = [re.escape(word) for word in sensitive_keywords]
    keyword_regex = r'\b(' + '|'.join(keyword_patterns) + r')\b'
 
    # 민감정보 추출
    result = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        result[key] = matches       # result 딕셔너리 구조: {'email': ['test@example.com'], 'person': ['900101-1234567'], ...}
   
    keyword_hits = re.findall(keyword_regex, text, re.IGNORECASE)

    summary = []  #summury는 각 카테고리의 개수정보 포함한 리스트 (ex)['email: 2개', 'person: 1개', 'card: 1개']
    total_count = 0  # 민감정보 총 개수

    # 민감정보 결과 요약
    for category, items in result.items():
        if items:
            count = len(items)
            summary.append(f"{category}: {count}개")
            total_count += count

    # 민감정보가 식별되었으면 출력
    if total_count > 0 or keyword_hits:
        print(f"⚠️ 문서에서 {total_count}개의 개인정보가 발견되었습니다.")
        for i in summary:                   # summary 출력결과 :' email: 2개  person: 1개  card: 1개'
            print(i, ' ', end='')
        print('\n')

        # 상세 내용 출력
        for key, value in result.items():   #민감정보 상세 내용 출력
            if value:
                print(f"{key}: {','.join(map(str, value))}")
        print('\n')

        # 민감정보 키워드 출력
        if keyword_hits:                # 수집되고 있는 민감정보 출력
            print(f"⚠️ 문서에서 {len(keyword_hits)}개의 민감정보 키워드가 발견되었습니다:")
            print(", ".join(map(str, keyword_hits)))
            print('\n')
        
        # 민감정보 발견 시 결과 반환
        return result, keyword_hits
    else:
        # 민감정보가 없으면 False와 빈 리스트 반환
        print("문서 내 민감정보가 발견되지 않았습니다.")
        return False, []

    

