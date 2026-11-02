# Price tags for the Rollo 4x6 printer: 8 tags (2" x 1.5") per label.
# Usage: python3 build/make_tags.py items.json out.pdf   (items: [{"id","desc","price"}])
import json, os, sys, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
TW,TH=600,450  # 2" x 1.5" at 300 dpi
items=json.load(open(sys.argv[1])); out=sys.argv[2]
LORA='/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
f_desc=ImageFont.truetype(LORA,28); f_price=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',64)
f_small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18); f_id=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24)
a=np.array(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'static','logo.webp')).convert('RGBA')); g=(0.3*a[...,0]+0.59*a[...,1]+0.11*a[...,2])
ink=((a[...,3]>110)&(g<215)).astype(np.uint8)*255
L=Image.fromarray(255-ink).convert('L').crop(Image.fromarray(ink).getbbox()); L.thumbnail((250,96))
def qr(url,size): return Image.fromarray(cv2.QRCodeEncoder.create().encode(url)).convert('L').resize((size,size),Image.NEAREST)
def wrap(d,text,font,w):
    lines=[];cur=''
    for wd in text.split():
        t=(cur+' '+wd).strip()
        if d.textlength(t,font=font)<=w: cur=t
        else: lines.append(cur); cur=wd
    lines.append(cur)
    if len(lines)>2:
        lines=lines[:2]
        while d.textlength(lines[1]+'…',font=font)>w: lines[1]=lines[1].rsplit(' ',1)[0]
        lines[1]=lines[1].rstrip(',')+'…'
    return lines
def tag(it):
    im=Image.new('L',(TW,TH),255); d=ImageDraw.Draw(im)
    d.ellipse((26,22,58,54),outline=0,width=3)
    im.paste(L,((TW-L.width)//2,14)); y=14+L.height+8
    for ln in wrap(d,it['desc'],f_desc,TW-50):
        d.text((TW//2,y),ln,font=f_desc,fill=0,anchor='mt'); y+=34
    Q=150; im.paste(qr('https://shopshantiques.com/#'+it['id'],Q),(TW-26-Q,TH-20-Q))
    base=TH-82
    if it['price']: d.text((32,base),it['price'].replace('.00',''),font=f_price,fill=0,anchor='ls')
    else:
        d.text((32,base),'$',font=f_price,fill=0,anchor='ls'); d.line((80,base-4,TW-200,base-4),fill=0,width=4)
    d.text((32,base+14),it['id'],font=f_id,fill=0)
    d.text((32,base+46),'shopshantiques.com',font=f_small,fill=0)
    return im
pages=[]
for p in range(0,len(items),8):
    pg=Image.new('L',(1200,1800),255); d=ImageDraw.Draw(pg)
    for k,it in enumerate(items[p:p+8]): pg.paste(tag(it),((k%2)*TW,(k//2)*TH))
    for y in range(0,1800,24): d.line((600,y,600,y+12),fill=120,width=2)
    for yy in (450,900,1350):
        for x in range(0,1200,24): d.line((x,yy,x+12,yy),fill=120,width=2)
    pages.append(pg.convert('RGB'))
pages[0].save(out,save_all=True,append_images=pages[1:],resolution=300)
pages[0].save(out.replace('.pdf','-preview.png'))
print(len(items),'tags,',len(pages),'labels')
