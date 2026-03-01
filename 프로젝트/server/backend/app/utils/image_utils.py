def get_image_url(image_filename):
    if not image_filename:
        return None
    
    if image_filename.startswith("http"):
      return image_filename
      
    # 로컬 static 폴더 기준
    return f"/static/{image_filename}"