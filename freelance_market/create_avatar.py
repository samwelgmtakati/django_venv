from PIL import Image, ImageDraw, ImageFont
import os

def create_default_avatar():
    # Create a 150x150 image with a light gray background
    img = Image.new('RGB', (150, 150), color='#f0f0f0')
    d = ImageDraw.Draw(img)
    
    # Draw a circle
    d.ellipse((10, 10, 140, 140), fill='#ddd', outline='#999', width=2)
    
    # Add text (first letter of 'User')
    try:
        # Try to use a nice font if available
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Center the text
    text = "U"
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((150 - text_width) // 2, (150 - text_height) // 2 - 10)
    
    d.text(position, text, fill='#666', font=font)
    
    # Save the image
    os.makedirs('static/dashboard/img', exist_ok=True)
    img.save('static/dashboard/img/default-avatar.png')
    print("Default avatar created at: static/dashboard/img/default-avatar.png")

if __name__ == "__main__":
    create_default_avatar()
