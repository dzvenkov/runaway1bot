from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
from PIL import Image
import cv2

class RealESRGAN_Inference():
    def __init__(self) -> None:
        self.model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        self.upsampler = RealESRGANer(
                scale=2,
                model_path="RealESRGAN_x2plus.pth",
                model=self.model,
                half=False)

    def upsample(self, image : Image):
        output, _ = self.upsampler.enhance(image, outscale=2)
        return output
    

if __name__ == '__main__':
        path = "sample.jpeg"
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        inf = RealESRGAN_Inference()
        output = inf.upsample(img)
        cv2.imwrite("output.jpeg", output)