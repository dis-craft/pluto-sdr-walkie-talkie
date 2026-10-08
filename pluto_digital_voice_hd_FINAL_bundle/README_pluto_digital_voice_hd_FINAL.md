# Pluto Digital Voice HD — final GNU Radio Companion build

This build is the corrected dashboard version of the ADALM-Pluto digital voice walkie-talkie flowgraph.

## Architecture

TX: 16 kHz mono audio → DC blocker → 100 Hz HPF → 7 kHz LPF → speech compression → soft limiter → Opus 16 kbps CBR, 20 ms → sequence + CRC32 → K=7 rate-1/2 convolutional FEC → 22×34 block interleaver → 32-symbol preamble + 16-symbol sync → differential Gray QPSK → RRC α=0.25 → PTT → 8× interpolation → Pluto TX.

RX: Pluto RX → 8× decimation → 14.5 kHz software channel filter → FLL band-edge frequency recovery → matched RRC / Gardner symbol timing → QPSK Costas carrier recovery → constellation decode → differential decode → symbol-to-bit expansion → preamble/sync search → inverse interleaving → Viterbi → CRC check → Opus decoder/PLC → 7 kHz audio LPF → speaker.

## Radio timing

- Opus: 16 kHz mono, 16 kbps CBR, 20 ms frame, 40-byte payload.
- 32-symbol preamble + 16-symbol sync + 374 coded QPSK symbols + 2 pad symbols = 424 symbols/frame.
- Symbol rate: 21.2 ksym/s.
- Modem baseband rate: 84.8 kS/s (4 samples/symbol).
- Pluto stream rate: 678.4 kS/s (8× interpolation/decimation around the modem baseband).
- QPSK RRC excess bandwidth: 0.25.
- Approximate occupied waveform class: 26.5 kHz.
- Pluto hardware RF bandwidth: 200 kHz minimum; narrow occupancy is created by baseband shaping/filtering.

## Live dashboard

The Qt GUI is organized into five tabs:

1. **Controls** — TX/RX frequency, TX attenuation, RX manual gain, microphone gain, speaker volume and half-duplex PTT.
2. **RF Spectrum** — live TX baseband spectrum, RX filtered spectrum and relative TX/RX baseband power monitor.
3. **Modem** — RX QPSK constellation and FLL frequency estimate.
4. **Audio** — live TX microphone waveform and decoded RX audio waveform.
5. **System Notes** — profile and RF/test notes.

## Dependencies

Ubuntu/Debian example:

```bash
sudo apt update
sudo apt install gnuradio gr-iio libopus0 libopus-dev python3-pip
python3 -m pip install --user opuslib
```

On a distribution enforcing an externally managed Python environment, use an appropriate virtual environment or distro package for `opuslib`.

## First test

Use two Plutos or separate TX/RX instances. For the first RF test, connect TX to RX through a **suitable RF attenuator chain**. Never connect a Pluto TX port directly to a Pluto RX port.

Start RX manual gain around 35–40 dB. Keep TX attenuation conservative. Set both frequencies identically. Put the transmitter in **TX / PTT** only while speaking.

## RF / regulatory note

The default frequency is 433.92 MHz as a development value only. Actual permitted frequencies, power, duty cycle, occupied bandwidth and amplification depend on local rules and authorization. Keep early tests cabled/attenuated or under the appropriate experimental authorization.
