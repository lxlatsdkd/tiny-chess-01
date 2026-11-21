# tiny-chess-01: 0x88 alpha-beta engine, written from scratch.
# Fixed node budget, no clock, no unseeded randomness: same position,
# same move, so live and replay trials agree.
import json,os,random,sys,urllib.error,urllib.request
ENV=os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")
LIM=100000
MATE=100000
VAL=(0,100,320,330,500,900,0)
PHA=(0,0,1,1,2,4,0)
ND=(14,18,31,33,-14,-18,-31,-33)
KD=(1,-1,16,-16,15,17,-15,-17)
BD=(15,17,-15,-17)
RD=(1,-1,16,-16)
SQS=tuple(s for s in range(128) if not s&0x88)
CK=[15]*128
for _s,_v in ((0,13),(7,14),(4,12),(112,7),(119,11),(116,3)):
 CK[_s]=_v
P_P=(0,0,0,0,50,50,50,50,10,10,20,30,5,5,10,25,0,0,0,20,5,-5,-10,0,5,10,10,-20,0,0,0,0)
P_N=(-50,-40,-30,-30,-40,-20,0,0,-30,0,10,15,-30,5,15,20,-30,0,15,20,-30,5,10,15,-40,-20,0,5,-50,-40,-30,-30)
P_B=(-20,-10,-10,-10,-10,0,0,0,-10,0,5,10,-10,5,5,10,-10,0,10,10,-10,10,10,10,-10,5,0,0,-20,-10,-10,-10)
P_R=(0,0,0,0,5,10,10,10,-5,0,0,0,-5,0,0,0,-5,0,0,0,-5,0,0,0,-5,0,0,0,0,0,0,5)
P_Q=(-20,-10,-10,-5,-10,0,0,0,-10,0,5,5,-5,0,5,5,-5,0,5,5,0,0,5,5,-10,5,5,5,-10,0,5,0,-20,-10,-10,-5)
P_K=(-30,-40,-40,-50,-30,-40,-40,-50,-30,-40,-40,-50,-30,-40,-40,-50,-20,-30,-30,-40,-10,-20,-20,-20,20,20,0,0,20,30,10,0)
def _mk(t):
 w=[0]*128
 b=[0]*128
 for s in SQS:
  r,f=s>>4,s&7
  if f>3:
   f=7-f
  w[s]=t[(7-r)*4+f]
  b[s]=t[r*4+f]
 return w,b
PW,PB=_mk(P_P)
NW,NB=_mk(P_N)
BW,BB=_mk(P_B)
RW,RB=_mk(P_R)
QW,QB=_mk(P_Q)
KW,KB=_mk(P_K)
TW=(None,PW,NW,BW,RW,QW,KW)
TB=(None,PB,NB,BB,RB,QB,KB)
_R=random.Random(42)
Z=[[_R.getrandbits(64) for _ in range(128)] for _ in range(15)]
ZS=_R.getrandbits(64)
ZC=[_R.getrandbits(64) for _ in range(16)]
ZE=[_R.getrandbits(64) for _ in range(8)]
B=[0]*128
side=0
cast=0
ep=-1
half=0
key=0
ksq=[4,116]
stk=[]
path=set()
hist={}
tt={}
kil=[[0,0] for _ in range(128)]
his=[[0]*128 for _ in range(15)]
nodes=0
PC={'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6,'p':9,'n':10,'b':11,'r':12,'q':13,'k':14}
START="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CAS=((1,4,6,7,5,(4,5,6),(5,6)),(2,4,2,0,3,(4,3,2),(3,2,1)),(4,116,118,119,117,(116,117,118),(117,118)),(8,116,114,112,115,(116,115,114),(115,114,113)))
def parse(fen):
 global B,side,cast,ep,half,key
 B=[0]*128
 w=fen.split()
 for i,row in enumerate(w[0].split("/")):
  f=0
  for ch in row:
   if ch.isdigit():
    f+=int(ch)
   else:
    B[(7-i)*16+f]=PC[ch]
    f+=1
 side=0 if w[1]=='w' else 1
 cast=sum(v for k,v in (('K',1),('Q',2),('k',4),('q',8)) if k in w[2])
 ep=-1 if w[3]=='-' else (ord(w[3][0])-97)+(int(w[3][1])-1)*16
 half=int(w[4]) if len(w)>4 else 0
 ksq[0]=next(s for s in SQS if B[s]==6)
 ksq[1]=next(s for s in SQS if B[s]==14)
 key=0
 for s in SQS:
  p=B[s]
  if p:
   key^=Z[p][s]
 if side:
  key^=ZS
 key^=ZC[cast]
 if ep>=0:
  key^=ZE[ep&7]
def attacked(s,by):
 if by==0:
  for u in (s-15,s-17):
   if not u&0x88 and B[u]==1:
    return 1
 else:
  for u in (s+15,s+17):
   if not u&0x88 and B[u]==9:
    return 1
 for d in ND:
  u=s+d
  if not u&0x88 and B[u]==(2 if by==0 else 10):
   return 1
 for d in KD:
  u=s+d
  if not u&0x88 and B[u]==(6 if by==0 else 14):
   return 1
 for d in BD+RD:
  u=s+d
  while not u&0x88:
   p=B[u]
   if p:
    if (p>>3)==by and ((p&7)==5 or ((p&7)==3 and d in BD) or ((p&7)==4 and d in RD)):
     return 1
    break
   u+=d
 return 0
def gen():
 ms=[]
 for s in SQS:
  p=B[s]
  if not p or (p>>3)!=side:
   continue
  t=p&7
  if t==1:
   d=16 if side==0 else -16
   tg=[]
   f=s+d
   if not B[f]:
    tg.append(f)
    if (s>>4)==(1 if side==0 else 6) and not B[f+d]:
     tg.append(f+d)
   for u in (s+d-1,s+d+1):
    if u&0x88:
     continue
    q=B[u]
    if (q and (q>>3)!=side) or u==ep:
     tg.append(u)
   for u in tg:
    if (u>>4)==0 or (u>>4)==7:
     for pr in (5,4,3,2):
      ms.append(s|u<<7|pr<<14)
    else:
     ms.append(s|u<<7)
  elif t==2 or t==6:
   for d in ND if t==2 else KD:
    u=s+d
    if u&0x88:
     continue
    q=B[u]
    if not q or (q>>3)!=side:
     ms.append(s|u<<7)
  else:
   for d in BD if t==3 else RD if t==4 else BD+RD:
    u=s+d
    while not u&0x88:
     q=B[u]
     if not q:
      ms.append(s|u<<7)
     else:
      if (q>>3)!=side:
       ms.append(s|u<<7)
      break
     u+=d
 for bit,kf,kt,rf,rt,atk,emp in CAS:
  if cast&bit and B[kf]==(6 if side==0 else 14) and B[rf]==(4 if side==0 else 12) and all(not B[s] for s in emp) and all(not attacked(s,side^1) for s in atk):
   ms.append(kf|kt<<7)
 return ms
def make(m):
 global side,cast,ep,half,key
 f=m&127
 t=m>>7&127
 pr=m>>14
 p=B[f]
 c=B[t]
 cs=t
 if (p&7)==1 and t==ep and not c:
  cs=t-16 if side==0 else t+16
  c=B[cs]
 stk.append((m,c,cs,cast,ep,half,key))
 key^=Z[p][f]
 if c:
  key^=Z[c][cs]
 if (p&7)==1 and t==ep and not B[t]:
  B[cs]=0
 B[f]=0
 np=pr+(side<<3) if pr else p
 B[t]=np
 key^=Z[np][t]
 if (p&7)==6:
  ksq[side]=t
  if abs(t-f)==2:
   r=t+1 if t>f else t-2
   nr=t-1 if t>f else t+1
   B[nr]=B[r]
   B[r]=0
   key^=Z[B[nr]][r]^Z[B[nr]][nr]
 key^=ZC[cast]
 cast&=CK[f]&CK[t]
 key^=ZC[cast]
 if ep>=0:
  key^=ZE[ep&7]
 ep=(f+t)//2 if (p&7)==1 and abs(t-f)==32 else -1
 if ep>=0:
  key^=ZE[ep&7]
 key^=ZS
 side^=1
 half=0 if (p&7)==1 or c else half+1
 rep=key in path or hist.get(key,0)>=1
 path.add(key)
 return rep
def unmake():
 global side,cast,ep,half,key
 m,c,cs,oc,oe,oh,ok=stk.pop()
 f=m&127
 t=m>>7&127
 pr=m>>14
 p=B[t]
 path.discard(key)
 B[f]=(1 if side else 9) if pr else p
 B[t]=0
 if c:
  B[cs]=c
 if (p&7)==6:
  ksq[side^1]=f
  if abs(t-f)==2:
   r=t-1 if t>f else t+1
   nr=t+1 if t>f else t-2
   B[nr]=B[r]
   B[r]=0
 side,cast,ep,half,key=side^1,oc,oe,oh,ok
def evl():
 mg=0
 eg=0
 ph=0
 wb=0
 bb=0
 for s in SQS:
  p=B[s]
  if not p:
   continue
  t=p&7
  ph+=PHA[t]
  if p<8:
   mg+=VAL[t]+TW[t][s]
   eg+=VAL[t]+TW[t][s]
   if t==3:
    wb+=1
   elif t==6:
    eg+=(3-max(abs((s&7)-3.5),abs((s>>4)-3.5)))*12
  else:
   mg-=VAL[t]+TB[t][s]
   eg-=VAL[t]+TB[t][s]
   if t==3:
    bb+=1
   elif t==6:
    eg-=(3-max(abs((s&7)-3.5),abs((s>>4)-3.5)))*12
 if wb>=2:
  mg+=30
  eg+=40
 if bb>=2:
  mg-=30
  eg-=40
 if ph>24:
  ph=24
 sc=(mg*ph+eg*(24-ph))//24
 return (sc if side==0 else -sc)+10
def order(ms,ttm,ply):
 def sc(m):
  if m==ttm:
   return 1<<30
  t=m>>7&127
  v=B[t]
  if v or (m>>14) or ((B[m&127]&7)==1 and t==ep):
   vv=VAL[v&7] if v else (900 if m>>14 else 100)
   return (1<<20)+vv*100-VAL[B[m&127]&7]
  if m==kil[ply][0] or m==kil[ply][1]:
   return 1<<19
  return his[B[m&127]][t]
 ms.sort(key=sc,reverse=True)
 return ms
def store(d,fl,v,bm,ply):
 sv=v
 if sv>MATE-1000:
  sv+=ply
 elif sv<-MATE+1000:
  sv-=ply
 if len(tt)>200000:
  tt.clear()
 tt[key]=(d,fl,sv,bm)
def probe(e,a,b,ply):
 v=e[2]
 if v>MATE-1000:
  v-=ply
 elif v<-MATE+1000:
  v+=ply
 if e[1]==0:
  return v
 if e[1]==1 and v>=b:
  return v
 if e[1]==2 and v<=a:
  return v
 return None
def S(d,a,b,ply):
 global nodes
 nodes+=1
 if nodes>LIM:
  return None
 if half>=100:
  return 0
 q=d<=0
 e=tt.get(key)
 ttm=0
 if e:
  ttm=e[3]
  if q or e[0]>=d:
   v=probe(e,a,b,ply)
   if v is not None:
    return v
 if q:
  st=evl()
  if st>=b:
   return b
  if st>a:
   a=st
 ao=a
 inch=attacked(ksq[side],side^1)
 if inch and not q:
  d+=1
 ms=gen()
 if q and not inch:
  ms=[m for m in ms if B[m>>7&127] or (m>>14) or ((B[m&127]&7)==1 and (m>>7&127)==ep)]
  ms=[m for m in ms if st+(VAL[B[m>>7&127]&7] if B[m>>7&127] else (900 if m>>14 else 100))+150>=a]
 order(ms,ttm,ply)
 best=(-MATE+ply if inch else a) if q else -MATE
 bm=0
 n=0
 for m in ms:
  t=m>>7&127
  f=m&127
  cap=B[t] or (m>>14) or ((B[f]&7)==1 and t==ep)
  rep=make(m)
  if attacked(ksq[side^1],side):
   unmake()
   continue
  n+=1
  if q:
   s=0 if rep else S(0,-b,-a,ply+1)
  elif n==1 or inch or cap:
   s=0 if rep else S(d-1,-b,-a,ply+1)
  elif d>=3 and n>=4:
   s=0 if rep else S(d-2,-b,-a,ply+1)
   if s is not None and -s>a:
    s=0 if rep else S(d-1,-b,-a,ply+1)
  else:
   s=0 if rep else S(d-1,-b,-a,ply+1)
  unmake()
  if s is None:
   return None
  v=-s
  if v>best:
   best=v
   bm=m
  if v>a:
   a=v
  if a>=b:
   if not q and not cap:
    if kil[ply][0]!=m:
     kil[ply][1]=kil[ply][0]
     kil[ply][0]=m
    his[B[f]][t]+=d*d
   break
 if n==0 and not q:
  return -MATE+ply if inch else 0
 store(0 if q else d,1 if best>=b else (2 if best<=ao else 0),best,bm,ply)
 return best
def root():
 global nodes
 nodes=0
 ms=[]
 for m in gen():
  make(m)
  if not attacked(ksq[side^1],side):
   ms.append(m)
  unmake()
 if not ms:
  return 0
 if len(ms)==1:
  return ms[0]
 path.clear()
 path.add(key)
 order(ms,0,0)
 best=ms[0]
 d=1
 while d<=32:
  cur=0
  cv=-MATE
  bad=False
  for m in ms:
   rep=make(m)
   s=0 if rep else S(d-1,-MATE,-cv,1)
   unmake()
   if s is None:
    bad=True
    break
   v=-s
   if v>cv:
    cv=v
    cur=m
  if bad or not cur:
   break
  best=cur
  ms.remove(cur)
  ms.insert(0,cur)
  d+=1
 path.discard(key)
 return best
def build_hist(moves):
 global hist
 hist={}
 parse(START)
 path.clear()
 for u in moves:
  f=(ord(u[0])-97)+(int(u[1])-1)*16
  t=(ord(u[2])-97)+(int(u[3])-1)*16
  pr={'q':5,'r':4,'b':3,'n':2}.get(u[4] if len(u)==5 else '',0)
  make(f|t<<7|pr<<14)
  hist[key]=hist.get(key,0)+1
 path.clear()
def post(path_,body):
 req=urllib.request.Request(ENV+path_,data=json.dumps(body).encode(),headers={"content-type":"application/json"})
 try:
  with urllib.request.urlopen(req) as res:
   return json.load(res)
 except urllib.error.HTTPError as e:
  sys.exit(f"{path_}: HTTP {e.code} {e.read().decode(errors='replace')}")
def main():
 while True:
  g=post("/game",{})
  if g.get("status")=="done":
   break
  while g.get("status")=="your_move":
   parse(g["fen"])
   build_hist(g["moves"])
   m=root()
   if not m:
    sys.exit("no legal move at root")
   f=m&127
   t=m>>7&127
   u="abcdefgh"[f&7]+str((f>>4)+1)+"abcdefgh"[t&7]+str((t>>4)+1)+(" pnbrqk"[m>>14] if m>>14 else "")
   g=post("/move",{"game":g["game"],"move":u})
  print(f"game {g.get('game')}: {g.get('outcome')} by {g.get('reason')}",file=sys.stderr)
 print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost",file=sys.stderr)
if __name__=="__main__":
 main()
