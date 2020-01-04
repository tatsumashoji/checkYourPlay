#プロット関係のライブラリ
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import sys
import math

#音声関係のライブラリ
import pyaudio
import struct
import librosa

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.plotting import figure
import requests
from math import radians
from pytz import timezone

class PlotWindow:
    def __init__(self):
        #マイクインプット設定
        self.CHUNK=1024            #1度に読み取る音声のデータ幅
        self.RATE=16000             #サンプリング周波数
        self.update_seconds=50      #更新時間[ms]
        self.audio=pyaudio.PyAudio()
        self.stream=self.audio.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=self.RATE,
                                    input=True,
                                    frames_per_buffer=self.CHUNK)

        #音声データの格納場所(プロットデータ)
        self.data=np.zeros(self.CHUNK)
        self.axis = list(range(12))
#        self.axis = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"] #list(range(12))

        #データソースの作成
        self.color = ["blue"]
        self.source = ColumnDataSource(dict(x=self.axis, y=[0]*12, color=self.color))
        self.new_data = dict(x=list(range(12)), y=[0]*12, color=self.color)

        #グラフの作成
        self.fig = figure(
                    x_axis_label="Chord",
                    y_axis_label="Energy",
                    plot_width=800,
                    plot_height=600)
        self.fig.title.text = "ChromagramAnalyzer"
        self.fig.line(source=self.source, x="x", y="y", line_width=2, color='color', id="first", name="first")

        #アップデート時間設定
        self.timer=QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_seconds)    #10msごとにupdateを呼び出し

    def update(self):
        self.color = ["green"]
        self.source.stream(self.new_data)
        self.data=np.append(self.data,self.AudioInput())
        if len(self.data)/1024 > 10:
            self.data=self.data[1024:]
        y_harmonic, y_percussive = librosa.effects.hpss(self.data)
        chroma_stft = librosa.feature.chroma_stft(y=y_harmonic, sr=16000)
        self.fft_data = chroma_stft.mean(axis=1)
        self.new_data = dict(x=list(range(12)), y=[math.log(i+1) for i in self.fft_data])
#        self.color = "blue"
#        self.source.stream(self.new_data)
#        self.plt.plot(x=self.axis, y=[math.log(i+1) for i in self.fft_data], clear=True, pen="y", stepMode=True, fillLevel=0, fillBrush=pg.mkBrush(0, 0, 255, 90))

    def AudioInput(self):
        ret=self.stream.read(self.CHUNK, exception_on_overflow = False)    #音声の読み取り(バイナリ) CHUNKが大きいとここで時間かかる # , exception_on_overflow = False added
        #バイナリ → 数値(int16)に変換
        #32768.0=2^16で割ってるのは正規化(絶対値を1以下にすること)
        ret=np.frombuffer(ret, dtype="int16")/32768.0
        return ret


#コールバックの設定
pw = PlotWindow()
curdoc().add_root(pw.fig)
curdoc().add_periodic_callback(pw.update, 1000) #ms単位
        
        