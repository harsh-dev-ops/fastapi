from PIL import Image

img = Image.open("/Users/harsh/Desktop/Astha/Astha2024-Photo.jpg")

rgb_im = img.convert('RGB')
base_width=720
wpercent = (base_width / float(img.size[0]))
hsize = int((float(img.size[1]) * float(wpercent)))
img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
rgb_im.save('Astha2024-Photo.jpg')