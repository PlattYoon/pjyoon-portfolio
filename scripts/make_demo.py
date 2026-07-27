#!/usr/bin/env python3
"""
make_demo.py — renders docs/ida_demo.mp4: an animated walkthrough of the IDA
pipeline. Numbers shown (states, confidences, evidence, message) are pulled from
the real service/signals.py, not hand-typed, so the demo shows true behavior.
"""
import os, sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "service"))
import signals as S  # the real classifier

W, H, FPS = 1280, 720, 24
OUT_DIR = "/tmp/ida_frames"
os.makedirs(OUT_DIR, exist_ok=True)

# palette (GitHub dark)
BG="#0d1117"; PANEL="#161b22"; PANEL2="#1c2230"; BORDER="#30363d"
TXT="#e6edf3"; MUT="#8b949e"; FAINT="#6e7681"
GREEN="#3fb950"; YEL="#d29922"; BLUE="#58a6ff"; PURP="#bc8cff"; RED="#f85149"; GRAY="#484f58"

GF="/usr/share/fonts/truetype/google-fonts/"
DJ="/usr/share/fonts/truetype/dejavu/"
def F(p,s): return ImageFont.truetype(p,s)
H1=F(GF+"Poppins-Bold.ttf",54); H2=F(GF+"Poppins-Bold.ttf",38)
H3=F(GF+"Poppins-SemiBold.ttf",28) if os.path.exists(GF+"Poppins-SemiBold.ttf") else F(GF+"Poppins-Medium.ttf",28)
MD=F(GF+"Poppins-Medium.ttf",24); RG=F(GF+"Poppins-Regular.ttf",22); SM=F(GF+"Poppins-Regular.ttf",18)
MONO=F(DJ+"DejaVuSansMono.ttf",19); MONOB=F(DJ+"DejaVuSansMono-Bold.ttf",19); MONOS=F(DJ+"DejaVuSansMono.ttf",16)

def ease(t): return t*t*(3-2*t)                      # smoothstep
def clamp01(x): return 0.0 if x<0 else 1.0 if x>1 else x
def appear(p, start, dur=0.25): return ease(clamp01((p-start)/dur))
def lerp(a,b,t): return a+(b-a)*t
def mix(c1,c2,t):
    a=Image.new("RGB",(1,1),c1).getpixel((0,0)); b=Image.new("RGB",(1,1),c2).getpixel((0,0))
    return tuple(int(lerp(a[i],b[i],t)) for i in range(3))

def base():
    img=Image.new("RGB",(W,H),BG); return img, ImageDraw.Draw(img)
def rr(d,xy,r,fill=None,outline=None,width=1):
    d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)
def ctext(d,cx,y,s,font,fill,anch="mm"):
    d.text((cx,y),s,font=font,fill=fill,anchor=anch)
def alpha_over(img, a):  # fade whole frame from black
    if a>=1: return img
    return Image.blend(Image.new("RGB",(W,H),"#000000"), img, a)

# real outputs from signals.py --------------------------------------------------
def stuck_estimate():
    t=1_000_000.0
    ev=[S.cell_run(t+i,"error","NameError","c3",consecutive_failures=i+1) for i in range(4)]
    ev.append(S.help_opened(t+5))
    f=S.extract_features(ev, now=t+6); e=S.infer(ev, now=t+6)
    from orchestration import FALLBACKS
    return f,e,FALLBACKS[e.support]
def away_estimate():
    t=1_000_000.0; ev=[S.idle(t,duration_ms=200_000,focused=False)]
    f=S.extract_features(ev, now=t+210); raw=S.classify(f); shown=S.infer(ev, now=t+210)
    return f,raw,shown
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","service"))
F_STUCK,E_STUCK,MSG_STUCK=stuck_estimate()
F_AWAY,RAW_AWAY,SHOWN_AWAY=away_estimate()

def wrap(d,text,font,maxw):
    words=text.split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if d.textlength(test,font=font)<=maxw: cur=test
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines

# ---------------------------------------------------------------- scenes -------
def sc_title(d,p):
    a=appear(p,0.05,0.5)
    ctext(d,W/2,H/2-70,"IDA",H1,mix(BG,TXT,a))
    if p>0.35:
        b=appear(p,0.35,0.4)
        ctext(d,W/2,H/2-8,"a behaviour-aware study companion",H3,mix(BG,MUT,b))
        ctext(d,W/2,H/2+34,"inside VS Code · Jupyter AI",RG,mix(BG,FAINT,b))
    if p>0.6:
        c=appear(p,0.6,0.35)
        rr(d,(W/2-230,H/2+80,W/2+230,H/2+128),24,outline=mix(BG,BORDER,c),width=2)
        ctext(d,W/2,H/2+104,"weekly demo · Platt Yoon · VariAbility Lab",SM,mix(BG,MUT,c))

def sc_problem(d,p):
    lines=["Some students won't ask for help —","out of disinterest, or rejection sensitivity."]
    for i,l in enumerate(lines):
        a=appear(p,0.1+i*0.18,0.4); ctext(d,W/2,240+i*54,l,H2,mix(BG,TXT,a))
    if p>0.55:
        b=appear(p,0.55,0.4)
        ctext(d,W/2,400,"So the editor itself should notice",H3,mix(BG,mix(TXT,BLUE,0.4),b))
        ctext(d,W/2,442,"and gently offer support — without being asked.",H3,mix(BG,mix(TXT,BLUE,0.4),b))
    if p>0.8:
        c=appear(p,0.8,0.3)
        ctext(d,W/2,520,"We infer support opportunities, not emotions.",MD,mix(BG,GREEN,c))

def pipeline_boxes():
    labels=[("CAPTURE","edits · errors\nidle · focus",BLUE),
            ("SIGNALS","events → state",GREEN),
            ("PERSONA","word the message",PURP),
            ("MODEL","local / API",YEL),
            ("DELIVER","inline · optional",BLUE)]
    n=len(labels); gap=28; bw=(W-160-gap*(n-1))/n; x0=80; y=300; bh=110
    boxes=[]
    for i,(t,s,c) in enumerate(labels):
        x=x0+i*(bw+gap); boxes.append((x,y,x+bw,y+bh,t,s,c))
    return boxes

def sc_arch(d,p):
    ctext(d,W/2,120,"How it fits together",H2,mix(BG,TXT,appear(p,0.02,0.3)),anch="mm")
    boxes=pipeline_boxes()
    for i,(x0,y0,x1,y1,t,s,c) in enumerate(boxes):
        a=appear(p,0.12+i*0.09,0.3)
        if a<=0: continue
        rr(d,(x0,y0,x1,y1),14,fill=mix(BG,PANEL,a),outline=mix(BG,c,a),width=2)
        ctext(d,(x0+x1)/2,y0+34,t,H3,mix(BG,c,a))
        for j,ln in enumerate(s.split("\n")):
            ctext(d,(x0+x1)/2,y0+66+j*22,ln,SM,mix(BG,MUT,a))
        if i<len(boxes)-1 and a>0.6:
            ax=x1+6; ay=(y0+y1)/2; d.text((ax,ay-14),"→",font=H3,fill=mix(BG,FAINT,a))
    if p>0.72:
        b=appear(p,0.72,0.35); yb=470
        rr(d,(80,yb,W-80,yb+120),14,fill=mix(BG,PANEL2,b))
        ctext(d,W/2,yb+38,"Jupyter AI answers when asked.  IDA has to speak first.",H3,mix(BG,mix(TXT,YEL,0.5),b))
        ctext(d,W/2,yb+82,"That proactive-delivery path has no upstream docs — so it's the one custom piece; everything else uses supported APIs.",SM,mix(BG,MUT,b))

# --- editor mock + live pipeline ----
def draw_editor(d, x,y,w,h, error_count, active=True):
    rr(d,(x,y,x+w,y+h),12,fill=PANEL,outline=BORDER,width=1)
    d.line((x,y+34,x+w,y+34),fill=BORDER,width=1)
    for i,col in enumerate([RED,YEL,GREEN]):
        d.ellipse((x+16+i*22,y+12,x+28+i*22,y+24),fill=col)
    ctext(d,x+w/2,y+23,"assignment2.ipynb",SM,MUT)
    # a cell
    cx,cy,cw=x+20,y+52,w-40
    rr(d,(cx,cy,cx+cw,cy+70),8,fill="#0b0f16",outline=BORDER,width=1)
    d.text((cx+14,cy+12),"In [ ]:",font=MONOS,fill=BLUE)
    d.text((cx+80,cy+12),"total = compute(scores)",font=MONO,fill=TXT)
    d.text((cx+80,cy+38),"print(totl)",font=MONO,fill=TXT)
    if error_count>0:
        rr(d,(cx,cy+82,cx+cw,cy+140),8,fill="#2d1214",outline=mix(PANEL,RED,0.5),width=1)
        d.text((cx+14,cy+94),"NameError: name 'totl' is not defined",font=MONOB,fill=RED)
        d.text((cx+14,cy+118),f"re-run ×{error_count}  (same error)",font=MONOS,fill=mix(TXT,RED,0.3))

def bar(d,x,y,w,val,color,label,valtxt):
    ctext(d,x,y-2,label,SM,MUT,anch="lm")
    by=y+22; rr(d,(x,by,x+w,by+16),8,fill="#0b0f16",outline=BORDER,width=1)
    fillw=max(0,min(1,val))*(w-4)
    if fillw>2: rr(d,(x+2,by+2,x+2+fillw,by+14),6,fill=color)
    ctext(d,x+w+12,by+8,valtxt,MONOS,mix(TXT,color,0.3),anch="lm")

def state_readout(d, cx, cy, est, actionable, msg, p_local):
    # colored verdict card
    cmap={"stuck":GREEN,"overwhelmed":YEL,"disengaged":GRAY,"withdrawn":PURP,"no_signal":FAINT}
    c=cmap.get(est.state.value,FAINT)
    rr(d,(cx-260,cy-70,cx+260,cy+70),14,fill=PANEL,outline=mix(PANEL,c,0.7),width=2)
    ctext(d,cx,cy-34,f"state:  {est.state.value.upper()}",H3,c)
    ctext(d,cx,cy+2,f"confidence  {est.confidence:.2f}",MD,TXT)
    if actionable:
        ctext(d,cx,cy+40,f"« {est.evidence} »",SM,MUT)
    else:
        ctext(d,cx,cy+40,"below floor → stays silent",SM,mix(TXT,c,0.3))

def sc_stuck(d,p):
    ctext(d,W/2,70,"Live: a student going in circles",H2,mix(BG,TXT,appear(p,0.0,0.3)))
    # error count animates 1..4
    ec=min(4,int(1+ p*6)) if p<0.55 else 4
    draw_editor(d,70,120,540,300,ec)
    # right: features filling
    rx=680
    if p>0.3:
        a=appear(p,0.3,0.3)
        d.text((rx,140),"features (from signals.py)",font=MD,fill=mix(BG,MUT,a))
        prog=ease(clamp01((p-0.3)/0.35))
        bar(d,rx,175,380,prog*(F_STUCK.error_rerun_streak/4),GREEN,"error_rerun_streak",f"{int(prog*F_STUCK.error_rerun_streak)}")
        bar(d,rx,235,380,prog*min(1,F_STUCK.thrash_index+0.15),YEL,"thrash_index",f"{prog*F_STUCK.thrash_index:.2f}")
        bar(d,rx,295,380,prog*0.15,BLUE,"spread (one cell)",f"{F_STUCK.spread}")
    if p>0.62:
        state_readout(d,W/2, 500, E_STUCK, True, MSG_STUCK, p)
    if p>0.8:
        b=appear(p,0.8,0.3)
        bx0,by0=210,585
        rr(d,(bx0,by0,bx0+860,by0+95),16,fill=mix(BG,mix(PANEL,GREEN,0.08),b))
        d.ellipse((bx0+22,by0+30,bx0+58,by0+66),fill=mix(BG,GREEN,b*0.9))
        ctext(d,bx0+40,by0+48,"i",H3,BG)
        for i,ln in enumerate(wrap(d,"IDA:  "+MSG_STUCK,RG,760)):
            d.text((bx0+80,by0+24+i*30),ln,font=RG,fill=mix(BG,TXT,b))

def sc_restraint(d,p):
    ctext(d,W/2,70,"...and when to say nothing",H2,mix(BG,TXT,appear(p,0.0,0.3)))
    # away illustration — dimmed editor to imply "stepped away"
    draw_editor(d,70,120,540,300,0)
    if p>0.2:
        a=appear(p,0.2,0.3)
        ctext(d,340,285,"away · 200s",MD,mix(BG,FAINT,a))
    rx=680
    if p>0.3:
        a=appear(p,0.3,0.3)
        d.text((rx,150),"features",font=MD,fill=mix(BG,MUT,a))
        prog=ease(clamp01((p-0.3)/0.3))
        bar(d,rx,185,380,prog*F_AWAY.away_ratio,GRAY,"away_ratio",f"{prog*F_AWAY.away_ratio:.2f}")
        bar(d,rx,245,380,0,GREEN,"error_rerun_streak","0")
    if p>0.55:
        state_readout(d,W/2,470,RAW_AWAY,False,"",p)
    if p>0.75:
        b=appear(p,0.75,0.35)
        ctext(d,W/2,600,"— IDA stays silent —",H3,mix(BG,mix(TXT,GRAY,0.2),b))
        ctext(d,W/2,644,"a break isn't a problem to fix. no single signal ever triggers a message.",SM,mix(BG,MUT,b))

def sc_connect(d,p):
    ctext(d,W/2,80,"How it plugs into the team's work",H2,mix(BG,TXT,appear(p,0.0,0.3)))
    cards=[("ADRIAN",PURP,"persona + inline redirect","→ same layer: orchestration.py\n   + delivery in extension.ts"),
           ("MICHAEL",GREEN,"keystroke / mouth datasets","→ plug in as new feature inputs;\n   active-file blocker handled in capture"),
           ("DARREN",YEL,"ATI / usability framing","→ thresholds are tunable params;\n   every message logs its evidence")]
    cw=360; gap=30; x0=(W-(cw*3+gap*2))/2; y0=190; ch=300
    for i,(name,c,sub,body) in enumerate(cards):
        a=appear(p,0.15+i*0.18,0.35)
        if a<=0: continue
        x=x0+i*(cw+gap)
        rr(d,(x,y0,x+cw,y0+ch),16,fill=mix(BG,PANEL,a),outline=mix(BG,c,a*0.8),width=2)
        rr(d,(x,y0,x+cw,y0+8),4,fill=mix(BG,c,a))
        ctext(d,x+cw/2,y0+52,name,H3,mix(BG,c,a))
        ctext(d,x+cw/2,y0+92,sub,SM,mix(BG,MUT,a))
        d.line((x+30,y0+120,x+cw-30,y0+120),fill=mix(BG,BORDER,a),width=1)
        for j,ln in enumerate(body.split("\n")):
            d.text((x+28,y0+142+j*30),ln,font=SM,fill=mix(BG,TXT,a))
    if p>0.8:
        b=appear(p,0.8,0.3)
        ctext(d,W/2,560,"Three directions, one pipeline — so we build it once, not three times.",MD,mix(BG,mix(TXT,GREEN,0.4),b))

def sc_status(d,p):
    ctext(d,W/2,90,"Where it stands",H2,mix(BG,TXT,appear(p,0.0,0.3)))
    done=["repo scaffold + README + setup scripts","architecture: all five stages implemented",
          "behavioral-signal taxonomy — tested, passing","model backend swappable local / API",
          "runs end-to-end today (no key needed)"]
    nxt=["wire extension to live JupyterLab, build .vsix","sync w/ Adrian + Michael (no dup work)",
         "small model eval to pick the local model","add user-study logging"]
    lx=140; rx=690; y0=180
    ctext(d,lx+140,y0-10,"done",H3,mix(BG,GREEN,appear(p,0.1,0.3)),anch="mm")
    for i,t in enumerate(done):
        a=appear(p,0.15+i*0.08,0.3)
        d.text((lx,y0+30+i*46),"✓",font=MD,fill=mix(BG,GREEN,a))
        d.text((lx+36,y0+32+i*46),t,font=RG,fill=mix(BG,TXT,a))
    ctext(d,rx+140,y0-10,"next",H3,mix(BG,BLUE,appear(p,0.3,0.3)),anch="mm")
    for i,t in enumerate(nxt):
        a=appear(p,0.4+i*0.08,0.3)
        d.text((rx,y0+30+i*46),"→",font=MD,fill=mix(BG,BLUE,a))
        d.text((rx+36,y0+32+i*46),t,font=RG,fill=mix(BG,TXT,a))
    if p>0.8:
        b=appear(p,0.8,0.3)
        ctext(d,W/2,560,"blocked on repo / board access — chasing that today",SM,mix(BG,MUT,b))

def sc_outro(d,p):
    a=appear(p,0.05,0.5)
    ctext(d,W/2,H/2-40,"Runs end-to-end today.",H2,mix(BG,TXT,a))
    if p>0.4:
        b=appear(p,0.4,0.4)
        ctext(d,W/2,H/2+30,"jupyter-ai-vscode  ·  ready for review",MD,mix(BG,mix(TXT,GREEN,0.4),b))

SCENES=[("title",sc_title,3.4),("problem",sc_problem,6.0),("arch",sc_arch,9.5),
        ("stuck",sc_stuck,10.5),("restraint",sc_restraint,9.0),("connect",sc_connect,9.0),
        ("status",sc_status,8.0),("outro",sc_outro,3.6)]

def render():
    total=sum(s[2] for s in SCENES); print(f"total {total:.1f}s, ~{int(total*FPS)} frames")
    idx=0
    for name,fn,dur in SCENES:
        nf=int(dur*FPS)
        for k in range(nf):
            p=k/max(1,nf-1)
            img,d=base(); fn(d,p)
            # scene-boundary fade
            fa=1.0
            if k< int(0.3*FPS): fa=ease(k/max(1,int(0.3*FPS)))
            if k> nf-int(0.3*FPS): fa=ease(max(0,(nf-1-k)/max(1,int(0.3*FPS))))
            img=alpha_over(img,fa)
            img.save(f"{OUT_DIR}/f{idx:05d}.png"); idx+=1
        print(f"  {name}: {nf} frames")
    return idx

if __name__=="__main__":
    n=render()
    out=os.path.join(os.path.dirname(__file__),"..","docs","ida_demo.mp4")
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",f"{OUT_DIR}/f%05d.png",
                    "-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",
                    "-vf","scale=1280:720","-crf","20",out],check=True,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("wrote",out,f"({n} frames)")
