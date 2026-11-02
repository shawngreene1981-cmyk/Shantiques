import sys, cv2, numpy as np
from PIL import Image, ImageOps
orig_p, mask_p, out_p = sys.argv[1:4]
im = ImageOps.exif_transpose(Image.open(orig_p)).convert("RGB")
W,H = im.size
a = np.array(Image.open(mask_p).convert("RGBA").split()[3].resize((W,H), Image.LANCZOS))
img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
m = np.full((H,W), cv2.GC_PR_BGD, np.uint8)
m[a>40] = cv2.GC_PR_FGD
k = max(3, W//60)
m[cv2.erode((a>200).astype(np.uint8), np.ones((k,k)))>0] = cv2.GC_FGD
m[cv2.dilate((a>15).astype(np.uint8), np.ones((k,k)))==0] = cv2.GC_BGD
bg,fg = np.zeros((1,65)),np.zeros((1,65))
cv2.grabCut(img, m, None, bg, fg, 4, cv2.GC_INIT_WITH_MASK)
alpha = np.where((m==1)|(m==3),255,0).astype(np.uint8)
# drop small stray specks (keep pieces at least 3% the size of the largest)
n,lab,st,_ = cv2.connectedComponentsWithStats((alpha>0).astype(np.uint8),8)
if n>2:
    big = st[1:,cv2.CC_STAT_AREA].max()
    for i in range(1,n):
        if st[i,cv2.CC_STAT_AREA] < 0.03*big: alpha[lab==i]=0
alpha = cv2.GaussianBlur(alpha,(3,3),0)
# place on soft cream background, centered with margin
rgba = np.dstack([np.array(im), alpha])
ys,xs = np.where(alpha>20); x0,x1,y0,y1 = xs.min(),xs.max(),ys.min(),ys.max()
crop = Image.fromarray(rgba[y0:y1+1,x0:x1+1])
side = int(max(crop.size)*1.15)
canvas = Image.new("RGB",(side,side),(250,247,240))
canvas.paste(crop,((side-crop.width)//2,(side-crop.height)//2),crop)
canvas.save(out_p, quality=90)
