import os
import re
from collections import defaultdict

def extract_info_from_path(html_path):
    """HTML 파일 경로에서 지역과 시설명 추출"""
    try:
        # 경로를 정규화하고 분리
        path_parts = html_path.replace('\\', '/').split('/')
        
        region_part = None
        facility_part = None
        
        # 1. 지역 정보 추출
        for part in path_parts:
            # ★숫자(지역명) 패턴으로 지역 추출
            if '★' in part and '(' in part and ')' in part:
                match = re.search(r'★\d*\(([^)]+)\)', part)
                if match:
                    region_part = match.group(1)
                    break
        
        # 2. 시설명 추출 - 여러 방법 시도
        filename = os.path.basename(html_path)
        
        # 방법 1: 파일명에서 직접 추출
        if filename.endswith('.html'):
            base_filename = filename[:-5]  # .html 제거
            
            # 각종 패턴에서 시설명 추출
            patterns = [
                r'도상훈련\(([^)]+)\)',                    # 도상훈련(시설명)
                r'도상훈련자료\(([^)]+)\)',                # 도상훈련자료(시설명) 
                r'특정소방대상물 도상훈련.*?\(([^)]+)\)',   # 특정소방대상물 도상훈련(시설명)
                r'360도 도상훈련.*?\(([^)]+)\)',          # 360도 도상훈련(시설명)
                r'최종-도상훈련\(([^)]+)\)',              # 최종-도상훈련(시설명)
                r'최종-([^)]+)',                         # 최종-시설명
                r'\d+\.\s*(.+)',                         # 숫자. 시설명
            ]
            
            for pattern in patterns:
                match = re.search(pattern, base_filename)
                if match:
                    facility_part = match.group(1).strip()
                    break
            
            # 패턴 매칭 실패 시 파일명 그대로 사용 (특정 제거 문자열)
            if not facility_part:
                facility_part = base_filename
                # 불필요한 문자 제거
                remove_patterns = [
                    r'특정소방대상물\s*도상훈련\s*PPT\s*서식?\s*',
                    r'도상훈련자료\s*',
                    r'도상훈련\s*기본자료\s*',
                    r'360도\s*도상훈련\s*자료\s*',
                    r'도상훈련\s*',
                    r'최종-',
                    r'\s*origin\s*',
                    r'\([^)]*수정[^)]*\)',
                ]
                
                for remove_pattern in remove_patterns:
                    facility_part = re.sub(remove_pattern, '', facility_part).strip()
        
        # 방법 2: 폴더명에서 시설명 추출 (백업)
        if not facility_part or len(facility_part) < 2:
            for part in reversed(path_parts):  # 역순으로 탐색
                if '★' in part and '(' in part and ')' in part:
                    # ★(지역)시설명 패턴
                    match = re.search(r'★\([^)]*\)(.+)', part)
                    if match:
                        facility_part = match.group(1).strip()
                        break
                elif part not in ['360도 모바일 변환'] and not '피난약자' in part and not '__MACOSX' in part:
                    # 시설명으로 보이는 폴더명
                    if len(part) > 2:
                        facility_part = part
                        break
        
        # 최종 정리
        if facility_part:
            # 추가 정리
            facility_part = facility_part.replace('_', '').strip()
            # 괄호 안의 내용 정리 (예: "시설명 (봄철)" -> "시설명")
            facility_part = re.sub(r'\s*\([^)]*\)\s*$', '', facility_part)
        
        return region_part, facility_part
        
    except Exception as e:
        print(f"경로 분석 오류 ({html_path}): {e}")
        return None, None

def scan_html_files():
    """HTML 파일들을 스캔하여 정보 수집"""
    base_dir = "360도 모바일 변환"
    
    if not os.path.exists(base_dir):
        print(f"'{base_dir}' 폴더를 찾을 수 없습니다.")
        return {}
    
    facilities_by_region = defaultdict(list)
    
    # HTML 파일 찾기 (.bak 파일 제외)
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html') and not file.endswith('.bak'):
                html_path = os.path.join(root, file)
                region, facility = extract_info_from_path(html_path)
                
                if region and facility:
                    # 상대 경로로 변환
                    relative_path = os.path.relpath(html_path).replace('\\', '/')
                    facilities_by_region[region].append({
                        'name': facility,
                        'path': relative_path
                    })
                    print(f"발견: {region} - {facility}")
                else:
                    print(f"정보 추출 실패: {html_path}")
    
    return dict(facilities_by_region)

def generate_index_html(facilities_data):
    """인덱스 HTML 생성"""
    
    if not facilities_data:
        print("분석할 데이터가 없습니다.")
        return
    
    # 지역별 정렬
    sorted_regions = sorted(facilities_data.keys())
    
    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>전남 소방본부 피난약자시설 도상훈련 자료</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        body {{
            font-family: 'Noto Sans KR', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .region-section {{
            margin-bottom: 40px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .region-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .region-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
        }}
        .facility-count {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-left: 10px;
        }}
        .facilities-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            padding: 20px;
        }}
        .facility-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .facility-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-color: #3498db;
        }}
        .facility-name {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 1.1em;
        }}
        .facility-type {{
            font-size: 0.9em;
            color: #7f8c8d;
            background: #ecf0f1;
            padding: 3px 8px;
            border-radius: 12px;
            display: inline-block;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            text-align: center;
        }}
        .stats h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .stats-numbers {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: 700;
            color: #3498db;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        @media (max-width: 768px) {{
            .facilities-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 2em;
            }}
            .stats-numbers {{
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚒 전남 소방본부</h1>
            <p>피난약자시설 도상훈련 자료</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <h3>📊 통계 현황</h3>
                <div class="stats-numbers">
                    <div class="stat-item">
                        <span class="stat-number">{len(sorted_regions)}</span>
                        <div class="stat-label">개 지역</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{sum(len(facilities) for facilities in facilities_data.values())}</span>
                        <div class="stat-label">개 시설</div>
                    </div>
                </div>
            </div>
'''
    
    # 각 지역별 섹션 생성
    for region in sorted_regions:
        facilities = facilities_data[region]
        html_content += f'''
            <div class="region-section">
                <div class="region-header">
                    <h2 class="region-title">
                        📍 {region}
                        <span class="facility-count">({len(facilities)}개 시설)</span>
                    </h2>
                </div>
                <div class="facilities-grid">
'''
        
        # 시설별 카드 생성
        for facility in sorted(facilities, key=lambda x: x['name']):
            # 시설 유형 판단
            facility_type = "기타시설"
            name_lower = facility['name'].lower()
            if any(keyword in name_lower for keyword in ['요양원', '노인전문요양원']):
                facility_type = "요양원"
            elif any(keyword in name_lower for keyword in ['요양병원']):
                facility_type = "요양병원"
            elif any(keyword in name_lower for keyword in ['복지센터', '복지원']):
                facility_type = "복지시설"
            elif any(keyword in name_lower for keyword in ['산후조리원']):
                facility_type = "산후조리원"
            elif any(keyword in name_lower for keyword in ['양로원']):
                facility_type = "양로원"
            
            html_content += f'''
                    <div class="facility-card" onclick="window.open('{facility['path']}', '_blank')">
                        <div class="facility-name">{facility['name']}</div>
                        <div class="facility-type">{facility_type}</div>
                    </div>
'''
        
        html_content += '''
                </div>
            </div>
'''
    
    html_content += '''
        </div>
    </div>
    
    <script>
        // 페이지 로드 시 통계 애니메이션
        document.addEventListener('DOMContentLoaded', function() {
            const numbers = document.querySelectorAll('.stat-number');
            numbers.forEach(number => {
                const target = parseInt(number.textContent);
                let current = 0;
                const increment = target / 20;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    number.textContent = Math.floor(current);
                }, 50);
            });
        });
    </script>
</body>
</html>'''
    
    # 파일 저장
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ index.html 파일이 생성되었습니다!")
    print(f"📊 총 {len(sorted_regions)}개 지역, {sum(len(facilities) for facilities in facilities_data.values())}개 시설")
    
    # 지역별 상세 정보 출력
    print("\n📋 지역별 상세 정보:")
    for region in sorted_regions:
        print(f"  🏢 {region}: {len(facilities_data[region])}개 시설")

def main():
    print("🔍 전남 소방본부 피난약자시설 도상훈련 자료 스캔 중...")
    print("=" * 60)
    
    facilities_data = scan_html_files()
    
    if facilities_data:
        print(f"\n✅ 스캔 완료! {len(facilities_data)}개 지역의 데이터를 발견했습니다.")
        generate_index_html(facilities_data)
    else:
        print("\n❌ HTML 파일을 찾을 수 없습니다.")
        print("'360도 모바일 변환' 폴더가 존재하는지 확인해주세요.")

if __name__ == "__main__":
    main()
