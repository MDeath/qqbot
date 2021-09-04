def At(ID:int) -> list:
    return {"type": "At","target": ID}

def AtAll() -> dict:
    return {"type": "AtAll"}

def Plain(s:str) -> dict:
    return {
        "type": "Plain",
        "text": s
    }

def Image(ID=None, url=None, path=None, base64=None) -> dict:
    if not (ID or url or path or base64):return
    return {
            "type": "Image",
            "imageId": (ID and f"{ID}.mirai") or None,  #群图片格式
            "url": url or None, # 可
            "path": path or None,
            "base64": base64 or None
        }

def FlashImage(ID=None, url=None, path=None, base64=None) -> dict:
    if not (ID or url or path or base64):return
    return {
            "type": "Image",
            "imageId": (ID and f"{ID}.mirai") or None,  #群图片格式
            "url": url or None, # 可
            "path": path or None,
            "base64": base64 or None
        }

def Voice(ID=None, url=None, path=None, base64=None) -> dict:
    if not (ID or url or path or base64):return
    return {
            "type": "Image",
            "imageId": f"{ID}.mirai" or None,  #群图片格式
            "url": url or None, # 可
            "path": path or None,
            "base64": base64 or None
        }

def Xml(xml:str) -> dict:
    return {
        "type": "Xml",
        "xml": xml
    }