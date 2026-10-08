import ctypes
import ctypes.util
import numpy as np
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name='opus_decoder_16k',
            in_sig=[np.uint8],
            out_sig=[np.float32]
        )
        libname = ctypes.util.find_library('opus') or 'libopus.so.0'
        self.lib = ctypes.CDLL(libname)
        self.lib.opus_decoder_create.argtypes = [
            ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int)
        ]
        self.lib.opus_decoder_create.restype = ctypes.c_void_p
        self.lib.opus_decode.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_int,
            ctypes.c_int
        ]
        self.lib.opus_decode.restype = ctypes.c_int
        self.lib.opus_decoder_destroy.argtypes = [ctypes.c_void_p]
        err = ctypes.c_int()
        self.dec = self.lib.opus_decoder_create(
            16000, 1, ctypes.byref(err)
        )
        if not self.dec or err.value != 0:
            raise RuntimeError(
                'libopus decoder creation failed (error %d)' % err.value
            )
        self.frame = 320
        self.packet = 42
        self.buf = bytearray()
        self.audio_q = np.empty(0, dtype=np.float32)
        self.expected = None

    def stop(self):
        if getattr(self, 'dec', None):
            self.lib.opus_decoder_destroy(self.dec)
            self.dec = None
        return super().stop()

    def decode_one(self, pkt):
        pcm = (ctypes.c_int16 * self.frame)()
        if pkt is None:
            n = self.lib.opus_decode(
                self.dec, None, 0, pcm, self.frame, 0
            )
        else:
            raw = (ctypes.c_ubyte * len(pkt)).from_buffer_copy(pkt)
            n = self.lib.opus_decode(
                self.dec, raw, len(pkt), pcm, self.frame, 0
            )
        if n < 0:
            raise RuntimeError('libopus decode failed (%d)' % n)
        return (
            np.ctypeslib.as_array(pcm)[:n]
            .astype(np.float32) / 32767.0
        )

    def push(self, raw):
        seq = int.from_bytes(raw[:2], 'big')
        pkt = bytes(raw[2:])
        if self.expected is None:
            self.expected = seq
        gap = (seq - self.expected) & 0xffff
        if gap > 32768:
            return
        for _ in range(gap):
            self.audio_q = np.concatenate(
                (self.audio_q, self.decode_one(None))
            )
            self.expected = (self.expected + 1) & 0xffff
        self.audio_q = np.concatenate(
            (self.audio_q, self.decode_one(pkt))
        )
        self.expected = (seq + 1) & 0xffff

    def general_work(self, input_items, output_items):
        x = input_items[0]
        if len(x):
            self.buf.extend(bytes(x.tolist()))
            self.consume(0, len(x))
        while len(self.buf) >= self.packet:
            raw = bytes(self.buf[:self.packet])
            del self.buf[:self.packet]
            try:
                self.push(raw)
            except Exception:
                pass
        out = output_items[0]
        n = min(len(out), len(self.audio_q))
        if n:
            out[:n] = self.audio_q[:n]
            self.audio_q = self.audio_q[n:]
        return n