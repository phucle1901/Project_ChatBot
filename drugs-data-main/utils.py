import json
import requests
from parsel import Selector
from typing import List
from pprint import pprint

def traverse(node, results=[]):
    # node.getchildren() không tồn tại trong parsel,
    # ta lấy child nodes qua xpath('*')
    children = node.xpath("./*")

    if not children:  # nếu không có con => leaf node
        text = node.xpath("normalize-space(text())").get()
        if text:
            results.append(text)
    else:
        for child in children:
            traverse(child, results)
        # Lấy tail text (text nằm sau thẻ con)
        tail_texts = node.xpath("normalize-space(text())").getall()
        for t in tail_texts:
            if t.strip():
                results.append(t.strip())
    return '\n'.join(results)

def extract_drug_info(url: str) -> List[str]:
    result = {}
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_text = response.text
        tree = Selector(text=html_text)
        describe = tree.xpath("//*[@id='__next']/div[1]/div[2]/div[3]/div/div/div[1]/div[2]/div")
        ingredient = tree.xpath("//*[@id='detail-content-0']")
        usage = tree.xpath("//*[@id='detail-content-1']")
        dosage = tree.xpath("//*[@id='detail-content-2']")
        adverse_effect = tree.xpath("//*[@id='detail-content-3']")
        careful = tree.xpath("//*[@id='detail-content-4']")
        preservation = tree.xpath("//*[@id='detail-content-5']")

        result['describe'] = traverse(node=describe)
        result['ingredient'] = traverse(node=ingredient)
        result['usage'] = traverse(node=usage)
        result['dosage'] = traverse(node=dosage)
        result['adverse_effect'] = traverse(node=adverse_effect)
        result['careful'] = traverse(node=careful)
        result['preservation'] = traverse(node=preservation)

    except Exception as e:
        print(f"Error extracting drug info: {e}")
    
    return result

def crawl_drug_info(url: str, dest_dir: str):
    results = extract_drug_info(url=url)
    slug = url.rstrip("/").split("/")[-1].replace(".html","")
    filename = slug + ".json"
    with open(f"./data/details/{dest_dir}/{filename}", mode='w', encoding='utf-8') as file:
        file.write(json.dumps(results, ensure_ascii=False, indent=4))