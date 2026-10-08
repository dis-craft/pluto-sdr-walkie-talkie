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
    -> 8x interpolation to 1.696 MSPS (Pluto host rate)
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
- 1.696 MSPS (Pluto host rate) Pluto stream rate
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


## RF / antenna design

The flowgraph is designed around the actual ADALM-PLUTO architecture: AD9363, 1 TX + 1 RX RF channel, direct-conversion RF, 12-bit ADC/DAC, programmable digital interpolation/decimation and analog filtering. The Pluto covers roughly 325 MHz–3.8 GHz, supports 200 kHz–20 MHz RF channel bandwidth and host sample rates up to 61.44 MSPS. citeturn0search1turn0search2

For a range-focused portable build, the RF chain matters as much as the DSP:

- Prefer a properly tuned external UHF antenna over the stock antenna when operating around 433 MHz. The Pluto board's RF front-end is optimized around 2.4 GHz, so a purpose-built antenna and matching network are important away from that region. citeturn0search3
- At 433 MHz, free-space quarter-wave is approximately **17.3 cm** and half-wave is approximately **34.6 cm total**. These are starting dimensions, not final cut lengths; connector geometry, ground plane and velocity factor change the tuned length.
- For a portable single-antenna half-duplex radio, use an external RF T/R switch so TX and RX share one tuned antenna. Do not hard-wire Pluto TX to Pluto RX or connect TX directly to RX.
- For initial RF validation, use a cabled path with adequate attenuation and a spectrum analyzer/power meter before attempting OTA operation.
- The Pluto's nominal TX output is only on the order of several dBm (ADI lists 7 dBm typical in its product highlight), so long range cannot be obtained by DSP alone. Antenna efficiency, feed loss, receiver sensitivity, legal EIRP, and—where authorized—an appropriate external PA/LNA determine the practical link budget. citeturn0search37turn0search10

### Modem strategy

The current modem deliberately keeps the robust, inspectable QPSK/FEC architecture rather than chasing maximum raw bitrate. For a real walkie-talkie, the next optimization target is **link robustness and audio quality at the lowest practical occupied bandwidth**, not simply increasing RF sample rate.

The design should be evaluated with BER/PER versus SNR, carrier offset, timing offset and multipath. Once the clean loopback is stable, add an automated modem test mode so every DSP change can be regression-tested before hardware OTA testing.

### Important distinction

A higher Pluto sample rate does **not** itself increase RF range. It gives the AD9363 more processing/filtering headroom. Range is primarily a link-budget problem: TX power/EIRP, antenna gain/efficiency, path loss, receiver noise figure and required Eb/N0.
