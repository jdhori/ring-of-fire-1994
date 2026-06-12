import sys
from PIL import Image
# usage: crop.py SRC OUT x0 y0 x1 y1   (fractions 0-1) [enhance]
src, out = sys.argv[1], sys.argv[2]
x0,y0,x1,y1 = map(float, sys.argv[3:7])
im = Image.open(src)
W,H = im.size
box = (int(x0*W), int(y0*H), int(x1*W), int(y1*H))
c = im.crop(box)
c.save(out, quality=90)
print(f"{out}: {c.size} from {src}{im.size}")
