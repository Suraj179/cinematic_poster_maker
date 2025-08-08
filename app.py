import streamlit as st
from rembg import remove
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import io

# ---------- Streamlit Config ----------
st.set_page_config(page_title="Cinematic Poster Maker", page_icon="🎬", layout="centered")
st.title("🎬 Cinematic Poster with Shadow & Glow")

# ---------- User Inputs ----------
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
user_text = st.text_input("Enter your stylish background text", "YOUR TEXT HERE")
font_size = st.slider("Font size", 30, 200, 80, 5)
color1 = st.color_picker("Pick first gradient color", "#FF00FF")
color2 = st.color_picker("Pick second gradient color", "#00FFFF")
opacity = st.slider("Text opacity", 50, 255, 180)
rings = st.slider("Number of rings", 1, 5, 3)
spiral_mode = st.checkbox("Enable Spiral Mode")
spiral_spacing = st.slider("Spiral spacing (only if spiral mode)", 0, 200, 50)

# Shadow & Glow Controls
add_shadow = st.checkbox("Add Shadow", True)
shadow_offset = st.slider("Shadow offset", 0, 50, 15)
shadow_blur = st.slider("Shadow blur", 0, 50, 20)
add_glow = st.checkbox("Add Glow", True)
glow_color = st.color_picker("Glow color", "#FFD700")
glow_size = st.slider("Glow size", 0, 50, 25)

# ---------- Helper Function ----------
def draw_circular_text(draw, text, center, radius, font, color1, color2, opacity, spiral=False, spacing=50):
    text = text.strip()
    if not text:
        return

    circumference = 2 * math.pi * radius
    repeated_text = (text + "   ") * (int(circumference // (font.getsize(text)[0])) + 5)

    angle = 0
    for i, char in enumerate(repeated_text):
        ratio = i / len(repeated_text)
        r = int(int(color1[1:3], 16) * (1 - ratio) + int(color2[1:3], 16) * ratio)
        g = int(int(color1[3:5], 16) * (1 - ratio) + int(color2[3:5], 16) * ratio)
        b = int(int(color1[5:7], 16) * (1 - ratio) + int(color2[5:7], 16) * ratio)

        w, h = draw.textsize(char, font=font)
        char_angle = (w / circumference) * 360

        theta = math.radians(angle + char_angle / 2)
        x = center[0] + radius * math.cos(theta) - w / 2
        y = center[1] + radius * math.sin(theta) - h / 2

        temp_img = Image.new("RGBA", (w * 4, h * 4), (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((w, h), char, font=font, fill=(r, g, b, opacity))
        rotated = temp_img.rotate(-(angle + char_angle / 2), resample=Image.BICUBIC, center=(w*2, h*2))

        draw.bitmap((x, y), rotated, fill=None)

        angle += char_angle
        if spiral:
            radius += spacing / len(repeated_text)

# ---------- Processing ----------
if uploaded_file and user_text:
    # Load image
    original_image = Image.open(uploaded_file).convert("RGBA")

    # Remove background
    with st.spinner("Removing background..."):
        img_bytes = io.BytesIO()
        original_image.save(img_bytes, format="PNG")
        img_no_bg = remove(img_bytes.getvalue())
        subject = Image.open(io.BytesIO(img_no_bg)).convert("RGBA")

    # Prepare layers
    bg_width, bg_height = original_image.size
    background = Image.new("RGBA", (bg_width, bg_height), (255, 255, 255, 255))
    text_layer = Image.new("RGBA", (bg_width, bg_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)

    try:
        font = ImageFont.truetype("fonts/BebasNeue.ttf", size=font_size)
    except:
        font = ImageFont.load_default()

    # Draw multiple rings
    for i in range(rings):
        radius = (min(bg_width, bg_height) // 4) + (i * font_size * 1.5)
        draw_circular_text(draw, user_text, (bg_width//2, bg_height//2),
                           radius, font, color1, color2, opacity,
                           spiral=spiral_mode, spacing=spiral_spacing)

    # Combine text with background
    background = Image.alpha_composite(background, text_layer)

    # Add Shadow
    if add_shadow:
        shadow = Image.new("RGBA", subject.size, (0, 0, 0, 255))
        shadow_mask = subject.split()[3]
        shadow.putalpha(shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        background.paste(shadow, (shadow_offset, shadow_offset), shadow)

    # Add Glow
    if add_glow:
        glow = Image.new("RGBA", subject.size, (
            int(glow_color[1:3], 16),
            int(glow_color[3:5], 16),
            int(glow_color[5:7], 16),
            255
        ))
        glow_mask = subject.split()[3]
        glow.putalpha(glow_mask)
        glow = glow.filter(ImageFilter.GaussianBlur(glow_size))
        background.paste(glow, (0, 0), glow)

    # Overlay subject
    final_image = background.copy()
    final_image.paste(subject, (0, 0), subject)

    # Output
    st.subheader("Final Cinematic Poster")
    st.image(final_image, use_column_width=True)

    img_bytes_out = io.BytesIO()
    final_image.save(img_bytes_out, format="PNG")
    st.download_button("Download Poster", img_bytes_out.getvalue(),
                       file_name="cinematic_poster_shadow_glow.png", mime="image/png")
