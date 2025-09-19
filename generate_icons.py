#!/usr/bin/env python3
"""
Icon Generator for PWA
Generates all required icon sizes for the Progressive Web App
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create an icon with the specified size"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors
    background_color = (255, 107, 107, 255)  # #ff6b6b
    text_color = (255, 255, 255, 255)  # White
    
    # Draw background circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=background_color, outline=None)
    
    # Add text (simplified for small sizes)
    if size >= 128:
        # For larger icons, add "🥗" emoji or "AI" text
        try:
            # Try to use a font
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Draw "AI" text
        text = "AI"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), text, fill=text_color, font=font)
    else:
        # For smaller icons, just draw a simple shape
        center = size // 2
        radius = size // 4
        draw.ellipse([center-radius, center-radius, center+radius, center+radius], 
                    fill=text_color)
    
    # Save the icon
    img.save(f"icons/{filename}")
    print(f"Created {filename} ({size}x{size})")

def main():
    """Generate all required icon sizes"""
    # Ensure icons directory exists
    os.makedirs("icons", exist_ok=True)
    
    # Define required icon sizes
    icon_sizes = [
        (16, "icon-16x16.png"),
        (32, "icon-32x32.png"),
        (72, "icon-72x72.png"),
        (96, "icon-96x96.png"),
        (128, "icon-128x128.png"),
        (144, "icon-144x144.png"),
        (152, "icon-152x152.png"),
        (192, "icon-192x192.png"),
        (384, "icon-384x384.png"),
        (512, "icon-512x512.png")
    ]
    
    print("🎨 Generating PWA icons...")
    
    for size, filename in icon_sizes:
        create_icon(size, filename)
    
    print("✅ All icons generated successfully!")
    print("\n📱 Your PWA is now ready for Android installation!")
    print("\nTo install on Android:")
    print("1. Open your app in Chrome browser")
    print("2. Tap the menu (3 dots) in Chrome")
    print("3. Select 'Add to Home screen' or 'Install app'")
    print("4. The app will appear on your home screen like a native app!")

if __name__ == "__main__":
    main()
