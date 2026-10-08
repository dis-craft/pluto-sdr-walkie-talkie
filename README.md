# Pluto SDR Walkie-Talkie

A GNU Radio Companion digital voice transceiver for ADALM-Pluto.

## One canonical flowgraph

Open only:

`pluto_digital_voice_hd.grc`

There are no separate TX/RX GRC files in the project. The same flowgraph supports:

1. **Software simulation (default)** — runs with no Pluto connected.
2. **Pluto hardware mode** — the Pluto TX and RX blocks are retained in the same graph for later RF testing.

## Default: hardware-free simulation

The graph starts in simulation mode so the dashboard and complete DSP chain can be tested on an ordinary Ubuntu PC.

```text
800 Hz test audio
    -> DC block / HPF / LPF / level / limiter
    -> Opus 16 kbps CBR, 20 ms
    -> CRC32 + K=7 rate-1/2 FEC + interleaving
    -> differential QPSK + RRC
    -> 8x interpolation to 678.4 kS/s
    -> real-time throttle
    -> AWGN + carrier-offset channel model
    -> 8x decimation to 84.8 kS/s
    -> FLL + timing recovery + Costas
    -> QPSK decode
    -> frame sync + Viterbi + CRC
    -> Opus decode / PLC
    -> RX audio + visualizations
```

The following controls are available for simulation:

- Simulation Audio Tone
- Simulation Audio Level
- Simulation Noise
- Simulation Frequency Offset

Start with noise = 0 and frequency offset = 0. Then introduce offset/noise and watch the RF spectrum, QPSK constellation and FLL estimate.

The microphone Audio Source and speaker Audio Sink are retained in the graph but disabled in the no-hardware simulation path.

## Dashboard / visualization

The GRC contains live visualization blocks for:

- TX baseband spectrum
- RX channel spectrum
- TX/RX power monitor
- QPSK constellation after carrier/timing recovery
- FLL frequency estimate
- TX microphone/test waveform
- RX audio waveform

These are ordinary GNU Radio QT GUI sinks, so the flowgraph can be used as a modem/RF troubleshooting dashboard.

## Digital voice profile

### Audio

- 16 kHz mono
- 100 Hz high-pass
- 7 kHz low-pass
- gentle compressor
- soft limiter
- Opus 16 kbps CBR
- 20 ms frames / 40-byte Opus payload

### Framing and protection

- 16-bit sequence number
- CRC32
- K=7, rate-1/2 convolutional FEC
- 22 x 34 block interleaver
- deterministic preamble + sync word
- Opus packet-loss concealment on RX

### Modem

- differential QPSK
- 4 samples/symbol at modem baseband
- RRC excess bandwidth 0.25
- 21.2 ksym/s
- 84.8 kS/s modem baseband
- 678.4 kS/s Pluto stream rate
- Pluto hardware RF bandwidth set to 200 kHz

## Dependencies

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install gnuradio gr-iio libopus0
```

The Opus encoder/decoder in the flowgraph calls the system `libopus.so.0` directly, so the Python `opuslib` package is not required.

The software simulation additionally uses GNU Radio's `analog`, `channels`, `blocks`, `digital`, `filter` and `QT GUI` modules.

## Run the simulation

From the repository root:

```bash
gnuradio-companion ./pluto_digital_voice_hd.grc
```

Press Run/Play.

No ADALM-Pluto is required in the default simulation mode.

## Later: use both Pluto TX and RX

The same file already contains:

- PlutoSDR Sink (TX)
- PlutoSDR Source (RX)

They are deliberately disabled by default so the project can be executed without hardware.

For a first hardware test, use a properly attenuated cabled RF path. Do not connect a Pluto TX directly into a Pluto RX. After the hardware path is verified, the TX/RX frequency, gain and attenuation controls can be adjusted within your legal/authorized operating limits.

## Important RF note

The example default frequency is 433.92 MHz for development. Use only frequencies, occupied bandwidths, output powers, duty cycles and external RF amplification that are permitted for your location and authorization. For initial modem development, a cabled/attenuated test is preferable to uncontrolled OTA transmission.
