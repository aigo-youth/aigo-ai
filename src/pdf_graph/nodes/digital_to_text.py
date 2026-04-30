from src.pdf_graph.state import PDF_State
import fitz

def digital_to_text(state: PDF_State) -> dict:
    
    doc = fitz.open(state['file_path'])
    texts = ''

    for page in doc:
        texts += page.get_text()

    doc.close()     # 메모리 관리 및 에러 방지 위해

    return {'extracted_text' : texts}