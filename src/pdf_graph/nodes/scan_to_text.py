from src.pdf_graph.state import PDF_State
import fitz
import numpy as np

from paddleocr import PaddleOCR

# 콜드스타트 문제로 이걸 빼놓았는데, 아래 노드에 합쳐야하는지가 고민...

ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",            # Default로 되어있는 PP-OCRv5_server_det로 했을 때에 인식 못한 부분을 mobile 버전이 더 잘 캐치했었음...(contract_02.pdf 4쪽을 server는 전혀 캐치 못했고 mobile은 캐치했음)
    text_recognition_model_name="korean_PP-OCRv5_mobile_rec",   # recognition model을 지정하지 않을 시에는 디폴트로 해당 모델을 설정하길래, 혹시나 하여 동일 모델 지정하여 설정하였음.
    use_doc_orientation_classify=False,                         # 문서 전체가 몇 도 회전됐는지 감지하고 보정
    use_doc_unwarping=False,                                    # 구겨지거나 휘어진 문서를 펴는 보정
    use_textline_orientation=False,                             # 텍스트 줄이 가로/세로인지 판단해주는 보정
    device='gpu'
)

def scan_to_text(state: PDF_State) -> dict:

    doc = fitz.open(state['file_path'])
    images = []

    for page in doc:
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
        images.append(img)

    doc.close()

    text_list = []
    all_scores = []

    for image in images:
        data = ocr.predict(image)[0].json
        text_list.extend(data['res']['rec_texts'])
        all_scores.extend(data['res']['rec_scores'])              # 잘못 인식된 경우가 왕왕 있음에도 점수가 높은 경우가 많아, 유효한 척도일지 고민이 됨.

    texts = " ".join(text_list)
    acc_score = round(np.mean(all_scores), 2)

    return {
        'extracted_text': texts,
        'ocr_accuracy_score': acc_score
    }