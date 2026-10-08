#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: DISCRAFT Pluto Digital Voice - FINAL
# Author: DISCRAFT
# Description: High-quality low-latency digital voice transceiver for ADALM-Pluto with live RF spectrum, QPSK constellation, FLL, audio waveform and power monitoring.
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import audio
from gnuradio import blocks
from gnuradio import channels
from gnuradio.filter import firdes
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import pluto_discraft_digital_voice_final_fec_rx as fec_rx  # embedded python block
import pluto_discraft_digital_voice_final_fec_tx as fec_tx  # embedded python block
import pluto_discraft_digital_voice_final_opus_dec as opus_dec  # embedded python block
import pluto_discraft_digital_voice_final_opus_enc as opus_enc  # embedded python block
import pluto_discraft_digital_voice_final_tx_limiter as tx_limiter  # embedded python block
import sip



class pluto_discraft_digital_voice_final(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "DISCRAFT Pluto Digital Voice - FINAL", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("DISCRAFT Pluto Digital Voice - FINAL")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "pluto_discraft_digital_voice_final")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.tx_freq = tx_freq = 433920000
        self.rx_freq = rx_freq = 433920000
        self.sim_freq_offset_hz = sim_freq_offset_hz = 0
        self.pluto_rate = pluto_rate = 1696000
        self.c0 = c0 = 299792458.0
        self.antenna_freq = antenna_freq = (tx_freq + rx_freq) / 2.0
        self.tx_monitor_gain = tx_monitor_gain = 0
        self.tx_attenuation = tx_attenuation = 10
        self.sym_rate = sym_rate = 21200
        self.sps = sps = 4
        self.sim_noise = sim_noise = 0.0
        self.sim_freq_offset = sim_freq_offset = sim_freq_offset_hz/pluto_rate
        self.sim_audio_freq = sim_audio_freq = 800
        self.sim_audio_amp = sim_audio_amp = 0.25
        self.samp_audio = samp_audio = 16000
        self.rx_volume = rx_volume = 1
        self.rx_gain = rx_gain = 38
        self.quarter_wave_cm = quarter_wave_cm = 100.0 * c0 / antenna_freq / 4.0
        self.qpsk_const = qpsk_const = digital.constellation_rect([0.70710678+0.70710678j, -0.70710678+0.70710678j, -0.70710678-0.70710678j, 0.70710678-0.70710678j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.ptt_enable = ptt_enable = 1
        self.mic_gain = mic_gain = 1
        self.half_wave_cm = half_wave_cm = 100.0 * c0 / antenna_freq / 2.0
        self.baseband_rate = baseband_rate = 84800

        ##################################################
        # Blocks
        ##################################################

        self._tx_monitor_gain_range = qtgui.Range(0, 1, 0.05, 0, 220)
        self._tx_monitor_gain_win = qtgui.RangeWidget(self._tx_monitor_gain_range, self.set_tx_monitor_gain, "TX monitor (sidetone)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_monitor_gain_win)
        self._sim_noise_range = qtgui.Range(0, 0.10, 0.001, 0.0, 220)
        self._sim_noise_win = qtgui.RangeWidget(self._sim_noise_range, self.set_sim_noise, "Simulation Noise", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sim_noise_win)
        self._rx_volume_range = qtgui.Range(0, 2, 0.05, 1, 200)
        self._rx_volume_win = qtgui.RangeWidget(self._rx_volume_range, self.set_rx_volume, "RX volume", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_volume_win)
        # Create the options list
        self._ptt_enable_options = [0, 1]
        # Create the labels list
        self._ptt_enable_labels = ['RX / Standby', 'TX / PTT']
        # Create the combo box
        # Create the radio buttons
        self._ptt_enable_group_box = Qt.QGroupBox("TX / PTT" + ": ")
        self._ptt_enable_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._ptt_enable_button_group = variable_chooser_button_group()
        self._ptt_enable_group_box.setLayout(self._ptt_enable_box)
        for i, _label in enumerate(self._ptt_enable_labels):
            radio_button = Qt.QRadioButton(_label)
            self._ptt_enable_box.addWidget(radio_button)
            self._ptt_enable_button_group.addButton(radio_button, i)
        self._ptt_enable_callback = lambda i: Qt.QMetaObject.invokeMethod(self._ptt_enable_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._ptt_enable_options.index(i)))
        self._ptt_enable_callback(self.ptt_enable)
        self._ptt_enable_button_group.buttonClicked[int].connect(
            lambda i: self.set_ptt_enable(self._ptt_enable_options[i]))
        self.top_layout.addWidget(self._ptt_enable_group_box)
        self._mic_gain_range = qtgui.Range(0.25, 3, 0.05, 1, 200)
        self._mic_gain_win = qtgui.RangeWidget(self._mic_gain_range, self.set_mic_gain, "Microphone gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._mic_gain_win)
        self.unpack_bits_tx = blocks.unpacked_to_packed_bb(8, gr.GR_MSB_FIRST)
        self.tx_to_pluto = filter.rational_resampler_ccc(
                interpolation=20,
                decimation=1,
                taps=[],
                fractional_bw=0.45)
        self.tx_ptt_gate = blocks.multiply_const_cc(ptt_enable)
        self.tx_power_db = blocks.nlog10_ff(10, 1, 0)
        self.tx_power_add = blocks.add_const_ff((1e-12))
        self.tx_monitor_block = blocks.multiply_const_ff(tx_monitor_gain)
        self.tx_mag = blocks.complex_to_mag_squared(1)
        self.tx_lp = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_audio,
                7000,
                500,
                window.WIN_HAMMING,
                6.76))
        self.tx_limiter = tx_limiter.blk()
        self.tx_hp = filter.fir_filter_fff(
            1,
            firdes.high_pass(
                1,
                samp_audio,
                100,
                100,
                window.WIN_HAMMING,
                6.76))
        self.tx_gain = blocks.multiply_const_ff(mic_gain)
        self._tx_freq_range = qtgui.Range(325000000, 3800000000, 1000, 433920000, 200)
        self._tx_freq_win = qtgui.RangeWidget(self._tx_freq_range, self.set_tx_freq, "TX frequency (Hz)", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_freq_win)
        self.tx_fft = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            baseband_rate, #bw
            'TX baseband', #name
            1,
            None # parent
        )
        self.tx_fft.set_update_time(0.10)
        self.tx_fft.set_y_axis((-140), 10)
        self.tx_fft.set_y_label('TX baseband spectrum', 'dB')
        self.tx_fft.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.tx_fft.enable_autoscale(False)
        self.tx_fft.enable_grid(True)
        self.tx_fft.set_fft_average(0.2)
        self.tx_fft.enable_axis_labels(True)
        self.tx_fft.enable_control_panel(True)
        self.tx_fft.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.tx_fft.set_line_label(i, "Data {0}".format(i))
            else:
                self.tx_fft.set_line_label(i, labels[i])
            self.tx_fft.set_line_width(i, widths[i])
            self.tx_fft.set_line_color(i, colors[i])
            self.tx_fft.set_line_alpha(i, alphas[i])

        self._tx_fft_win = sip.wrapinstance(self.tx_fft.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._tx_fft_win)
        self.tx_dc = filter.dc_blocker_ff(64, True)
        self.tx_audio_time = qtgui.time_sink_f(
            4000, #size
            samp_audio, #samp_rate
            'LIVE Microphone', #name
            1, #number of inputs
            None # parent
        )
        self.tx_audio_time.set_update_time(0.10)
        self.tx_audio_time.set_y_axis(-1, 1)

        self.tx_audio_time.set_y_label('Amplitude', "")

        self.tx_audio_time.enable_tags(False)
        self.tx_audio_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0, 0, 0, "")
        self.tx_audio_time.enable_autoscale(False)
        self.tx_audio_time.enable_grid(True)
        self.tx_audio_time.enable_axis_labels(True)
        self.tx_audio_time.enable_control_panel(False)
        self.tx_audio_time.enable_stem_plot(False)


        labels = ['LIVE Mic', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.tx_audio_time.set_line_label(i, "Data {0}".format(i))
            else:
                self.tx_audio_time.set_line_label(i, labels[i])
            self.tx_audio_time.set_line_width(i, widths[i])
            self.tx_audio_time.set_line_color(i, colors[i])
            self.tx_audio_time.set_line_style(i, styles[i])
            self.tx_audio_time.set_line_marker(i, markers[i])
            self.tx_audio_time.set_line_alpha(i, alphas[i])

        self._tx_audio_time_win = sip.wrapinstance(self.tx_audio_time.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._tx_audio_time_win)
        self._tx_attenuation_range = qtgui.Range(0, 60, 0.25, 10, 200)
        self._tx_attenuation_win = qtgui.RangeWidget(self._tx_attenuation_range, self.set_tx_attenuation, "TX attenuation (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_attenuation_win)
        self.sim_throttle = blocks.throttle(gr.sizeof_gr_complex*1, pluto_rate,True)
        self._sim_freq_offset_hz_range = qtgui.Range(-2500, 2500, 10, 0, 220)
        self._sim_freq_offset_hz_win = qtgui.RangeWidget(self._sim_freq_offset_hz_range, self.set_sim_freq_offset_hz, "Simulation Frequency Offset (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sim_freq_offset_hz_win)
        self.sim_channel = channels.channel_model(
            noise_voltage=sim_noise,
            frequency_offset=sim_freq_offset,
            epsilon=1.0,
            taps=[1.0+0j],
            noise_seed=42,
            block_tags=False)
        self._sim_audio_freq_range = qtgui.Range(200, 3000, 10, 800, 220)
        self._sim_audio_freq_win = qtgui.RangeWidget(self._sim_audio_freq_range, self.set_sim_audio_freq, "Simulation Audio Tone (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sim_audio_freq_win)
        self._sim_audio_amp_range = qtgui.Range(0.05, 0.70, 0.01, 0.25, 220)
        self._sim_audio_amp_win = qtgui.RangeWidget(self._sim_audio_amp_range, self.set_sim_audio_amp, "Simulation Audio Level", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sim_audio_amp_win)
        self.rx_volume_block = blocks.multiply_const_ff(rx_volume)
        self.rx_symbols_to_bits = blocks.packed_to_unpacked_bb(2, gr.GR_MSB_FIRST)
        self.rx_sym = digital.symbol_sync_cc(
            digital.TED_GARDNER,
            sps,
            0.03,
            1.0,
            1.0,
            1.5,
            1,
            qpsk_const,
            digital.IR_MMSE_8TAP,
            128,
            [])
        self.rx_rrc = filter.fir_filter_ccf(
            1,
            firdes.root_raised_cosine(
                1,
                baseband_rate,
                sym_rate,
                0.25,
                161))
        self.rx_power_db = blocks.nlog10_ff(10, 1, 0)
        self.rx_power_add = blocks.add_const_ff((1e-12))
        self.rx_mag = blocks.complex_to_mag_squared(1)
        self._rx_gain_range = qtgui.Range(0, 70, 0.5, 38, 200)
        self._rx_gain_win = qtgui.RangeWidget(self._rx_gain_range, self.set_rx_gain, "RX manual gain (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_gain_win)
        self._rx_freq_range = qtgui.Range(325000000, 3800000000, 1000, 433920000, 200)
        self._rx_freq_win = qtgui.RangeWidget(self._rx_freq_range, self.set_rx_freq, "RX frequency (Hz)", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_freq_win)
        self.rx_fll = digital.fll_band_edge_cc(sps, 0.25, 65, 0.02)
        self.rx_fft = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            baseband_rate, #bw
            'RX filtered', #name
            1,
            None # parent
        )
        self.rx_fft.set_update_time(0.10)
        self.rx_fft.set_y_axis((-140), 10)
        self.rx_fft.set_y_label('RX filtered spectrum', 'dB')
        self.rx_fft.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.rx_fft.enable_autoscale(False)
        self.rx_fft.enable_grid(True)
        self.rx_fft.set_fft_average(0.2)
        self.rx_fft.enable_axis_labels(True)
        self.rx_fft.enable_control_panel(True)
        self.rx_fft.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.rx_fft.set_line_label(i, "Data {0}".format(i))
            else:
                self.rx_fft.set_line_label(i, labels[i])
            self.rx_fft.set_line_width(i, widths[i])
            self.rx_fft.set_line_color(i, colors[i])
            self.rx_fft.set_line_alpha(i, alphas[i])

        self._rx_fft_win = sip.wrapinstance(self.rx_fft.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._rx_fft_win)
        self.rx_diff = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.rx_decim = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=20,
                taps=[],
                fractional_bw=0.45)
        self.rx_costas = digital.costas_loop_cc(0.01, 4, False)
        self.rx_const_sink = qtgui.const_sink_c(
            2048, #size
            "RX QPSK Constellation", #name
            1, #number of inputs
            None # parent
        )
        self.rx_const_sink.set_update_time(0.10)
        self.rx_const_sink.set_y_axis((-1.5), 1.5)
        self.rx_const_sink.set_x_axis((-1.5), 1.5)
        self.rx_const_sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0, 0, "")
        self.rx_const_sink.enable_autoscale(False)
        self.rx_const_sink.enable_grid(True)
        self.rx_const_sink.enable_axis_labels(True)


        labels = ['Symbols', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, -1, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.rx_const_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.rx_const_sink.set_line_label(i, labels[i])
            self.rx_const_sink.set_line_width(i, widths[i])
            self.rx_const_sink.set_line_color(i, colors[i])
            self.rx_const_sink.set_line_style(i, styles[i])
            self.rx_const_sink.set_line_marker(i, markers[i])
            self.rx_const_sink.set_line_alpha(i, alphas[i])

        self._rx_const_sink_win = sip.wrapinstance(self.rx_const_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._rx_const_sink_win)
        self.rx_const_dec = digital.constellation_decoder_cb(qpsk_const)
        self.rx_channel = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                baseband_rate,
                12500,
                2500,
                window.WIN_HAMMING,
                6.76))
        self.rx_audio_time = qtgui.time_sink_f(
            4000, #size
            samp_audio, #samp_rate
            "RX Audio", #name
            1, #number of inputs
            None # parent
        )
        self.rx_audio_time.set_update_time(0.10)
        self.rx_audio_time.set_y_axis(-1, 1)

        self.rx_audio_time.set_y_label('Amplitude', "")

        self.rx_audio_time.enable_tags(False)
        self.rx_audio_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0, 0, 0, "")
        self.rx_audio_time.enable_autoscale(False)
        self.rx_audio_time.enable_grid(True)
        self.rx_audio_time.enable_axis_labels(True)
        self.rx_audio_time.enable_control_panel(False)
        self.rx_audio_time.enable_stem_plot(False)


        labels = ['RX', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['red', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.rx_audio_time.set_line_label(i, "Data {0}".format(i))
            else:
                self.rx_audio_time.set_line_label(i, labels[i])
            self.rx_audio_time.set_line_width(i, widths[i])
            self.rx_audio_time.set_line_color(i, colors[i])
            self.rx_audio_time.set_line_style(i, styles[i])
            self.rx_audio_time.set_line_marker(i, markers[i])
            self.rx_audio_time.set_line_alpha(i, alphas[i])

        self._rx_audio_time_win = sip.wrapinstance(self.rx_audio_time.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._rx_audio_time_win)
        self.rx_audio_lp = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_audio,
                7000,
                500,
                window.WIN_HAMMING,
                6.76))
        self.qpsk_symbols_tx = blocks.packed_to_unpacked_bb(2, gr.GR_MSB_FIRST)
        self.qpsk_mod_tx = digital.generic_mod(
            constellation=qpsk_const,
            differential=True,
            samples_per_symbol=4,
            pre_diff_code=True,
            excess_bw=0.25,
            verbose=False,
            log=False,
            truncate=False)
        self.power_sink = qtgui.number_sink(
            gr.sizeof_float,
            0.1,
            qtgui.NUM_GRAPH_VERT,
            2,
            None # parent
        )
        self.power_sink.set_update_time(0.20)
        self.power_sink.set_title("Baseband Power")

        labels = ['TX', 'RX', '', '', '',
            '', '', '', '', '']
        units = ['dBFS', 'dBFS', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(2):
            self.power_sink.set_min(i, -120)
            self.power_sink.set_max(i, 5)
            self.power_sink.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.power_sink.set_label(i, "Data {0}".format(i))
            else:
                self.power_sink.set_label(i, labels[i])
            self.power_sink.set_unit(i, units[i])
            self.power_sink.set_factor(i, factor[i])

        self.power_sink.enable_autoscale(False)
        self._power_sink_win = sip.wrapinstance(self.power_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._power_sink_win)
        self.opus_enc = opus_enc.blk()
        self.opus_dec = opus_dec.blk()
        self.fll_time = qtgui.time_sink_f(
            2000, #size
            baseband_rate, #samp_rate
            "FLL estimate", #name
            1, #number of inputs
            None # parent
        )
        self.fll_time.set_update_time(0.10)
        self.fll_time.set_y_axis(-0.2, 0.2)

        self.fll_time.set_y_label('Frequency estimate', 'normalized')

        self.fll_time.enable_tags(False)
        self.fll_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0, 0, 0, "")
        self.fll_time.enable_autoscale(True)
        self.fll_time.enable_grid(True)
        self.fll_time.enable_axis_labels(True)
        self.fll_time.enable_control_panel(False)
        self.fll_time.enable_stem_plot(False)


        labels = ['FLL', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['green', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.fll_time.set_line_label(i, "Data {0}".format(i))
            else:
                self.fll_time.set_line_label(i, labels[i])
            self.fll_time.set_line_width(i, widths[i])
            self.fll_time.set_line_color(i, colors[i])
            self.fll_time.set_line_style(i, styles[i])
            self.fll_time.set_line_marker(i, markers[i])
            self.fll_time.set_line_alpha(i, alphas[i])

        self._fll_time_win = sip.wrapinstance(self.fll_time.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._fll_time_win)
        self.fec_tx = fec_tx.blk()
        self.fec_rx = fec_rx.blk()
        self.audio_src = audio.source(samp_audio, '', True)
        self.audio_sink = audio.sink(samp_audio, '', True)
        self.audio_mix = blocks.add_vff(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.audio_mix, 0), (self.audio_sink, 0))
        self.connect((self.audio_src, 0), (self.tx_audio_time, 0))
        self.connect((self.audio_src, 0), (self.tx_dc, 0))
        self.connect((self.fec_rx, 0), (self.opus_dec, 0))
        self.connect((self.fec_tx, 0), (self.unpack_bits_tx, 0))
        self.connect((self.opus_dec, 0), (self.rx_audio_lp, 0))
        self.connect((self.opus_enc, 0), (self.fec_tx, 0))
        self.connect((self.qpsk_mod_tx, 0), (self.tx_fft, 0))
        self.connect((self.qpsk_mod_tx, 0), (self.tx_ptt_gate, 0))
        self.connect((self.qpsk_symbols_tx, 0), (self.qpsk_mod_tx, 0))
        self.connect((self.rx_audio_lp, 0), (self.rx_volume_block, 0))
        self.connect((self.rx_channel, 0), (self.rx_fft, 0))
        self.connect((self.rx_channel, 0), (self.rx_fll, 0))
        self.connect((self.rx_channel, 0), (self.rx_mag, 0))
        self.connect((self.rx_const_dec, 0), (self.rx_diff, 0))
        self.connect((self.rx_costas, 0), (self.rx_const_dec, 0))
        self.connect((self.rx_costas, 0), (self.rx_const_sink, 0))
        self.connect((self.rx_decim, 0), (self.rx_channel, 0))
        self.connect((self.rx_diff, 0), (self.rx_symbols_to_bits, 0))
        self.connect((self.rx_fll, 1), (self.fll_time, 0))
        self.connect((self.rx_fll, 0), (self.rx_rrc, 0))
        self.connect((self.rx_mag, 0), (self.rx_power_add, 0))
        self.connect((self.rx_power_add, 0), (self.rx_power_db, 0))
        self.connect((self.rx_power_db, 0), (self.power_sink, 1))
        self.connect((self.rx_rrc, 0), (self.rx_sym, 0))
        self.connect((self.rx_sym, 0), (self.rx_costas, 0))
        self.connect((self.rx_symbols_to_bits, 0), (self.fec_rx, 0))
        self.connect((self.rx_volume_block, 0), (self.audio_mix, 1))
        self.connect((self.rx_volume_block, 0), (self.rx_audio_time, 0))
        self.connect((self.sim_channel, 0), (self.rx_decim, 0))
        self.connect((self.sim_throttle, 0), (self.sim_channel, 0))
        self.connect((self.tx_dc, 0), (self.tx_hp, 0))
        self.connect((self.tx_gain, 0), (self.tx_limiter, 0))
        self.connect((self.tx_hp, 0), (self.tx_lp, 0))
        self.connect((self.tx_limiter, 0), (self.opus_enc, 0))
        self.connect((self.tx_limiter, 0), (self.tx_monitor_block, 0))
        self.connect((self.tx_lp, 0), (self.tx_gain, 0))
        self.connect((self.tx_mag, 0), (self.tx_power_add, 0))
        self.connect((self.tx_monitor_block, 0), (self.audio_mix, 0))
        self.connect((self.tx_power_add, 0), (self.tx_power_db, 0))
        self.connect((self.tx_power_db, 0), (self.power_sink, 0))
        self.connect((self.tx_ptt_gate, 0), (self.tx_mag, 0))
        self.connect((self.tx_ptt_gate, 0), (self.tx_to_pluto, 0))
        self.connect((self.tx_to_pluto, 0), (self.sim_throttle, 0))
        self.connect((self.unpack_bits_tx, 0), (self.qpsk_symbols_tx, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "pluto_discraft_digital_voice_final")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tx_freq(self):
        return self.tx_freq

    def set_tx_freq(self, tx_freq):
        self.tx_freq = tx_freq
        self.set_antenna_freq((self.tx_freq + self.rx_freq) / 2.0)

    def get_rx_freq(self):
        return self.rx_freq

    def set_rx_freq(self, rx_freq):
        self.rx_freq = rx_freq
        self.set_antenna_freq((self.tx_freq + self.rx_freq) / 2.0)

    def get_sim_freq_offset_hz(self):
        return self.sim_freq_offset_hz

    def set_sim_freq_offset_hz(self, sim_freq_offset_hz):
        self.sim_freq_offset_hz = sim_freq_offset_hz
        self.set_sim_freq_offset(self.sim_freq_offset_hz/self.pluto_rate)

    def get_pluto_rate(self):
        return self.pluto_rate

    def set_pluto_rate(self, pluto_rate):
        self.pluto_rate = pluto_rate
        self.set_sim_freq_offset(self.sim_freq_offset_hz/self.pluto_rate)
        self.sim_throttle.set_sample_rate(self.pluto_rate)

    def get_c0(self):
        return self.c0

    def set_c0(self, c0):
        self.c0 = c0
        self.set_quarter_wave_cm(100.0 * self.c0 / self.antenna_freq / 4.0)
        self.set_half_wave_cm(100.0 * self.c0 / self.antenna_freq / 2.0)

    def get_antenna_freq(self):
        return self.antenna_freq

    def set_antenna_freq(self, antenna_freq):
        self.antenna_freq = antenna_freq
        self.set_quarter_wave_cm(100.0 * self.c0 / self.antenna_freq / 4.0)
        self.set_half_wave_cm(100.0 * self.c0 / self.antenna_freq / 2.0)

    def get_tx_monitor_gain(self):
        return self.tx_monitor_gain

    def set_tx_monitor_gain(self, tx_monitor_gain):
        self.tx_monitor_gain = tx_monitor_gain
        self.tx_monitor_block.set_k(self.tx_monitor_gain)

    def get_tx_attenuation(self):
        return self.tx_attenuation

    def set_tx_attenuation(self, tx_attenuation):
        self.tx_attenuation = tx_attenuation

    def get_sym_rate(self):
        return self.sym_rate

    def set_sym_rate(self, sym_rate):
        self.sym_rate = sym_rate
        self.rx_rrc.set_taps(firdes.root_raised_cosine(1, self.baseband_rate, self.sym_rate, 0.25, 161))

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.rx_sym.set_sps(self.sps)

    def get_sim_noise(self):
        return self.sim_noise

    def set_sim_noise(self, sim_noise):
        self.sim_noise = sim_noise
        self.sim_channel.set_noise_voltage(self.sim_noise)

    def get_sim_freq_offset(self):
        return self.sim_freq_offset

    def set_sim_freq_offset(self, sim_freq_offset):
        self.sim_freq_offset = sim_freq_offset
        self.sim_channel.set_frequency_offset(self.sim_freq_offset)

    def get_sim_audio_freq(self):
        return self.sim_audio_freq

    def set_sim_audio_freq(self, sim_audio_freq):
        self.sim_audio_freq = sim_audio_freq

    def get_sim_audio_amp(self):
        return self.sim_audio_amp

    def set_sim_audio_amp(self, sim_audio_amp):
        self.sim_audio_amp = sim_audio_amp

    def get_samp_audio(self):
        return self.samp_audio

    def set_samp_audio(self, samp_audio):
        self.samp_audio = samp_audio
        self.tx_hp.set_taps(firdes.high_pass(1, self.samp_audio, 100, 100, window.WIN_HAMMING, 6.76))
        self.tx_lp.set_taps(firdes.low_pass(1, self.samp_audio, 7000, 500, window.WIN_HAMMING, 6.76))
        self.rx_audio_lp.set_taps(firdes.low_pass(1, self.samp_audio, 7000, 500, window.WIN_HAMMING, 6.76))
        self.tx_audio_time.set_samp_rate(self.samp_audio)
        self.rx_audio_time.set_samp_rate(self.samp_audio)

    def get_rx_volume(self):
        return self.rx_volume

    def set_rx_volume(self, rx_volume):
        self.rx_volume = rx_volume
        self.rx_volume_block.set_k(self.rx_volume)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain

    def get_quarter_wave_cm(self):
        return self.quarter_wave_cm

    def set_quarter_wave_cm(self, quarter_wave_cm):
        self.quarter_wave_cm = quarter_wave_cm

    def get_qpsk_const(self):
        return self.qpsk_const

    def set_qpsk_const(self, qpsk_const):
        self.qpsk_const = qpsk_const
        self.rx_const_dec.set_constellation(self.qpsk_const)

    def get_ptt_enable(self):
        return self.ptt_enable

    def set_ptt_enable(self, ptt_enable):
        self.ptt_enable = ptt_enable
        self._ptt_enable_callback(self.ptt_enable)
        self.tx_ptt_gate.set_k(self.ptt_enable)

    def get_mic_gain(self):
        return self.mic_gain

    def set_mic_gain(self, mic_gain):
        self.mic_gain = mic_gain
        self.tx_gain.set_k(self.mic_gain)

    def get_half_wave_cm(self):
        return self.half_wave_cm

    def set_half_wave_cm(self, half_wave_cm):
        self.half_wave_cm = half_wave_cm

    def get_baseband_rate(self):
        return self.baseband_rate

    def set_baseband_rate(self, baseband_rate):
        self.baseband_rate = baseband_rate
        self.rx_channel.set_taps(firdes.low_pass(1, self.baseband_rate, 12500, 2500, window.WIN_HAMMING, 6.76))
        self.rx_rrc.set_taps(firdes.root_raised_cosine(1, self.baseband_rate, self.sym_rate, 0.25, 161))
        self.tx_fft.set_frequency_range(0, self.baseband_rate)
        self.rx_fft.set_frequency_range(0, self.baseband_rate)
        self.fll_time.set_samp_rate(self.baseband_rate)




def main(top_block_cls=pluto_discraft_digital_voice_final, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
