from src.pdf_graph.state import PDF_State
import fitz
from pathlib import Path

def check_pdf(state: PDF_State) -> dict:

    path = state['file_path']
    doc = fitz.open(path)
    scanned = False

    # file_info 정보들 한 번에 취득
    page_count = len(doc)                                   # file_info의 page에 들어갈 값

    file = Path(path)
    title = file.name
    volume = round(file.stat().st_size / (1024 * 1024), 2)  # 소수점 2자리까지, MB 기준


    for page in doc:
        images = page.get_images(full=True)

        if len(images) > 0:     # 이미지로 인식되면
            scanned = True
            break

    doc.close()     # (진 曰: close()문 한 줄 추가합니당)

    return {
        'file_info': {'title': title, 'volume': volume, 'page_count': page_count},
        'file_type': 'Scan' if scanned else 'Digital'
    }
    


def route_after_check_pdf(state: PDF_State) -> str:

    if state['file_type'] == 'Scan':    # Scan인 경우
        return 'scan_to_text'
    else:                               # Digital인 경우
        return 'digital_to_text'
        