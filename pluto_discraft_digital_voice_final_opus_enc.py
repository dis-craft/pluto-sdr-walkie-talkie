import ctypes
import ctypes.util
import numpy as np
from gnuradio import gr

OPUS_APPLICATION_VOIP = 2048
OPUS_SET_BITRATE_REQUEST = 4002
OPUS_SET_VBR_REQUEST = 4006
OPUS_SET_COMPLEXITY_REQUEST = 4010

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name='opus_cbr_encoder_16k',
            in_sig=[np.float32],
            out_sig=[np.uint8]
        )
        libname = ctypes.util.find_library('opus') or 'libopus.so.0'
        self.lib = ctypes.CDLL(libname)
        self.lib.opus_encoder_create.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int)
        ]
        self.lib.opus_encoder_create.restype = ctypes.c_void_p
        self.lib.opus_encoder_ctl.restype = ctypes.c_int
        self.lib.opus_encode.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int
        ]
        self.lib.opus_encode.restype = ctypes.c_int
        self.lib.opus_encoder_destroy.argtypes = [ctypes.c_void_p]
        err = ctypes.c_int()
        self.enc = self.lib.opus_encoder_create(
            16000, 1, OPUS_APPLICATION_VOIP, ctypes.byref(err)
        )
        if not self.enc or err.value != 0:
            raise RuntimeError(
                'libopus encoder creation failed (error %d)' % err.value
            )
        for req, val in (
            (OPUS_SET_BITRATE_REQUEST, 16000),
            (OPUS_SET_VBR_REQUEST, 0),
            (OPUS_SET_COMPLEXITY_REQUEST, 10)
        ):
            rc = self.lib.opus_encoder_ctl(
                self.enc, ctypes.c_int(req), ctypes.c_int(val)
            )
            if rc != 0:
                raise RuntimeError(
                    'libopus encoder control request %d failed' % req
                )
        self.frame = 320
        self.packet_bytes = 40
        self.buf = np.empty(0, dtype=np.float32)

    def stop(self):
        if getattr(self, 'enc', None):
            self.lib.opus_encoder_destroy(self.enc)
            self.enc = None
        return super().stop()

    def general_work(self, input_items, output_items):
        x = input_items[0]
        if len(x):
            self.buf = np.concatenate(
                (self.buf, x.astype(np.float32, copy=False))
            )
            self.consume(0, len(x))
        out = output_items[0]
        n = min(len(self.buf) // self.frame,
                len(out) // self.packet_bytes)
        if n <= 0:
            return 0
        p = 0
        for i in range(n):
            pcm = np.clip(
                self.buf[i*self.frame:(i+1)*self.frame],
                -1.0, 1.0
            )
            pcm16 = (pcm * 32767.0).astype(np.int16)
            obuf = (ctypes.c_ubyte * 4000)()
            nb = self.lib.opus_encode(
                self.enc,
                pcm16.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                self.frame,
                obuf,
                4000
            )
            if nb != self.packet_bytes:
                raise RuntimeError(
                    'libopus returned %d bytes; expected 40 for 16 kbps CBR/20 ms'
                    % nb
                )
            out[p:p+self.packet_bytes] = np.frombuffer(
                bytes(obuf[:self.packet_bytes]), dtype=np.uint8
            )
            p += self.packet_bytes
        self.buf = self.buf[n*self.frame:]
        return p