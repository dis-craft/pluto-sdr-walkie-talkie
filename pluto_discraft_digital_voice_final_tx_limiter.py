import numpy as np
from gnuradio import gr

class blk(gr.sync_block):
    """Low-latency soft limiter for speech."""
    def __init__(self):
        gr.sync_block.__init__(self,
            name="speech_soft_limiter",
            in_sig=[np.float32],
            out_sig=[np.float32])
        self.drive = 1.8
        self.norm = np.tanh(self.drive)

    def work(self, input_items, output_items):
        x = input_items[0]
        y = output_items[0]
        y[:] = np.tanh(self.drive * x) / self.norm
        return len(y)
