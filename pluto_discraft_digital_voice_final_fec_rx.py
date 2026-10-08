import numpy as np
import zlib
from gnuradio import gr
SYNC=0x1ACFFC1D
G0=0o171; G1=0o133
PRE_SYMS=np.array([0,1,2,3]*8,dtype=np.uint8)
PRE_BITS=np.empty(64,dtype=np.uint8)
PRE_BITS[0::2]=PRE_SYMS>>1; PRE_BITS[1::2]=PRE_SYMS&1
SYNC_BITS=np.array([(SYNC>>i)&1 for i in range(31,-1,-1)],dtype=np.uint8)
PAT=np.concatenate((PRE_BITS,SYNC_BITS))
NEXT=np.zeros((64,2),dtype=np.uint8); O0=np.zeros((64,2),dtype=np.uint8); O1=np.zeros((64,2),dtype=np.uint8)
for s in range(64):
    for b in (0,1):
        r=((s<<1)|b)&0x7f; NEXT[s,b]=r&0x3f; O0[s,b]=(r&G0).bit_count()&1; O1[s,b]=(r&G1).bit_count()&1
def vit(c):
    n=len(c)//2; INF=10**9; m=np.full(64,INF,dtype=np.int32); m[0]=0
    ps=np.zeros((n,64),dtype=np.int8); pb=np.zeros((n,64),dtype=np.int8)
    for t in range(n):
        r0=int(c[2*t]); r1=int(c[2*t+1]); nm=np.full(64,INF,dtype=np.int32)
        for s in range(64):
            ms=int(m[s])
            if ms>=INF: continue
            for b in (0,1):
                ns=int(NEXT[s,b]); v=ms+(int(O0[s,b])!=r0)+(int(O1[s,b])!=r1)
                if v<int(nm[ns]): nm[ns]=v; ps[t,ns]=s; pb[t,ns]=b
        m=nm
    if m[0]>=INF: return None,INF
    out=np.zeros(n,dtype=np.uint8); s=0
    for t in range(n-1,-1,-1): out[t]=pb[t,s]; s=int(ps[t,s])
    return out,int(m[0])
class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self,name='voice_fec_deframer',in_sig=[np.uint8],out_sig=[np.uint8]); self.buf=np.empty(0,dtype=np.uint8)
    def general_work(self,input_items,output_items):
        x=input_items[0]
        if len(x): self.buf=np.concatenate((self.buf,x.astype(np.uint8,copy=False))); self.consume(0,len(x))
        out=output_items[0]; made=0; total=848; plen=len(PAT)
        while len(self.buf)>=plen and made+42<=len(out):
            found=-1
            for i in range(len(self.buf)-plen+1):
                if np.count_nonzero(self.buf[i:i+plen]!=PAT)<=5: found=i; break
            if found<0: self.buf=self.buf[-(plen-1):]; break
            if found>0: self.buf=self.buf[found:]
            if len(self.buf)<total: break
            frame=self.buf[:total]; coded=frame[plen:plen+748].reshape(34,22).T.flatten()
            decbits,metric=vit(coded)
            if decbits is not None and metric<=80:
                body=np.packbits(decbits[:368],bitorder='big').tobytes(); seq=body[:2]; payload=body[2:42]; crc=body[42:46]
                if len(body)>=46 and zlib.crc32(seq+payload).to_bytes(4,'big')==crc:
                    out[made:made+42]=np.frombuffer(seq+payload,dtype=np.uint8); made+=42; self.buf=self.buf[total:]; continue
            self.buf=self.buf[1:]
        return made
