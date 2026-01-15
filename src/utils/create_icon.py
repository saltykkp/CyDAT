from PIL import Image, ImageDraw
import math

def create_icon():
    size = 256
    padding = 20
    # Create dark rounded background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle (dark background)
    bg_color = (25, 25, 30, 255)
    r = size // 2
    # Draw large circle for rounded rect approximation or just use a standard rounded rect path
    # For simplicity, let's draw a super-ellipse or rounded rect
    draw.rounded_rectangle([(0,0), (size, size)], radius=60, fill=bg_color)
    
    # Draw "C" dots
    # Center (cx, cy)
    cx, cy = size // 2, size // 2
    radius = 70 # Radius of the C arc
    dot_radius = 28
    
    # Colors from the image description (Purple, Red, Orange, Blue, Cyan, Green)
    colors = [
        (160, 100, 255), # Purple
        (255, 80, 80),   # Red
        (255, 120, 80),  # Orange
        (80, 120, 255),  # Blue
        (80, 200, 255),  # Cyan
        (80, 255, 160),  # Green
    ]
    
    # Angles for C shape (roughly from 45 degrees to 315 degrees?)
    # Let's place 7 dots along an arc
    start_angle = -60
    end_angle = 240
    
    # We have 7 dots in the image? OCR says "C shape". 
    # Let's place dots in a circle but leave a gap on the right.
    
    # Positions based on visual estimation of a "C"
    # Top-Right, Top, Top-Left, Left, Bottom-Left, Bottom, Bottom-Right
    # Angles in degrees (0 is right, 90 is bottom in PIL? No, standard trig: 0 right, -90 top)
    
    # Let's try 7 dots
    dots = 7
    # Angles: -45 (Top Right), -90 (Top), -135 (Top Left), 180 (Left), 135 (Bottom Left), 90 (Bottom), 45 (Bottom Right)
    # Actually let's just distribute them
    
    angles = [-45, -90, -135, 180, 135, 90, 45]
    # Re-order colors to match gradients if possible, or just cycle
    
    # Correct order based on typical "C" drawing
    # Start from top right end of C, go counter-clockwise?
    # Or just place them
    
    # Let's use a simple list of angles for the C
    # The C opens to the right. So we fill from e.g. -60 to 60 degrees (gap)
    # We draw from 60 to 300 degrees?
    
    dots_pos = []
    
    # Manually placing dots for a nice C shape
    # 1. Top Right (start of C top)
    dots_pos.append((cx + int(radius * math.cos(math.radians(-50))), cy + int(radius * math.sin(math.radians(-50))), colors[1])) # Redish
    # 2. Top
    dots_pos.append((cx + int(radius * math.cos(math.radians(-100))), cy + int(radius * math.sin(math.radians(-100))), colors[0])) # Purple
    # 3. Left Top
    dots_pos.append((cx + int(radius * math.cos(math.radians(-150))), cy + int(radius * math.sin(math.radians(-150))), colors[3])) # Blue
    # 4. Left
    dots_pos.append((cx + int(radius * math.cos(math.radians(180))), cy + int(radius * math.sin(math.radians(180))), colors[3])) # Blue
    # 5. Left Bottom
    dots_pos.append((cx + int(radius * math.cos(math.radians(150))), cy + int(radius * math.sin(math.radians(150))), colors[4])) # Cyan
    # 6. Bottom
    dots_pos.append((cx + int(radius * math.cos(math.radians(100))), cy + int(radius * math.sin(math.radians(100))), colors[5])) # Green
    # 7. Bottom Right
    dots_pos.append((cx + int(radius * math.cos(math.radians(50))), cy + int(radius * math.sin(math.radians(50))), colors[5])) # Greenish
    
    for x, y, col in dots_pos:
        draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill=col + (255,))
        # Add a subtle glow? (optional, skip for simple icon)

    img.save('resources/icon.png')
    print("Icon created at resources/icon.png")

if __name__ == "__main__":
    create_icon()
