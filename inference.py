from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import cv2

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)

upsampler = RealESRGANer(
        scale=2,
        model_path="RealESRGAN_x2plus.pth",
        model=model,
        half=False)

path = "sample.jpeg"
img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
output, _ = upsampler.enhance(img, outscale=2)

cv2.imwrite("output.jpeg", output)