import os
from PIL import Image
import imagehash

def find_similar_stocks(target_code, kline_img_dir, top_n=10):
    """
    计算目标股票K线图与所有股票K线图的相似度，返回最相似的top_n只股票。
    返回: [(code, similarity, img_path), ...]
    """
    target_img = os.path.join(kline_img_dir, f'{target_code}.png')
    if not os.path.exists(target_img):
        print(f'目标K线图不存在: {target_img}')
        return []
    try:
        target_hash = imagehash.phash(Image.open(target_img))
    except Exception as e:
        print(f'无法读取目标图片: {e}')
        return []
    results = []
    for fname in os.listdir(kline_img_dir):
        if not fname.lower().endswith('.png') or fname == f'{target_code}.png':
            continue
        code = fname.replace('.png', '')
        img_path = os.path.join(kline_img_dir, fname)
        try:
            img_hash = imagehash.phash(Image.open(img_path))
            distance = target_hash - img_hash
            similarity = max(0, 100 - distance * 2)
            results.append((code, similarity, img_path))
        except Exception as e:
            continue
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n] 