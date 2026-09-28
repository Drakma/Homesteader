from PIL import Image
img = Image.open(r"C:\Users\casey\Downloads\sun-moon.jpg")
print(img.size, img.mode)
img.thumbnail((512, 512))
img.save(r"C:\Users\casey\Desktop\Homesteader\preview\sun_moon_thumb.png")
