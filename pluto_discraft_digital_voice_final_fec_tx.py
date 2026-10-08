import numpy as np
import zlib
from gnuradio import gr
SYNC=0x1ACFFC1D
G0=0o171; G1=0o133
PRE_SYMS=np.array([0,1,2,3]*8,dtype=np.uint8)
PRE_BITS=np.empty(64,dtype=np.uint8)
PRE_BITS[0::2]=PRE_SYMS>>1; PRE_BITS[1::2]=PRE_SYMS&1
SYNC_BITS=np.array([(SYNC>>i)&1 for i in range(31,-1,-1)],dtype=np.uint8)
def bbits(b): return np.unpackbits(np.frombuffer(b,dtype=np.uint8),bitorder='big').astype(np.uint8)
def conv(x):
    s=0; o=[]
    for bit in x:
        r=((s<<1)|int(bit))&0x7f; o.extend([(r&G0).bit_count()&1,(r&G1).bit_count()&1]); s=r&0x3f
    for _ in range(6):
        r=(s<<1)&0x7f; o.extend([(r&G0).bit_count()&1,(r&G1).bit_count()&1]); s=r&0x3f
    return np.asarray(o,dtype=np.uint8)
class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self,name='voice_fec_framer',in_sig=[np.uint8],out_sig=[np.uint8]); self.buf=bytearray(); self.seq=0
    def general_work(self,input_items,output_items):
        x=input_items[0]
        if len(x): self.buf.extend(bytes(x.tolist())); self.consume(0,len(x))
        out=output_items[0]; frame_bits=848
        n=min(len(self.buf)//40,len(out)//frame_bits)
        if n<=0: return 0
        p=0
        for _ in range(n):
            payload=bytes(self.buf[:40]); del self.buf[:40]
            seq=(self.seq&0xffff).to_bytes(2,'big')
            crc=zlib.crc32(seq+payload).to_bytes(4,'big')
            c=conv(bbits(seq+payload+crc)); c=c.reshape(22,34).T.flatten()
            out[p:p+848]=np.concatenate((PRE_BITS,SYNC_BITS,c,np.zeros(4,dtype=np.uint8)))
            p+=848; self.seq=(self.seq+1)&0xffff
        return p
