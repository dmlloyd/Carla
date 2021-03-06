#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Carla plugin host
# Copyright (C) 2011-2013 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the GPL.txt file

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

from time import sleep
from PyQt4.QtCore import Qt, QModelIndex, QPointF, QSize
from PyQt4.QtGui import QApplication, QDialogButtonBox, QFileSystemModel, QLabel, QMainWindow, QResizeEvent
from PyQt4.QtGui import QImage, QPalette, QPrinter, QPrintDialog, QSyntaxHighlighter

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom Stuff)

import patchcanvas
import ui_carla
import ui_carla_settings
import ui_carla_settings_driver
from carla_shared import *

# ------------------------------------------------------------------------------------------------------------
# Try Import OpenGL

try:
    from PyQt4.QtOpenGL import QGLWidget
    hasGL = True
except:
    hasGL = False

# ------------------------------------------------------------------------------------------------------------
# Static Variables

# Canvas size
DEFAULT_CANVAS_WIDTH  = 3100
DEFAULT_CANVAS_HEIGHT = 2400

# Tab indexes
TAB_INDEX_MAIN         = 0
TAB_INDEX_CANVAS       = 1
TAB_INDEX_CARLA_ENGINE = 2
TAB_INDEX_CARLA_PATHS  = 3
TAB_INDEX_NONE         = 4

# Single and Multiple client mode is only for JACK,
# but we still want to match QComboBox index to defines,
# so add +2 pos padding if driverName != "JACK".
PROCESS_MODE_NON_JACK_PADDING = 2

# Carla defaults
CARLA_DEFAULT_DISABLE_CHECKS        = False
CARLA_DEFAULT_FORCE_STEREO          = False
CARLA_DEFAULT_PREFER_PLUGIN_BRIDGES = False
CARLA_DEFAULT_PREFER_UI_BRIDGES     = True
CARLA_DEFAULT_UIS_ALWAYS_ON_TOP     = True
CARLA_DEFAULT_USE_DSSI_VST_CHUNKS   = False
CARLA_DEFAULT_MAX_PARAMETERS        = MAX_DEFAULT_PARAMETERS
CARLA_DEFAULT_OSC_UI_TIMEOUT        = 4000
CARLA_DEFAULT_JACK_AUTOCONNECT      = False
CARLA_DEFAULT_JACK_TIMEMASTER       = False
CARLA_DEFAULT_RTAUDIO_BUFFER_SIZE   = 1024
CARLA_DEFAULT_RTAUDIO_SAMPLE_RATE   = 44100

if WINDOWS:
    CARLA_DEFAULT_AUDIO_DRIVER = "DirectSound"
elif MACOS:
    CARLA_DEFAULT_AUDIO_DRIVER = "CoreAudio"
else:
    CARLA_DEFAULT_AUDIO_DRIVER = "JACK"

if WINDOWS or MACOS:
    CARLA_DEFAULT_PROCESS_MODE   = PROCESS_MODE_CONTINUOUS_RACK
    CARLA_DEFAULT_TRANSPORT_MODE = TRANSPORT_MODE_INTERNAL
else:
    CARLA_DEFAULT_PROCESS_MODE   = PROCESS_MODE_MULTIPLE_CLIENTS
    CARLA_DEFAULT_TRANSPORT_MODE = TRANSPORT_MODE_JACK

BUFFER_SIZES = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192)
SAMPLE_RATES = (22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000)

LADISH_APP_NAME = os.getenv("LADISH_APP_NAME")
NSM_URL = os.getenv("NSM_URL")

# ------------------------------------------------------------------------------------------------------------
# Global Variables

appName = os.path.basename(__file__) if "__file__" in dir() and os.path.dirname(__file__) in PATH else sys.argv[0]
libPrefix = None
projectFilename = None

# ------------------------------------------------------------------------------------------------------------
# Log Syntax Highlighter

class LogSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        QSyntaxHighlighter.__init__(self, parent)

        palette = parent.palette()

        self.fColorDebug = palette.color(QPalette.Disabled, QPalette.WindowText)
        self.fColorError = Qt.red

        # -------------------------------------------------------------

    def highlightBlock(self, text):
        if text.startswith("DEBUG:"):
            self.setFormat(0, len(text), self.fColorDebug)
        elif text.startswith("ERROR:"):
            self.setFormat(0, len(text), self.fColorError)

# ------------------------------------------------------------------------------------------------------------
# Driver Settings

class DriverSettingsW(QDialog):
    def __init__(self, parent, driverIndex, driverName):
        QDialog.__init__(self, parent)
        self.ui = ui_carla_settings_driver.Ui_DriverSettingsW()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0 if driverName == "JACK" else 1)

        # -------------------------------------------------------------
        # Internal stuff

        self.fDriverIndex = driverIndex
        self.fDriverName  = driverName

        # -------------------------------------------------------------
        # Set-up GUI

        if driverName != "JACK":
            self.fDeviceNames = Carla.host.get_engine_driver_device_names(driverIndex)

            for name in self.fDeviceNames:
                self.ui.cb_rtaudio_device.addItem(name)

            for bsize in BUFFER_SIZES:
                self.ui.cb_rtaudio_buffersize.addItem(str(bsize))

            for srate in SAMPLE_RATES:
                self.ui.cb_rtaudio_samplerate.addItem(str(srate))

        # -------------------------------------------------------------
        # Load settings

        self.loadSettings()

        # -------------------------------------------------------------
        # Set-up connections

        self.connect(self, SIGNAL("accepted()"), SLOT("slot_saveSettings()"))

        # -------------------------------------------------------------

    def loadSettings(self):
        settings = QSettings()

        if self.fDriverName == "JACK":
            jackAutoConnect = settings.value("Engine/JackAutoConnect", CARLA_DEFAULT_JACK_AUTOCONNECT, type=bool)
            jackTimeMaster  = settings.value("Engine/JackTimeMaster", CARLA_DEFAULT_JACK_TIMEMASTER, type=bool)

            self.ui.cb_jack_autoconnect.setChecked(jackAutoConnect)
            self.ui.cb_jack_timemaster.setChecked(jackTimeMaster)

        else:
            rtaudioDevice     = settings.value("Engine/RtAudioDevice", "", type=str)
            rtaudioBufferSize = settings.value("Engine/RtAudioBufferSize", CARLA_DEFAULT_RTAUDIO_BUFFER_SIZE, type=int)
            rtaudioSampleRate = settings.value("Engine/RtAudioSampleRate", CARLA_DEFAULT_RTAUDIO_SAMPLE_RATE, type=int)

            if rtaudioDevice and rtaudioDevice in self.fDeviceNames:
                self.ui.cb_rtaudio_device.setCurrentIndex(self.fDeviceNames.index(rtaudioDevice))
            else:
                self.ui.cb_rtaudio_device.setCurrentIndex(-1)

            if rtaudioBufferSize and rtaudioBufferSize in BUFFER_SIZES:
                self.ui.cb_rtaudio_buffersize.setCurrentIndex(BUFFER_SIZES.index(rtaudioBufferSize))
            else:
                self.ui.cb_rtaudio_buffersize.setCurrentIndex(BUFFER_SIZES.index(CARLA_DEFAULT_RTAUDIO_BUFFER_SIZE))

            if rtaudioSampleRate and rtaudioSampleRate in SAMPLE_RATES:
                self.ui.cb_rtaudio_samplerate.setCurrentIndex(SAMPLE_RATES.index(rtaudioSampleRate))
            else:
                self.ui.cb_rtaudio_samplerate.setCurrentIndex(SAMPLE_RATES.index(CARLA_DEFAULT_RTAUDIO_SAMPLE_RATE))

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings()

        if self.fDriverName == "JACK":
            settings.setValue("Engine/JackAutoConnect", self.ui.cb_jack_autoconnect.isChecked())
            settings.setValue("Engine/JackTimeMaster", self.ui.cb_jack_timemaster.isChecked())
        else:
            settings.setValue("Engine/RtAudioDevice", self.ui.cb_rtaudio_device.currentText())
            settings.setValue("Engine/RtAudioBufferSize", self.ui.cb_rtaudio_buffersize.currentText())
            settings.setValue("Engine/RtAudioSampleRate", self.ui.cb_rtaudio_samplerate.currentText())

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Settings Dialog

class CarlaSettingsW(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.ui = ui_carla_settings.Ui_CarlaSettingsW()
        self.ui.setupUi(self)

        # -------------------------------------------------------------
        # Set-up GUI

        driverCount = Carla.host.get_engine_driver_count()

        for i in range(driverCount):
            driverName = cString(Carla.host.get_engine_driver_name(i))
            self.ui.cb_engine_audio_driver.addItem(driverName)

        # -------------------------------------------------------------
        # Load settings

        self.loadSettings()

        if not hasGL:
            self.ui.cb_canvas_use_opengl.setChecked(False)
            self.ui.cb_canvas_use_opengl.setEnabled(False)

        if WINDOWS:
            self.ui.group_theme.setEnabled(False)
            self.ui.ch_theme_pro.setChecked(False)
            self.ui.ch_engine_dssi_chunks.setChecked(False)
            self.ui.ch_engine_dssi_chunks.setEnabled(False)

        # -------------------------------------------------------------
        # Set-up connections

        self.connect(self, SIGNAL("accepted()"), SLOT("slot_saveSettings()"))
        self.connect(self.ui.buttonBox.button(QDialogButtonBox.Reset), SIGNAL("clicked()"), SLOT("slot_resetSettings()"))

        self.connect(self.ui.b_main_def_folder_open, SIGNAL("clicked()"), SLOT("slot_getAndSetProjectPath()"))
        self.connect(self.ui.cb_engine_audio_driver, SIGNAL("currentIndexChanged(int)"), SLOT("slot_engineAudioDriverChanged()"))
        self.connect(self.ui.tb_engine_driver_config, SIGNAL("clicked()"), SLOT("slot_showAudioDriverSettings()"))
        self.connect(self.ui.b_paths_add, SIGNAL("clicked()"), SLOT("slot_addPluginPath()"))
        self.connect(self.ui.b_paths_remove, SIGNAL("clicked()"), SLOT("slot_removePluginPath()"))
        self.connect(self.ui.b_paths_change, SIGNAL("clicked()"), SLOT("slot_changePluginPath()"))
        self.connect(self.ui.tw_paths, SIGNAL("currentChanged(int)"), SLOT("slot_pluginPathTabChanged(int)"))
        self.connect(self.ui.lw_ladspa, SIGNAL("currentRowChanged(int)"), SLOT("slot_pluginPathRowChanged(int)"))
        self.connect(self.ui.lw_dssi, SIGNAL("currentRowChanged(int)"), SLOT("slot_pluginPathRowChanged(int)"))
        self.connect(self.ui.lw_lv2, SIGNAL("currentRowChanged(int)"), SLOT("slot_pluginPathRowChanged(int)"))
        self.connect(self.ui.lw_vst, SIGNAL("currentRowChanged(int)"), SLOT("slot_pluginPathRowChanged(int)"))
        self.connect(self.ui.lw_sf2, SIGNAL("currentRowChanged(int)"), SLOT("slot_pluginPathRowChanged(int)"))

        # -------------------------------------------------------------
        # Post-connect setup

        self.ui.lw_ladspa.setCurrentRow(0)
        self.ui.lw_dssi.setCurrentRow(0)
        self.ui.lw_lv2.setCurrentRow(0)
        self.ui.lw_vst.setCurrentRow(0)
        self.ui.lw_gig.setCurrentRow(0)
        self.ui.lw_sf2.setCurrentRow(0)
        self.ui.lw_sfz.setCurrentRow(0)

        self.ui.lw_page.setCurrentCell(0, 0)

    def loadSettings(self):
        settings = QSettings()

        # ---------------------------------------

        self.ui.le_main_def_folder.setText(settings.value("Main/DefaultProjectFolder", HOME, type=str))
        self.ui.ch_theme_pro.setChecked(settings.value("Main/UseProTheme", True, type=bool))
        self.ui.sb_gui_refresh.setValue(settings.value("Main/RefreshInterval", 50, type=int))

        themeColor = settings.value("Main/ProThemeColor", "Black", type=str)

        if themeColor == "System":
            self.ui.cb_theme_color.setCurrentIndex(1)
        else:
            self.ui.cb_theme_color.setCurrentIndex(0)

        # ---------------------------------------

        self.ui.cb_canvas_hide_groups.setChecked(settings.value("Canvas/AutoHideGroups", False, type=bool))
        self.ui.cb_canvas_bezier_lines.setChecked(settings.value("Canvas/UseBezierLines", True, type=bool))
        self.ui.cb_canvas_eyecandy.setCheckState(settings.value("Canvas/EyeCandy", patchcanvas.EYECANDY_SMALL, type=int))
        self.ui.cb_canvas_use_opengl.setChecked(settings.value("Canvas/UseOpenGL", False, type=bool))
        self.ui.cb_canvas_render_aa.setCheckState(settings.value("Canvas/Antialiasing", patchcanvas.ANTIALIASING_SMALL, type=int))
        self.ui.cb_canvas_render_hq_aa.setChecked(settings.value("Canvas/HighQualityAntialiasing", False, type=bool))

        canvasThemeName = settings.value("Canvas/Theme", patchcanvas.getDefaultThemeName(), type=str)

        for i in range(patchcanvas.Theme.THEME_MAX):
            thisThemeName = patchcanvas.getThemeName(i)
            self.ui.cb_canvas_theme.addItem(thisThemeName)
            if thisThemeName == canvasThemeName:
                self.ui.cb_canvas_theme.setCurrentIndex(i)

        # --------------------------------------------

        audioDriver = settings.value("Engine/AudioDriver", CARLA_DEFAULT_AUDIO_DRIVER, type=str)

        for i in range(self.ui.cb_engine_audio_driver.count()):
            if self.ui.cb_engine_audio_driver.itemText(i) == audioDriver:
                self.ui.cb_engine_audio_driver.setCurrentIndex(i)
                break
        else:
            self.ui.cb_engine_audio_driver.setCurrentIndex(-1)

        if audioDriver == "JACK":
            processModeIndex = settings.value("Engine/ProcessMode", PROCESS_MODE_MULTIPLE_CLIENTS, type=int)
            self.ui.cb_engine_process_mode_jack.setCurrentIndex(processModeIndex)
            self.ui.sw_engine_process_mode.setCurrentIndex(0)
        else:
            processModeIndex  = settings.value("Engine/ProcessMode", PROCESS_MODE_CONTINUOUS_RACK, type=int)
            processModeIndex -= PROCESS_MODE_NON_JACK_PADDING
            self.ui.cb_engine_process_mode_other.setCurrentIndex(processModeIndex)
            self.ui.sw_engine_process_mode.setCurrentIndex(1)

        self.ui.sb_engine_max_params.setValue(settings.value("Engine/MaxParameters", CARLA_DEFAULT_MAX_PARAMETERS, type=int))
        self.ui.ch_engine_uis_always_on_top.setChecked(settings.value("Engine/UIsAlwaysOnTop", CARLA_DEFAULT_UIS_ALWAYS_ON_TOP, type=bool))
        self.ui.ch_engine_prefer_ui_bridges.setChecked(settings.value("Engine/PreferUiBridges", CARLA_DEFAULT_PREFER_UI_BRIDGES, type=bool))
        self.ui.sb_engine_oscgui_timeout.setValue(settings.value("Engine/OscUiTimeout", CARLA_DEFAULT_OSC_UI_TIMEOUT, type=int))
        self.ui.ch_engine_disable_checks.setChecked(settings.value("Engine/DisableChecks", CARLA_DEFAULT_DISABLE_CHECKS, type=bool))
        self.ui.ch_engine_dssi_chunks.setChecked(settings.value("Engine/UseDssiVstChunks", CARLA_DEFAULT_USE_DSSI_VST_CHUNKS, type=bool))
        self.ui.ch_engine_prefer_plugin_bridges.setChecked(settings.value("Engine/PreferPluginBridges", CARLA_DEFAULT_PREFER_PLUGIN_BRIDGES, type=bool))
        self.ui.ch_engine_force_stereo.setChecked(settings.value("Engine/ForceStereo", CARLA_DEFAULT_FORCE_STEREO, type=bool))

        # --------------------------------------------

        ladspas = toList(settings.value("Paths/LADSPA", Carla.LADSPA_PATH))
        dssis = toList(settings.value("Paths/DSSI", Carla.DSSI_PATH))
        lv2s = toList(settings.value("Paths/LV2", Carla.LV2_PATH))
        vsts = toList(settings.value("Paths/VST", Carla.VST_PATH))
        gigs = toList(settings.value("Paths/GIG", Carla.GIG_PATH))
        sf2s = toList(settings.value("Paths/SF2", Carla.SF2_PATH))
        sfzs = toList(settings.value("Paths/SFZ", Carla.SFZ_PATH))

        ladspas.sort()
        dssis.sort()
        lv2s.sort()
        vsts.sort()
        gigs.sort()
        sf2s.sort()
        sfzs.sort()

        for ladspa in ladspas:
            self.ui.lw_ladspa.addItem(ladspa)

        for dssi in dssis:
            self.ui.lw_dssi.addItem(dssi)

        for lv2 in lv2s:
            self.ui.lw_lv2.addItem(lv2)

        for vst in vsts:
            self.ui.lw_vst.addItem(vst)

        for gig in gigs:
            self.ui.lw_gig.addItem(gig)

        for sf2 in sf2s:
            self.ui.lw_sf2.addItem(sf2)

        for sfz in sfzs:
            self.ui.lw_sfz.addItem(sfz)

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings()

        # ---------------------------------------

        settings.setValue("Main/DefaultProjectFolder", self.ui.le_main_def_folder.text())
        settings.setValue("Main/UseProTheme", self.ui.ch_theme_pro.isChecked())
        settings.setValue("Main/ProThemeColor", self.ui.cb_theme_color.currentText())
        settings.setValue("Main/RefreshInterval", self.ui.sb_gui_refresh.value())

        # ---------------------------------------

        settings.setValue("Canvas/Theme", self.ui.cb_canvas_theme.currentText())
        settings.setValue("Canvas/AutoHideGroups", self.ui.cb_canvas_hide_groups.isChecked())
        settings.setValue("Canvas/UseBezierLines", self.ui.cb_canvas_bezier_lines.isChecked())
        settings.setValue("Canvas/UseOpenGL", self.ui.cb_canvas_use_opengl.isChecked())
        settings.setValue("Canvas/HighQualityAntialiasing", self.ui.cb_canvas_render_hq_aa.isChecked())

        # 0, 1, 2 match their enum variants
        settings.setValue("Canvas/EyeCandy", self.ui.cb_canvas_eyecandy.checkState())
        settings.setValue("Canvas/Antialiasing", self.ui.cb_canvas_render_aa.checkState())

        # --------------------------------------------

        audioDriver = self.ui.cb_engine_audio_driver.currentText()

        if audioDriver:
            settings.setValue("Engine/AudioDriver", audioDriver)

            if audioDriver == "JACK":
                settings.setValue("Engine/ProcessMode", self.ui.cb_engine_process_mode_jack.currentIndex())
            else:
                settings.setValue("Engine/ProcessMode", self.ui.cb_engine_process_mode_other.currentIndex()+PROCESS_MODE_NON_JACK_PADDING)

        settings.setValue("Engine/MaxParameters", self.ui.sb_engine_max_params.value())
        settings.setValue("Engine/UIsAlwaysOnTop", self.ui.ch_engine_uis_always_on_top.isChecked())
        settings.setValue("Engine/PreferUiBridges", self.ui.ch_engine_prefer_ui_bridges.isChecked())
        settings.setValue("Engine/OscUiTimeout", self.ui.sb_engine_oscgui_timeout.value())
        settings.setValue("Engine/DisableChecks", self.ui.ch_engine_disable_checks.isChecked())
        settings.setValue("Engine/UseDssiVstChunks", self.ui.ch_engine_dssi_chunks.isChecked())
        settings.setValue("Engine/PreferPluginBridges", self.ui.ch_engine_prefer_plugin_bridges.isChecked())
        settings.setValue("Engine/ForceStereo", self.ui.ch_engine_force_stereo.isChecked())

        # --------------------------------------------

        ladspas = []
        dssis = []
        lv2s = []
        vsts = []
        gigs = []
        sf2s = []
        sfzs = []

        for i in range(self.ui.lw_ladspa.count()):
            ladspas.append(self.ui.lw_ladspa.item(i).text())

        for i in range(self.ui.lw_dssi.count()):
            dssis.append(self.ui.lw_dssi.item(i).text())

        for i in range(self.ui.lw_lv2.count()):
            lv2s.append(self.ui.lw_lv2.item(i).text())

        for i in range(self.ui.lw_vst.count()):
            vsts.append(self.ui.lw_vst.item(i).text())

        for i in range(self.ui.lw_gig.count()):
            gigs.append(self.ui.lw_gig.item(i).text())

        for i in range(self.ui.lw_sf2.count()):
            sf2s.append(self.ui.lw_sf2.item(i).text())

        for i in range(self.ui.lw_sfz.count()):
            sfzs.append(self.ui.lw_sfz.item(i).text())

        settings.setValue("Paths/LADSPA", ladspas)
        settings.setValue("Paths/DSSI", dssis)
        settings.setValue("Paths/LV2", lv2s)
        settings.setValue("Paths/VST", vsts)
        settings.setValue("Paths/GIG", gigs)
        settings.setValue("Paths/SF2", sf2s)
        settings.setValue("Paths/SFZ", sfzs)

    @pyqtSlot()
    def slot_resetSettings(self):
        if self.ui.lw_page.currentRow() == TAB_INDEX_MAIN:
            self.ui.le_main_def_folder.setText(HOME)
            self.ui.ch_theme_pro.setChecked(True)
            self.ui.cb_theme_color.setCurrentIndex(0)
            self.ui.sb_gui_refresh.setValue(50)

        elif self.ui.lw_page.currentRow() == TAB_INDEX_CANVAS:
            self.ui.cb_canvas_theme.setCurrentIndex(0)
            self.ui.cb_canvas_hide_groups.setChecked(False)
            self.ui.cb_canvas_bezier_lines.setChecked(True)
            self.ui.cb_canvas_eyecandy.setCheckState(Qt.PartiallyChecked)
            self.ui.cb_canvas_use_opengl.setChecked(False)
            self.ui.cb_canvas_render_aa.setCheckState(Qt.PartiallyChecked)
            self.ui.cb_canvas_render_hq_aa.setChecked(False)

        elif self.ui.lw_page.currentRow() == TAB_INDEX_CARLA_ENGINE:
            self.ui.cb_engine_audio_driver.setCurrentIndex(0)
            self.ui.sb_engine_max_params.setValue(CARLA_DEFAULT_MAX_PARAMETERS)
            self.ui.ch_engine_uis_always_on_top.setChecked(CARLA_DEFAULT_UIS_ALWAYS_ON_TOP)
            self.ui.ch_engine_prefer_ui_bridges.setChecked(CARLA_DEFAULT_PREFER_UI_BRIDGES)
            self.ui.sb_engine_oscgui_timeout.setValue(CARLA_DEFAULT_OSC_UI_TIMEOUT)
            self.ui.ch_engine_disable_checks.setChecked(CARLA_DEFAULT_DISABLE_CHECKS)
            self.ui.ch_engine_dssi_chunks.setChecked(CARLA_DEFAULT_USE_DSSI_VST_CHUNKS)
            self.ui.ch_engine_prefer_plugin_bridges.setChecked(CARLA_DEFAULT_PREFER_PLUGIN_BRIDGES)
            self.ui.ch_engine_force_stereo.setChecked(CARLA_DEFAULT_FORCE_STEREO)

            if self.ui.cb_engine_audio_driver.currentText() == "JACK":
                self.ui.cb_engine_process_mode_jack.setCurrentIndex(PROCESS_MODE_MULTIPLE_CLIENTS)
                self.ui.sw_engine_process_mode.setCurrentIndex(0)
            else:
                self.ui.cb_engine_process_mode_other.setCurrentIndex(PROCESS_MODE_CONTINUOUS_RACK-PROCESS_MODE_NON_JACK_PADDING)
                self.ui.sw_engine_process_mode.setCurrentIndex(1)

        elif self.ui.lw_page.currentRow() == TAB_INDEX_CARLA_PATHS:
            if self.ui.tw_paths.currentIndex() == 0:
                paths = DEFAULT_LADSPA_PATH.split(splitter)
                paths.sort()
                self.ui.lw_ladspa.clear()

                for ladspa in paths:
                    self.ui.lw_ladspa.addItem(ladspa)

            elif self.ui.tw_paths.currentIndex() == 1:
                paths = DEFAULT_DSSI_PATH.split(splitter)
                paths.sort()
                self.ui.lw_dssi.clear()

                for dssi in paths:
                    self.ui.lw_dssi.addItem(dssi)

            elif self.ui.tw_paths.currentIndex() == 2:
                paths = DEFAULT_LV2_PATH.split(splitter)
                paths.sort()
                self.ui.lw_lv2.clear()

                for lv2 in paths:
                    self.ui.lw_lv2.addItem(lv2)

            elif self.ui.tw_paths.currentIndex() == 3:
                paths = DEFAULT_VST_PATH.split(splitter)
                paths.sort()
                self.ui.lw_vst.clear()

                for vst in paths:
                    self.ui.lw_vst.addItem(vst)

            elif self.ui.tw_paths.currentIndex() == 4:
                paths = DEFAULT_GIG_PATH.split(splitter)
                paths.sort()
                self.ui.lw_gig.clear()

                for gig in paths:
                    self.ui.lw_gig.addItem(gig)

            elif self.ui.tw_paths.currentIndex() == 5:
                paths = DEFAULT_SF2_PATH.split(splitter)
                paths.sort()
                self.ui.lw_sf2.clear()

                for sf2 in paths:
                    self.ui.lw_sf2.addItem(sf2)

            elif self.ui.tw_paths.currentIndex() == 6:
                paths = DEFAULT_SFZ_PATH.split(splitter)
                paths.sort()
                self.ui.lw_sfz.clear()

                for sfz in paths:
                    self.ui.lw_sfz.addItem(sfz)

    @pyqtSlot()
    def slot_getAndSetProjectPath(self):
        getAndSetPath(self, self.ui.le_main_def_folder.text(), self.ui.le_main_def_folder)

    @pyqtSlot()
    def slot_engineAudioDriverChanged(self):
        if self.ui.cb_engine_audio_driver.currentText() == "JACK":
            self.ui.sw_engine_process_mode.setCurrentIndex(0)
        else:
            self.ui.sw_engine_process_mode.setCurrentIndex(1)

    @pyqtSlot()
    def slot_showAudioDriverSettings(self):
        driverIndex = self.ui.cb_engine_audio_driver.currentIndex()
        driverName  = self.ui.cb_engine_audio_driver.currentText()
        DriverSettingsW(self, driverIndex, driverName).exec_()

    @pyqtSlot()
    def slot_addPluginPath(self):
        newPath = QFileDialog.getExistingDirectory(self, self.tr("Add Path"), "", QFileDialog.ShowDirsOnly)
        if newPath:
            if self.ui.tw_paths.currentIndex() == 0:
                self.ui.lw_ladspa.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 1:
                self.ui.lw_dssi.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 2:
                self.ui.lw_lv2.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 3:
                self.ui.lw_vst.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 4:
                self.ui.lw_gig.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 5:
                self.ui.lw_sf2.addItem(newPath)
            elif self.ui.tw_paths.currentIndex() == 6:
                self.ui.lw_sfz.addItem(newPath)

    @pyqtSlot()
    def slot_removePluginPath(self):
        if self.ui.tw_paths.currentIndex() == 0:
            self.ui.lw_ladspa.takeItem(self.ui.lw_ladspa.currentRow())
        elif self.ui.tw_paths.currentIndex() == 1:
            self.ui.lw_dssi.takeItem(self.ui.lw_dssi.currentRow())
        elif self.ui.tw_paths.currentIndex() == 2:
            self.ui.lw_lv2.takeItem(self.ui.lw_lv2.currentRow())
        elif self.ui.tw_paths.currentIndex() == 3:
            self.ui.lw_vst.takeItem(self.ui.lw_vst.currentRow())
        elif self.ui.tw_paths.currentIndex() == 4:
            self.ui.lw_gig.takeItem(self.ui.lw_gig.currentRow())
        elif self.ui.tw_paths.currentIndex() == 5:
            self.ui.lw_sf2.takeItem(self.ui.lw_sf2.currentRow())
        elif self.ui.tw_paths.currentIndex() == 6:
            self.ui.lw_sfz.takeItem(self.ui.lw_sfz.currentRow())

    @pyqtSlot()
    def slot_changePluginPath(self):
        if self.ui.tw_paths.currentIndex() == 0:
            currentPath = self.ui.lw_ladspa.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 1:
            currentPath = self.ui.lw_dssi.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 2:
            currentPath = self.ui.lw_lv2.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 3:
            currentPath = self.ui.lw_vst.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 4:
            currentPath = self.ui.lw_gig.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 5:
            currentPath = self.ui.lw_sf2.currentItem().text()
        elif self.ui.tw_paths.currentIndex() == 6:
            currentPath = self.ui.lw_sfz.currentItem().text()
        else:
            currentPath = ""

        newPath = QFileDialog.getExistingDirectory(self, self.tr("Add Path"), currentPath, QFileDialog.ShowDirsOnly)

        if newPath:
            if self.ui.tw_paths.currentIndex() == 0:
                self.ui.lw_ladspa.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 1:
                self.ui.lw_dssi.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 2:
                self.ui.lw_lv2.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 3:
                self.ui.lw_vst.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 4:
                self.ui.lw_gig.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 5:
                self.ui.lw_sf2.currentItem().setText(newPath)
            elif self.ui.tw_paths.currentIndex() == 6:
                self.ui.lw_sfz.currentItem().setText(newPath)

    @pyqtSlot(int)
    def slot_pluginPathTabChanged(self, index):
        if index == 0:
            row = self.ui.lw_ladspa.currentRow()
        elif index == 1:
            row = self.ui.lw_dssi.currentRow()
        elif index == 2:
            row = self.ui.lw_lv2.currentRow()
        elif index == 3:
            row = self.ui.lw_vst.currentRow()
        elif index == 4:
            row = self.ui.lw_gig.currentRow()
        elif index == 5:
            row = self.ui.lw_sf2.currentRow()
        elif index == 6:
            row = self.ui.lw_sfz.currentRow()
        else:
            row = -1

        check = bool(row >= 0)
        self.ui.b_paths_remove.setEnabled(check)
        self.ui.b_paths_change.setEnabled(check)

    @pyqtSlot(int)
    def slot_pluginPathRowChanged(self, row):
        check = bool(row >= 0)
        self.ui.b_paths_remove.setEnabled(check)
        self.ui.b_paths_change.setEnabled(check)

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Main Window

class CarlaMainW(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui =  ui_carla.Ui_CarlaMainW()
        self.ui.setupUi(self)

        # -------------------------------------------------------------
        # Internal stuff

        self.fBufferSize = 0
        self.fSampleRate = 0.0

        self.fEngineStarted   = False
        self.fFirstEngineInit = True

        self.fProjectFilename = None
        self.fProjectLoading  = False

        self.fPluginCount = 0
        self.fPluginList  = []

        self.fIdleTimerFast = 0
        self.fIdleTimerSlow = 0

        self.fLastTransportFrame = 0
        self.fLastTransportState = False

        self.fClientName = "Carla"
        self.fSessionManagerName = "LADISH" if LADISH_APP_NAME else ""

        self.fLadspaRdfNeedsUpdate = True
        self.fLadspaRdfList = []

        # -------------------------------------------------------------
        # Load Settings

        self.loadSettings(True)

        # -------------------------------------------------------------
        # Set-up GUI stuff

        self.fInfoLabel = QLabel(self)
        self.fInfoLabel.setText("")
        self.fInfoText = ""

        self.fDirModel = QFileSystemModel(self)
        self.fDirModel.setNameFilters(cString(Carla.host.get_supported_file_types()).split(";"))
        self.fDirModel.setRootPath(HOME)

        if not WINDOWS:
            self.fSyntaxLog = LogSyntaxHighlighter(self.ui.pte_log)
            self.fSyntaxLog.setDocument(self.ui.pte_log.document())

            if LADISH_APP_NAME:
                self.ui.miniCanvasPreview.setVisible(False)
                self.ui.tabMain.removeTab(1)
        else:
            self.ui.tabMain.removeTab(2)

        self.ui.fileTreeView.setModel(self.fDirModel)
        self.ui.fileTreeView.setRootIndex(self.fDirModel.index(HOME))
        self.ui.fileTreeView.setColumnHidden(1, True)
        self.ui.fileTreeView.setColumnHidden(2, True)
        self.ui.fileTreeView.setColumnHidden(3, True)
        self.ui.fileTreeView.setHeaderHidden(True)

        self.ui.act_engine_start.setEnabled(False)
        self.ui.act_engine_stop.setEnabled(False)
        self.ui.act_plugin_remove_all.setEnabled(False)

        # FIXME: Qt4 needs this so it properly creates & resizes the canvas
        self.ui.tabMain.setCurrentIndex(1)
        self.ui.tabMain.setCurrentIndex(0)

        # -------------------------------------------------------------
        # Set-up Canvas

        self.scene = patchcanvas.PatchScene(self, self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.setRenderHint(QPainter.Antialiasing, bool(self.fSavedSettings["Canvas/Antialiasing"] == patchcanvas.ANTIALIASING_FULL))
        if self.fSavedSettings["Canvas/UseOpenGL"] and hasGL:
            self.ui.graphicsView.setViewport(QGLWidget(self.ui.graphicsView))
            self.ui.graphicsView.setRenderHint(QPainter.HighQualityAntialiasing, self.fSavedSettings["Canvas/HighQualityAntialiasing"])

        pOptions = patchcanvas.options_t()
        pOptions.theme_name       = self.fSavedSettings["Canvas/Theme"]
        pOptions.auto_hide_groups = self.fSavedSettings["Canvas/AutoHideGroups"]
        pOptions.use_bezier_lines = self.fSavedSettings["Canvas/UseBezierLines"]
        pOptions.antialiasing     = self.fSavedSettings["Canvas/Antialiasing"]
        pOptions.eyecandy         = self.fSavedSettings["Canvas/EyeCandy"]

        pFeatures = patchcanvas.features_t()
        pFeatures.group_info   = False
        pFeatures.group_rename = False
        pFeatures.port_info    = False
        pFeatures.port_rename  = False
        pFeatures.handle_group_pos = True

        patchcanvas.setOptions(pOptions)
        patchcanvas.setFeatures(pFeatures)
        patchcanvas.init("Carla", self.scene, canvasCallback, False)

        patchcanvas.setCanvasSize(0, 0, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)
        patchcanvas.setInitialPos(DEFAULT_CANVAS_WIDTH / 2, DEFAULT_CANVAS_HEIGHT / 2)
        self.ui.graphicsView.setSceneRect(0, 0, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)

        # -------------------------------------------------------------
        # Set-up Canvas Preview

        self.ui.miniCanvasPreview.setRealParent(self)
        self.ui.miniCanvasPreview.setViewTheme(patchcanvas.canvas.theme.canvas_bg, patchcanvas.canvas.theme.rubberband_brush, patchcanvas.canvas.theme.rubberband_pen.color())
        self.ui.miniCanvasPreview.init(self.scene, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, self.fSavedSettings["UseCustomMiniCanvasPaint"])
        QTimer.singleShot(100, self, SLOT("slot_miniCanvasInit()"))

        # -------------------------------------------------------------
        # Connect actions to functions

        self.connect(self.ui.act_file_new, SIGNAL("triggered()"), SLOT("slot_fileNew()"))
        self.connect(self.ui.act_file_open, SIGNAL("triggered()"), SLOT("slot_fileOpen()"))
        self.connect(self.ui.act_file_save, SIGNAL("triggered()"), SLOT("slot_fileSave()"))
        self.connect(self.ui.act_file_save_as, SIGNAL("triggered()"), SLOT("slot_fileSaveAs()"))
        #self.connect(self.ui.act_file_export_lv2, SIGNAL("triggered()"), SLOT("slot_fileExportLv2Preset()"))

        self.connect(self.ui.act_engine_start, SIGNAL("triggered()"), SLOT("slot_engineStart()"))
        self.connect(self.ui.act_engine_stop, SIGNAL("triggered()"), SLOT("slot_engineStop()"))

        self.connect(self.ui.act_plugin_add, SIGNAL("triggered()"), SLOT("slot_pluginAdd()"))
        self.connect(self.ui.act_plugin_add2, SIGNAL("triggered()"), SLOT("slot_pluginAdd()"))
        #self.connect(self.ui.act_plugin_refresh, SIGNAL("triggered()"), SLOT("slot_pluginRefresh()"))
        self.connect(self.ui.act_plugin_remove_all, SIGNAL("triggered()"), SLOT("slot_pluginRemoveAll()"))

        self.connect(self.ui.act_plugins_enable, SIGNAL("triggered()"), SLOT("slot_pluginsEnable()"))
        self.connect(self.ui.act_plugins_disable, SIGNAL("triggered()"), SLOT("slot_pluginsDisable()"))
        self.connect(self.ui.act_plugins_panic, SIGNAL("triggered()"), SLOT("slot_pluginsDisable()"))
        self.connect(self.ui.act_plugins_volume100, SIGNAL("triggered()"), SLOT("slot_pluginsVolume100()"))
        self.connect(self.ui.act_plugins_mute, SIGNAL("triggered()"), SLOT("slot_pluginsMute()"))
        self.connect(self.ui.act_plugins_wet100, SIGNAL("triggered()"), SLOT("slot_pluginsWet100()"))
        self.connect(self.ui.act_plugins_bypass, SIGNAL("triggered()"), SLOT("slot_pluginsBypass()"))
        self.connect(self.ui.act_plugins_center, SIGNAL("triggered()"), SLOT("slot_pluginsCenter()"))

        self.connect(self.ui.act_transport_play, SIGNAL("triggered(bool)"), SLOT("slot_transportPlayPause(bool)"))
        self.connect(self.ui.act_transport_stop, SIGNAL("triggered()"), SLOT("slot_transportStop()"))
        self.connect(self.ui.act_transport_backwards, SIGNAL("triggered()"), SLOT("slot_transportBackwards()"))
        self.connect(self.ui.act_transport_forwards, SIGNAL("triggered()"), SLOT("slot_transportForwards()"))

        self.ui.act_canvas_arrange.setEnabled(False) # TODO, later
        self.connect(self.ui.act_canvas_arrange, SIGNAL("triggered()"), SLOT("slot_canvasArrange()"))
        self.connect(self.ui.act_canvas_refresh, SIGNAL("triggered()"), SLOT("slot_canvasRefresh()"))
        self.connect(self.ui.act_canvas_zoom_fit, SIGNAL("triggered()"), SLOT("slot_canvasZoomFit()"))
        self.connect(self.ui.act_canvas_zoom_in, SIGNAL("triggered()"), SLOT("slot_canvasZoomIn()"))
        self.connect(self.ui.act_canvas_zoom_out, SIGNAL("triggered()"), SLOT("slot_canvasZoomOut()"))
        self.connect(self.ui.act_canvas_zoom_100, SIGNAL("triggered()"), SLOT("slot_canvasZoomReset()"))
        self.connect(self.ui.act_canvas_print, SIGNAL("triggered()"), SLOT("slot_canvasPrint()"))
        self.connect(self.ui.act_canvas_save_image, SIGNAL("triggered()"), SLOT("slot_canvasSaveImage()"))

        self.connect(self.ui.act_settings_show_toolbar, SIGNAL("triggered(bool)"), SLOT("slot_toolbarShown()"))
        self.connect(self.ui.act_settings_configure, SIGNAL("triggered()"), SLOT("slot_configureCarla()"))

        self.connect(self.ui.act_help_about, SIGNAL("triggered()"), SLOT("slot_aboutCarla()"))
        self.connect(self.ui.act_help_about_qt, SIGNAL("triggered()"), app, SLOT("aboutQt()"))

        self.connect(self.ui.splitter, SIGNAL("splitterMoved(int, int)"), SLOT("slot_splitterMoved()"))

        self.connect(self.ui.cb_disk, SIGNAL("currentIndexChanged(int)"), SLOT("slot_diskFolderChanged(int)"))
        self.connect(self.ui.b_disk_add, SIGNAL("clicked()"), SLOT("slot_diskFolderAdd()"))
        self.connect(self.ui.b_disk_remove, SIGNAL("clicked()"), SLOT("slot_diskFolderRemove()"))
        self.connect(self.ui.fileTreeView, SIGNAL("doubleClicked(QModelIndex)"), SLOT("slot_fileTreeDoubleClicked(QModelIndex)"))
        self.connect(self.ui.miniCanvasPreview, SIGNAL("miniCanvasMoved(double, double)"), SLOT("slot_miniCanvasMoved(double, double)"))

        self.connect(self.ui.graphicsView.horizontalScrollBar(), SIGNAL("valueChanged(int)"), SLOT("slot_horizontalScrollBarChanged(int)"))
        self.connect(self.ui.graphicsView.verticalScrollBar(), SIGNAL("valueChanged(int)"), SLOT("slot_verticalScrollBarChanged(int)"))

        self.connect(self.scene, SIGNAL("sceneGroupMoved(int, int, QPointF)"), SLOT("slot_canvasItemMoved(int, int, QPointF)"))
        self.connect(self.scene, SIGNAL("scaleChanged(double)"), SLOT("slot_canvasScaleChanged(double)"))

        self.connect(self, SIGNAL("SIGUSR1()"), SLOT("slot_handleSIGUSR1()"))
        self.connect(self, SIGNAL("SIGTERM()"), SLOT("slot_handleSIGTERM()"))

        self.connect(self, SIGNAL("DebugCallback(int, int, int, double, QString)"), SLOT("slot_handleDebugCallback(int, int, int, double, QString)"))
        self.connect(self, SIGNAL("PluginAddedCallback(int)"), SLOT("slot_handlePluginAddedCallback(int)"))
        self.connect(self, SIGNAL("PluginRemovedCallback(int)"), SLOT("slot_handlePluginRemovedCallback(int)"))
        self.connect(self, SIGNAL("PluginRenamedCallback(int, QString)"), SLOT("slot_handlePluginRenamedCallback(int, QString)"))
        self.connect(self, SIGNAL("ParameterValueChangedCallback(int, int, double)"), SLOT("slot_handleParameterValueChangedCallback(int, int, double)"))
        self.connect(self, SIGNAL("ParameterDefaultChangedCallback(int, int, double)"), SLOT("slot_handleParameterDefaultChangedCallback(int, int, double)"))
        self.connect(self, SIGNAL("ParameterMidiChannelChangedCallback(int, int, int)"), SLOT("slot_handleParameterMidiChannelChangedCallback(int, int, int)"))
        self.connect(self, SIGNAL("ParameterMidiCcChangedCallback(int, int, int)"), SLOT("slot_handleParameterMidiCcChangedCallback(int, int, int)"))
        self.connect(self, SIGNAL("ProgramChangedCallback(int, int)"), SLOT("slot_handleProgramChangedCallback(int, int)"))
        self.connect(self, SIGNAL("MidiProgramChangedCallback(int, int)"), SLOT("slot_handleMidiProgramChangedCallback(int, int)"))
        self.connect(self, SIGNAL("NoteOnCallback(int, int, int, int)"), SLOT("slot_handleNoteOnCallback(int, int, int, int)"))
        self.connect(self, SIGNAL("NoteOffCallback(int, int, int)"), SLOT("slot_handleNoteOffCallback(int, int, int)"))
        self.connect(self, SIGNAL("ShowGuiCallback(int, int)"), SLOT("slot_handleShowGuiCallback(int, int)"))
        self.connect(self, SIGNAL("UpdateCallback(int)"), SLOT("slot_handleUpdateCallback(int)"))
        self.connect(self, SIGNAL("ReloadInfoCallback(int)"), SLOT("slot_handleReloadInfoCallback(int)"))
        self.connect(self, SIGNAL("ReloadParametersCallback(int)"), SLOT("slot_handleReloadParametersCallback(int)"))
        self.connect(self, SIGNAL("ReloadProgramsCallback(int)"), SLOT("slot_handleReloadProgramsCallback(int)"))
        self.connect(self, SIGNAL("ReloadAllCallback(int)"), SLOT("slot_handleReloadAllCallback(int)"))
        self.connect(self, SIGNAL("PatchbayClientAddedCallback(int, int, QString)"), SLOT("slot_handlePatchbayClientAddedCallback(int, int, QString)"))
        self.connect(self, SIGNAL("PatchbayClientRemovedCallback(int)"), SLOT("slot_handlePatchbayClientRemovedCallback(int)"))
        self.connect(self, SIGNAL("PatchbayClientRenamedCallback(int, QString)"), SLOT("slot_handlePatchbayClientRenamedCallback(int, QString)"))
        self.connect(self, SIGNAL("PatchbayPortAddedCallback(int, int, int, QString)"), SLOT("slot_handlePatchbayPortAddedCallback(int, int, int, QString)"))
        self.connect(self, SIGNAL("PatchbayPortRemovedCallback(int)"), SLOT("slot_handlePatchbayPortRemovedCallback(int)"))
        self.connect(self, SIGNAL("PatchbayPortRenamedCallback(int, QString)"), SLOT("slot_handlePatchbayPortRenamedCallback(int, QString)"))
        self.connect(self, SIGNAL("PatchbayConnectionAddedCallback(int, int, int)"), SLOT("slot_handlePatchbayConnectionAddedCallback(int, int, int)"))
        self.connect(self, SIGNAL("PatchbayConnectionRemovedCallback(int)"), SLOT("slot_handlePatchbayConnectionRemovedCallback(int)"))
        self.connect(self, SIGNAL("PatchbayIconChangedCallback(int, int)"), SLOT("slot_handlePatchbayIconChangedCallback(int, int)"))
        self.connect(self, SIGNAL("BufferSizeChangedCallback(int)"), SLOT("slot_handleBufferSizeChangedCallback(int)"))
        self.connect(self, SIGNAL("SampleRateChangedCallback(double)"), SLOT("slot_handleSampleRateChangedCallback(double)"))
        self.connect(self, SIGNAL("NSM_AnnounceCallback(QString)"), SLOT("slot_handleNSM_AnnounceCallback(QString)"))
        self.connect(self, SIGNAL("NSM_OpenCallback(QString)"), SLOT("slot_handleNSM_OpenCallback(QString)"))
        self.connect(self, SIGNAL("NSM_SaveCallback()"), SLOT("slot_handleNSM_SaveCallback()"))
        self.connect(self, SIGNAL("ErrorCallback(QString)"), SLOT("slot_handleErrorCallback(QString)"))
        self.connect(self, SIGNAL("QuitCallback()"), SLOT("slot_handleQuitCallback()"))

        self.setProperWindowTitle()

        if NSM_URL:
            Carla.host.nsm_ready()
        else:
            QTimer.singleShot(0, self, SLOT("slot_engineStart()"))

    def startEngine(self):
        # ---------------------------------------------
        # Engine settings

        settings = QSettings()

        audioDriver         = settings.value("Engine/AudioDriver", CARLA_DEFAULT_AUDIO_DRIVER, type=str)
        transportMode       = settings.value("Engine/TransportMode", TRANSPORT_MODE_JACK, type=int)
        forceStereo         = settings.value("Engine/ForceStereo", CARLA_DEFAULT_FORCE_STEREO, type=bool)
        preferPluginBridges = settings.value("Engine/PreferPluginBridges", CARLA_DEFAULT_PREFER_PLUGIN_BRIDGES, type=bool)
        preferUiBridges     = settings.value("Engine/PreferUiBridges", CARLA_DEFAULT_PREFER_UI_BRIDGES, type=bool)
        useDssiVstChunks    = settings.value("Engine/UseDssiVstChunks", CARLA_DEFAULT_USE_DSSI_VST_CHUNKS, type=bool)
        oscUiTimeout        = settings.value("Engine/OscUiTimeout", CARLA_DEFAULT_OSC_UI_TIMEOUT, type=int)

        Carla.processMode   = settings.value("Engine/ProcessMode", CARLA_DEFAULT_PROCESS_MODE, type=int)
        Carla.maxParameters = settings.value("Engine/MaxParameters", CARLA_DEFAULT_MAX_PARAMETERS, type=int)

        if Carla.processMode == PROCESS_MODE_CONTINUOUS_RACK:
            forceStereo = True
        elif Carla.processMode == PROCESS_MODE_MULTIPLE_CLIENTS and LADISH_APP_NAME:
            print("LADISH detected but using multiple clients (not allowed), forcing single client now")
            Carla.processMode = PROCESS_MODE_SINGLE_CLIENT

        Carla.host.set_engine_option(OPTION_PROCESS_MODE, Carla.processMode, "")
        Carla.host.set_engine_option(OPTION_MAX_PARAMETERS, Carla.maxParameters, "")
        Carla.host.set_engine_option(OPTION_FORCE_STEREO, forceStereo, "")
        Carla.host.set_engine_option(OPTION_PREFER_PLUGIN_BRIDGES, preferPluginBridges, "")
        Carla.host.set_engine_option(OPTION_PREFER_UI_BRIDGES, preferUiBridges, "")
        Carla.host.set_engine_option(OPTION_USE_DSSI_VST_CHUNKS, useDssiVstChunks, "")
        Carla.host.set_engine_option(OPTION_OSC_UI_TIMEOUT, oscUiTimeout, "")

        if audioDriver == "JACK":
            jackAutoConnect = settings.value("Engine/JackAutoConnect", CARLA_DEFAULT_JACK_AUTOCONNECT, type=bool)
            jackTimeMaster  = settings.value("Engine/JackTimeMaster", CARLA_DEFAULT_JACK_TIMEMASTER, type=bool)

            if jackAutoConnect and LADISH_APP_NAME:
                print("LADISH detected but using JACK auto-connect (not desired), disabling auto-connect now")
                jackAutoConnect = False

            Carla.host.set_engine_option(OPTION_JACK_AUTOCONNECT, jackAutoConnect, "")
            Carla.host.set_engine_option(OPTION_JACK_TIMEMASTER, jackTimeMaster, "")

        else:
            rtaudioBufferSize = settings.value("Engine/RtAudioBufferSize", CARLA_DEFAULT_RTAUDIO_BUFFER_SIZE, type=int)
            rtaudioSampleRate = settings.value("Engine/RtAudioSampleRate", CARLA_DEFAULT_RTAUDIO_SAMPLE_RATE, type=int)
            rtaudioDevice     = settings.value("Engine/RtAudioDevice", "", type=str)

            Carla.host.set_engine_option(OPTION_RTAUDIO_BUFFER_SIZE, rtaudioBufferSize, "")
            Carla.host.set_engine_option(OPTION_RTAUDIO_SAMPLE_RATE, rtaudioSampleRate, "")
            Carla.host.set_engine_option(OPTION_RTAUDIO_DEVICE, 0, rtaudioDevice)

        # ---------------------------------------------
        # Start

        if not Carla.host.engine_init(audioDriver, self.fClientName):
            if self.fFirstEngineInit:
                self.fFirstEngineInit = False
                return

            audioError = cString(Carla.host.get_last_error())

            if audioError:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Could not connect to Audio backend '%s', possible reasons:\n%s" % (audioDriver, audioError)))
            else:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Could not connect to Audio backend '%s'" % audioDriver))
            return

        self.fBufferSize = Carla.host.get_buffer_size()
        self.fSampleRate = Carla.host.get_sample_rate()

        self.fEngineStarted   = True
        self.fFirstEngineInit = False

        self.fPluginCount = 0
        self.fPluginList  = []

        if transportMode == TRANSPORT_MODE_JACK and audioDriver != "JACK":
            transportMode = TRANSPORT_MODE_INTERNAL

        Carla.host.set_engine_option(OPTION_TRANSPORT_MODE, transportMode, "")

        # Peaks and TimeInfo
        self.fIdleTimerFast = self.startTimer(self.fSavedSettings["Main/RefreshInterval"])
        # LEDs and edit dialog parameters
        self.fIdleTimerSlow = self.startTimer(self.fSavedSettings["Main/RefreshInterval"]*2)

    def stopEngine(self):
        if self.fPluginCount > 0:
            ask = QMessageBox.question(self, self.tr("Warning"), self.tr("There are still some plugins loaded, you need to remove them to stop the engine.\n"
                                                                         "Do you want to do this now?"),
                                                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ask != QMessageBox.Yes:
                return

            self.removeAllPlugins()

        self.fEngineStarted = False

        if Carla.host.is_engine_running() and not Carla.host.engine_close():
            print(cString(Carla.host.get_last_error()))

        self.fBufferSize = 0
        self.fSampleRate = 0.0

        self.fPluginCount = 0
        self.fPluginList  = []

        self.killTimer(self.fIdleTimerFast)
        self.killTimer(self.fIdleTimerSlow)

        patchcanvas.clear()

    def loadProject(self, filename):
        self.fProjectFilename = filename
        self.setProperWindowTitle()

        self.fProjectLoading = True
        Carla.host.load_project(filename)
        self.fProjectLoading = False

    def loadProjectLater(self, filename):
        self.fProjectFilename = filename
        self.setProperWindowTitle()
        QTimer.singleShot(0, self, SLOT("slot_loadProjectLater()"))

    def saveProject(self, filename):
        self.fProjectFilename = filename
        self.setProperWindowTitle()
        Carla.host.save_project(filename)

    def addPlugin(self, btype, ptype, filename, name, label, extraStuff):
        if not self.fEngineStarted:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Cannot add new plugins while engine is stopped"))
            return False

        if not Carla.host.add_plugin(btype, ptype, filename, name, label, extraStuff):
            CustomMessageBox(self, QMessageBox.Critical, self.tr("Error"), self.tr("Failed to load plugin"), cString(Carla.host.get_last_error()), QMessageBox.Ok, QMessageBox.Ok)
            return False

        return True

    def removeAllPlugins(self):
        while (self.ui.w_plugins.layout().takeAt(0)):
            pass

        self.ui.act_plugin_remove_all.setEnabled(False)

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            pwidget.ui.edit_dialog.close()
            pwidget.close()
            pwidget.deleteLater()
            del pwidget

        self.fPluginCount = 0
        self.fPluginList  = []

        Carla.host.remove_all_plugins()

    def getExtraStuff(self, plugin):
        ptype = plugin['type']

        if ptype == PLUGIN_LADSPA:
            uniqueId = plugin['uniqueId']

            self.loadRDFs()

            for rdfItem in self.fLadspaRdfList:
                if rdfItem.UniqueID == uniqueId:
                    return pointer(rdfItem)

        elif ptype == PLUGIN_DSSI:
            if plugin['hints'] & PLUGIN_HAS_GUI:
                gui = findDSSIGUI(plugin['binary'], plugin['name'], plugin['label'])
                if gui:
                    return gui.encode("utf-8")

        elif ptype in (PLUGIN_GIG, PLUGIN_SF2, PLUGIN_SFZ):
            if plugin['name'].endswith(" (16 outputs)"):
                # return a dummy non-null pointer
                INTPOINTER = POINTER(c_int)
                ptr  = c_int(0x1)
                addr = addressof(ptr)
                return cast(addr, INTPOINTER)

        return c_nullptr

    def loadRDFs(self):
        if not self.fLadspaRdfNeedsUpdate:
            return

        self.fLadspaRdfList = []
        self.fLadspaRdfNeedsUpdate = False

        if not haveLRDF:
            return

        settingsDir  = os.path.join(HOME, ".config", "falkTX")
        frLadspaFile = os.path.join(settingsDir, "ladspa_rdf.db")

        if os.path.exists(frLadspaFile):
            frLadspa = open(frLadspaFile, 'r')

            try:
                self.fLadspaRdfList = ladspa_rdf.get_c_ladspa_rdfs(json.load(frLadspa))
            except:
                pass

            frLadspa.close()

    def loadRDFsNeeded(self):
        self.fLadspaRdfNeedsUpdate = True

    def menuTransport(self, enabled):
        self.ui.act_transport_play.setEnabled(enabled)
        self.ui.act_transport_stop.setEnabled(enabled)
        self.ui.act_transport_backwards.setEnabled(enabled)
        self.ui.act_transport_forwards.setEnabled(enabled)
        self.ui.menu_Transport.setEnabled(enabled)

    def refreshTransport(self, forced = False):
        if not self.fEngineStarted:
            return
        if self.fSampleRate == 0.0:
            return

        timeInfo = Carla.host.get_transport_info()
        playing  = bool(timeInfo['playing'])
        frame    = int(timeInfo['frame'])

        if playing != self.fLastTransportState or forced:
            if playing:
                icon = getIcon("media-playback-pause")
                self.ui.act_transport_play.setChecked(True)
                self.ui.act_transport_play.setIcon(icon)
                self.ui.act_transport_play.setText(self.tr("&Pause"))
            else:
                icon = getIcon("media-playback-start")
                self.ui.act_transport_play.setChecked(False)
                self.ui.act_transport_play.setIcon(icon)
                self.ui.act_transport_play.setText(self.tr("&Play"))

            self.fLastTransportState = playing

        if frame != self.fLastTransportFrame or forced:
            time = frame / self.fSampleRate
            secs = time % 60
            mins = (time / 60) % 60
            hrs  = (time / 3600) % 60

            textTransport = "Transport %s, at %02i:%02i:%02i" % ("playing" if playing else "stopped", hrs, mins, secs)
            self.fInfoLabel.setText("%s | %s" % (self.fInfoText, textTransport))

            self.fLastTransportFrame = frame

    def setProperWindowTitle(self):
        title = LADISH_APP_NAME if LADISH_APP_NAME else "Carla"

        if self.fProjectFilename:
            title += " - %s" % os.path.basename(self.fProjectFilename)
        if self.fSessionManagerName:
            title += " (%s)" % self.fSessionManagerName

        self.setWindowTitle(title)

    def updateInfoLabelPos(self):
        tabBar = self.ui.tabMain.tabBar()
        y = tabBar.mapFromParent(self.ui.centralwidget.pos()).y()+tabBar.height()/4

        if not self.ui.toolBar.isVisible():
            y -= self.ui.toolBar.height()

        self.fInfoLabel.move(self.fInfoLabel.x(), y)

    def updateInfoLabelSize(self):
        tabBar = self.ui.tabMain.tabBar()
        self.fInfoLabel.resize(self.ui.tabMain.width()-tabBar.width()-20, self.fInfoLabel.height())

    @pyqtSlot()
    def slot_fileNew(self):
        self.removeAllPlugins()
        self.fProjectFilename = None
        self.fProjectLoading  = False
        self.setProperWindowTitle()

    @pyqtSlot()
    def slot_fileOpen(self):
        fileFilter  = self.tr("Carla Project File (*.carxp)")
        filenameTry = QFileDialog.getOpenFileName(self, self.tr("Open Carla Project File"), self.fSavedSettings["Main/DefaultProjectFolder"], filter=fileFilter)

        if filenameTry:
            # FIXME - show dialog to user (remove all plugins?)
            self.removeAllPlugins()
            self.loadProject(filenameTry)

    @pyqtSlot()
    def slot_fileSave(self, saveAs=False):
        if self.fProjectFilename and not saveAs:
            return self.saveProject(self.fProjectFilename)

        fileFilter  = self.tr("Carla Project File (*.carxp)")
        filenameTry = QFileDialog.getSaveFileName(self, self.tr("Save Carla Project File"), self.fSavedSettings["Main/DefaultProjectFolder"], filter=fileFilter)

        if not filenameTry:
            return

        if not filenameTry.endswith(".carxp"):
            filenameTry += ".carxp"

        self.saveProject(filenameTry)

    @pyqtSlot()
    def slot_fileSaveAs(self):
        self.slot_fileSave(True)

    @pyqtSlot()
    def slot_fileExportLv2Preset(self):
        fileFilter  = self.tr("LV2 Preset (*.lv2)")
        filenameTry = QFileDialog.getSaveFileName(self, self.tr("Save Carla Project File"), self.fSavedSettings["Main/DefaultProjectFolder"], filter=fileFilter)

        if not filenameTry:
            return

        if not filenameTry.endswith(".lv2"):
            filenameTry += ".lv2"

        if os.path.exists(filenameTry) and not os.path.isdir(filenameTry):
            # TODO - error
            return

        # Save current project to a tmp file, and read it
        tmpFile = os.path.join(TMP, "carla-plugin-export.carxp")

        if not Carla.host.save_project(tmpFile):
            # TODO - error
            return

        tmpFileFd = open(tmpFile, "r")
        presetContents = tmpFileFd.read()
        tmpFileFd.close()
        os.remove(tmpFile)

        # Create LV2 Preset
        os.mkdir(filenameTry)

        manifestPath = os.path.join(filenameTry, "manifest.ttl")

        manifestFd = open(manifestPath, "w")
        manifestFd.write("""# LV2 Preset for the Carla LV2 Plugin
@prefix lv2:   <http://lv2plug.in/ns/lv2core#> .
@prefix pset:  <http://lv2plug.in/ns/ext/presets#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix state: <http://lv2plug.in/ns/ext/state#> .

<file://%s>
    a pset:Preset ;
    lv2:appliesTo <http://kxstudio.sf.net/carla> ;
    rdfs:label "%s" ;
    state:state [
        <http://kxstudio.sf.net/ns/carla/string>
\"\"\"
%s
\"\"\"
    ] .
""" % (manifestPath, os.path.basename(filenameTry), presetContents))
        manifestFd.close()

    @pyqtSlot()
    def slot_loadProjectLater(self):
        self.fProjectLoading = True
        Carla.host.load_project(self.fProjectFilename)
        self.fProjectLoading = False

    @pyqtSlot()
    def slot_engineStart(self):
        self.startEngine()
        check = Carla.host.is_engine_running()
        self.ui.act_engine_start.setEnabled(not check)
        self.ui.act_engine_stop.setEnabled(check)

        if self.fSessionManagerName != "Non Session Manager":
            self.ui.act_file_open.setEnabled(check)

        if check:
            self.fInfoText = "Engine running | SampleRate: %g | BufferSize: %i" % (self.fSampleRate, self.fBufferSize)
            self.refreshTransport(True)

        self.menuTransport(check)

    @pyqtSlot()
    def slot_engineStop(self):
        self.stopEngine()
        check = Carla.host.is_engine_running()
        self.ui.act_engine_start.setEnabled(not check)
        self.ui.act_engine_stop.setEnabled(check)

        if self.fSessionManagerName != "Non Session Manager":
            self.ui.act_file_open.setEnabled(check)

        if not check:
            self.fInfoText = ""
            self.fInfoLabel.setText("Engine stopped")

        self.menuTransport(check)

    @pyqtSlot()
    def slot_pluginAdd(self):
        dialog = PluginDatabaseW(self)
        if dialog.exec_():
            btype    = dialog.fRetPlugin['build']
            ptype    = dialog.fRetPlugin['type']
            filename = dialog.fRetPlugin['binary']
            label    = dialog.fRetPlugin['label']
            extraStuff = self.getExtraStuff(dialog.fRetPlugin)
            self.addPlugin(btype, ptype, filename, None, label, extraStuff)

    @pyqtSlot()
    def slot_pluginRemoveAll(self):
        self.removeAllPlugins()

    @pyqtSlot()
    def slot_pluginsEnable(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            pwidget.setActive(True, True, True)

    @pyqtSlot()
    def slot_pluginsDisable(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            pwidget.setActive(False, True, True)

    @pyqtSlot()
    def slot_pluginsVolume100(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            if pwidget.fPluginInfo['hints'] & PLUGIN_CAN_VOLUME:
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_VOLUME, 1.0)
                Carla.host.set_volume(i, 1.0)

    @pyqtSlot()
    def slot_pluginsMute(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            if pwidget.fPluginInfo['hints'] & PLUGIN_CAN_VOLUME:
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_VOLUME, 0.0)
                Carla.host.set_volume(i, 0.0)

    @pyqtSlot()
    def slot_pluginsWet100(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            if pwidget.fPluginInfo['hints'] & PLUGIN_CAN_DRYWET:
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_DRYWET, 1.0)
                Carla.host.set_drywet(i, 1.0)

    @pyqtSlot()
    def slot_pluginsBypass(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            if pwidget.fPluginInfo['hints'] & PLUGIN_CAN_DRYWET:
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_DRYWET, 0.0)
                Carla.host.set_drywet(i, 0.0)

    @pyqtSlot()
    def slot_pluginsCenter(self):
        if not self.fEngineStarted:
            return

        for i in range(self.fPluginCount):
            pwidget = self.fPluginList[i]

            if pwidget is None:
                break

            if pwidget.fPluginInfo['hints'] & PLUGIN_CAN_BALANCE:
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_BALANCE_LEFT, -1.0)
                pwidget.ui.edit_dialog.setParameterValue(PARAMETER_BALANCE_RIGHT, 1.0)
                Carla.host.set_balance_left(i, -1.0)
                Carla.host.set_balance_right(i, 1.0)

    @pyqtSlot(bool)
    def slot_transportPlayPause(self, toggled):
        if not self.fEngineStarted:
            return

        if toggled:
            Carla.host.transport_play()
        else:
            Carla.host.transport_pause()

        self.refreshTransport()

    @pyqtSlot()
    def slot_transportStop(self):
        if not self.fEngineStarted:
            return

        Carla.host.transport_pause()
        Carla.host.transport_relocate(0)

        self.refreshTransport()

    @pyqtSlot()
    def slot_transportBackwards(self):
        if not self.fEngineStarted:
            return

        newFrame = Carla.host.get_current_transport_frame() - 100000

        if newFrame < 0:
            newFrame = 0

        Carla.host.transport_relocate(newFrame)

    @pyqtSlot()
    def slot_transportForwards(self):
        if not self.fEngineStarted:
            return

        newFrame = Carla.host.get_current_transport_frame() + 100000
        Carla.host.transport_relocate(newFrame)

    @pyqtSlot()
    def slot_canvasArrange(self):
        patchcanvas.arrange()

    @pyqtSlot()
    def slot_canvasRefresh(self):
        patchcanvas.clear()
        if Carla.host.is_engine_running():
            Carla.host.patchbay_refresh()
        QTimer.singleShot(1000 if self.fSavedSettings['Canvas/EyeCandy'] else 0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot()
    def slot_canvasZoomFit(self):
        self.scene.zoom_fit()

    @pyqtSlot()
    def slot_canvasZoomIn(self):
        self.scene.zoom_in()

    @pyqtSlot()
    def slot_canvasZoomOut(self):
        self.scene.zoom_out()

    @pyqtSlot()
    def slot_canvasZoomReset(self):
        self.scene.zoom_reset()

    @pyqtSlot()
    def slot_canvasPrint(self):
        self.scene.clearSelection()
        self.fExportPrinter = QPrinter()
        dialog = QPrintDialog(self.fExportPrinter, self)

        if dialog.exec_():
            painter = QPainter(self.fExportPrinter)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            self.scene.render(painter)
            painter.restore()

    @pyqtSlot()
    def slot_canvasSaveImage(self):
        newPath = QFileDialog.getSaveFileName(self, self.tr("Save Image"), filter=self.tr("PNG Image (*.png);;JPEG Image (*.jpg)"))

        if newPath:
            self.scene.clearSelection()

            # FIXME - must be a better way...
            if newPath.endswith((".jpg", ".jpG", ".jPG", ".JPG", ".JPg", ".Jpg")):
                imgFormat = "JPG"
            elif newPath.endswith((".png", ".pnG", ".pNG", ".PNG", ".PNg", ".Png")):
                imgFormat = "PNG"
            else:
                # File-dialog may not auto-add the extension
                imgFormat = "PNG"
                newPath  += ".png"

            self.fExportImage = QImage(self.scene.sceneRect().width(), self.scene.sceneRect().height(), QImage.Format_RGB32)
            painter = QPainter(self.fExportImage)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing) # TODO - set true, cleanup this
            painter.setRenderHint(QPainter.TextAntialiasing)
            self.scene.render(painter)
            self.fExportImage.save(newPath, imgFormat, 100)
            painter.restore()

    @pyqtSlot()
    def slot_toolbarShown(self):
        self.updateInfoLabelPos()

    @pyqtSlot()
    def slot_configureCarla(self):
        dialog = CarlaSettingsW(self)
        if dialog.exec_():
            self.loadSettings(False)
            patchcanvas.clear()

            pOptions = patchcanvas.options_t()
            pOptions.theme_name       = self.fSavedSettings["Canvas/Theme"]
            pOptions.auto_hide_groups = self.fSavedSettings["Canvas/AutoHideGroups"]
            pOptions.use_bezier_lines = self.fSavedSettings["Canvas/UseBezierLines"]
            pOptions.antialiasing     = self.fSavedSettings["Canvas/Antialiasing"]
            pOptions.eyecandy         = self.fSavedSettings["Canvas/EyeCandy"]

            pFeatures = patchcanvas.features_t()
            pFeatures.group_info   = False
            pFeatures.group_rename = False
            pFeatures.port_info    = False
            pFeatures.port_rename  = False
            pFeatures.handle_group_pos = True

            patchcanvas.setOptions(pOptions)
            patchcanvas.setFeatures(pFeatures)
            patchcanvas.init("Carla", self.scene, canvasCallback, False)

            if self.fEngineStarted:
                Carla.host.patchbay_refresh()

    @pyqtSlot()
    def slot_aboutCarla(self):
        CarlaAboutW(self).exec_()

    @pyqtSlot()
    def slot_splitterMoved(self):
        self.updateInfoLabelSize()

    @pyqtSlot(int)
    def slot_diskFolderChanged(self, index):
        if index < 0:
            return
        elif index == 0:
            filename = HOME
            self.ui.b_disk_remove.setEnabled(False)
        else:
            filename = self.ui.cb_disk.itemData(index)
            self.ui.b_disk_remove.setEnabled(True)

        self.fDirModel.setRootPath(filename)
        self.ui.fileTreeView.setRootIndex(self.fDirModel.index(filename))

    @pyqtSlot()
    def slot_diskFolderAdd(self):
        newPath = QFileDialog.getExistingDirectory(self, self.tr("New Folder"), "", QFileDialog.ShowDirsOnly)

        if newPath:
            if newPath[-1] == os.sep:
                newPath = newPath[:-1]
            self.ui.cb_disk.addItem(os.path.basename(newPath), newPath)
            self.ui.cb_disk.setCurrentIndex(self.ui.cb_disk.count()-1)
            self.ui.b_disk_remove.setEnabled(True)

    @pyqtSlot()
    def slot_diskFolderRemove(self):
        index = self.ui.cb_disk.currentIndex()

        if index <= 0:
            return

        self.ui.cb_disk.removeItem(index)

        if self.ui.cb_disk.currentIndex() == 0:
            self.ui.b_disk_remove.setEnabled(False)

    @pyqtSlot(QModelIndex)
    def slot_fileTreeDoubleClicked(self, modelIndex):
        filename = self.fDirModel.filePath(modelIndex)

        if not Carla.host.load_filename(filename):
            CustomMessageBox(self, QMessageBox.Critical, self.tr("Error"),
                             self.tr("Failed to load file"),
                             cString(Carla.host.get_last_error()), QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot(float, float)
    def slot_miniCanvasMoved(self, xp, yp):
        self.ui.graphicsView.horizontalScrollBar().setValue(xp * DEFAULT_CANVAS_WIDTH)
        self.ui.graphicsView.verticalScrollBar().setValue(yp * DEFAULT_CANVAS_HEIGHT)

    @pyqtSlot(int)
    def slot_horizontalScrollBarChanged(self, value):
        maximum = self.ui.graphicsView.horizontalScrollBar().maximum()
        if maximum == 0:
            xp = 0
        else:
            xp = float(value) / maximum
        self.ui.miniCanvasPreview.setViewPosX(xp)

    @pyqtSlot(int)
    def slot_verticalScrollBarChanged(self, value):
        maximum = self.ui.graphicsView.verticalScrollBar().maximum()
        if maximum == 0:
            yp = 0
        else:
            yp = float(value) / maximum
        self.ui.miniCanvasPreview.setViewPosY(yp)

    @pyqtSlot(int, int, QPointF)
    def slot_canvasItemMoved(self, group_id, split_mode, pos):
        self.ui.miniCanvasPreview.update()

    @pyqtSlot(float)
    def slot_canvasScaleChanged(self, scale):
        self.ui.miniCanvasPreview.setViewScale(scale)

    @pyqtSlot()
    def slot_handleSIGUSR1(self):
        print("Got SIGUSR1 -> Saving project now")
        QTimer.singleShot(0, self, SLOT("slot_fileSave()"))

    @pyqtSlot()
    def slot_handleSIGTERM(self):
        print("Got SIGTERM -> Closing now")
        self.close()

    @pyqtSlot()
    def slot_miniCanvasInit(self):
        settings = QSettings()
        self.ui.graphicsView.horizontalScrollBar().setValue(settings.value("HorizontalScrollBarValue", DEFAULT_CANVAS_WIDTH / 3, type=int))
        self.ui.graphicsView.verticalScrollBar().setValue(settings.value("VerticalScrollBarValue", DEFAULT_CANVAS_HEIGHT * 3 / 8, type=int))

        tabBar = self.ui.tabMain.tabBar()
        x = tabBar.width()+20
        y = tabBar.mapFromParent(self.ui.centralwidget.pos()).y()+tabBar.height()/4
        self.fInfoLabel.move(x, y)
        self.fInfoLabel.resize(self.ui.tabMain.width()-x, tabBar.height())

    @pyqtSlot()
    def slot_miniCanvasCheckAll(self):
        self.slot_miniCanvasCheckSize()
        self.slot_horizontalScrollBarChanged(self.ui.graphicsView.horizontalScrollBar().value())
        self.slot_verticalScrollBarChanged(self.ui.graphicsView.verticalScrollBar().value())

    @pyqtSlot()
    def slot_miniCanvasCheckSize(self):
        self.ui.miniCanvasPreview.setViewSize(float(self.ui.graphicsView.width()) / DEFAULT_CANVAS_WIDTH, float(self.ui.graphicsView.height()) / DEFAULT_CANVAS_HEIGHT)

    @pyqtSlot(int, int, int, float, str)
    def slot_handleDebugCallback(self, pluginId, value1, value2, value3, valueStr):
        self.ui.pte_log.appendPlainText(valueStr.replace("[30;1m", "DEBUG: ").replace("[31m", "ERROR: ").replace("[0m", "").replace("\n", ""))

    @pyqtSlot(int)
    def slot_handlePluginAddedCallback(self, pluginId):
        pwidget = PluginWidget(self, pluginId)

        self.ui.w_plugins.layout().addWidget(pwidget)

        self.fPluginList.append(pwidget)
        self.fPluginCount += 1

        if not self.fProjectLoading:
            pwidget.setActive(True, True, True)

        if self.fPluginCount == 1:
            self.ui.act_plugin_remove_all.setEnabled(True)

    @pyqtSlot(int)
    def slot_handlePluginRemovedCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        self.fPluginCount -= 1
        self.fPluginList.pop(pluginId)

        self.ui.w_plugins.layout().removeWidget(pwidget)

        pwidget.ui.edit_dialog.close()
        pwidget.close()
        pwidget.deleteLater()
        del pwidget

        # push all plugins 1 slot back
        for i in range(pluginId, self.fPluginCount):
            self.fPluginList[i].setId(i)

        if self.fPluginCount == 0:
            self.ui.act_plugin_remove_all.setEnabled(False)

    @pyqtSlot(int, str)
    def slot_handlePluginRenamedCallback(self, pluginId, newName):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.label_name.setText(newName)

    @pyqtSlot(int, int, float)
    def slot_handleParameterValueChangedCallback(self, pluginId, parameterId, value):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setParameterValue(parameterId, value)

    @pyqtSlot(int, int, float)
    def slot_handleParameterDefaultChangedCallback(self, pluginId, parameterId, value):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setParameterDefault(parameterId, value)

    @pyqtSlot(int, int, int)
    def slot_handleParameterMidiChannelChangedCallback(self, pluginId, parameterId, channel):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setParameterMidiChannel(parameterId, channel)

    @pyqtSlot(int, int, int)
    def slot_handleParameterMidiCcChangedCallback(self, pluginId, parameterId, cc):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setParameterMidiControl(parameterId, cc)

    @pyqtSlot(int, int)
    def slot_handleProgramChangedCallback(self, pluginId, programId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setProgram(programId)

    @pyqtSlot(int, int)
    def slot_handleMidiProgramChangedCallback(self, pluginId, midiProgramId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.setMidiProgram(midiProgramId)

    @pyqtSlot(int, int, int, int)
    def slot_handleNoteOnCallback(self, pluginId, channel, note, velo):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.sendNoteOn(channel, note)

    @pyqtSlot(int, int, int)
    def slot_handleNoteOffCallback(self, pluginId, channel, note):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.sendNoteOff(channel, note)

    @pyqtSlot(int, int)
    def slot_handleShowGuiCallback(self, pluginId, show):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        if show == 0:
            pwidget.ui.b_gui.setChecked(False)
            pwidget.ui.b_gui.setEnabled(True)
        elif show == 1:
            pwidget.ui.b_gui.setChecked(True)
            pwidget.ui.b_gui.setEnabled(True)
        elif show == -1:
            pwidget.ui.b_gui.setChecked(False)
            pwidget.ui.b_gui.setEnabled(False)

    @pyqtSlot(int)
    def slot_handleUpdateCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.edit_dialog.updateInfo()

    @pyqtSlot(int)
    def slot_handleReloadInfoCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.edit_dialog.reloadInfo()

    @pyqtSlot(int)
    def slot_handleReloadParametersCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.edit_dialog.reloadParameters()

    @pyqtSlot(int)
    def slot_handleReloadProgramsCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.edit_dialog.reloadPrograms()

    @pyqtSlot(int)
    def slot_handleReloadAllCallback(self, pluginId):
        if pluginId >= self.fPluginCount:
            return

        pwidget = self.fPluginList[pluginId]
        if pwidget is None:
            return

        pwidget.ui.edit_dialog.reloadAll()

    @pyqtSlot(int, int, str)
    def slot_handlePatchbayClientAddedCallback(self, clientId, clientIcon, clientName):
        pcSplit = patchcanvas.SPLIT_UNDEF
        pcIcon  = patchcanvas.ICON_APPLICATION

        if clientIcon == PATCHBAY_ICON_HARDWARE:
            pcSplit = patchcanvas.SPLIT_YES
            pcIcon = patchcanvas.ICON_HARDWARE
        elif clientIcon == PATCHBAY_ICON_DISTRHO:
            pcIcon = patchcanvas.ICON_DISTRHO
        elif clientIcon == PATCHBAY_ICON_FILE:
            pcIcon = patchcanvas.ICON_FILE
        elif clientIcon == PATCHBAY_ICON_PLUGIN:
            pcIcon = patchcanvas.ICON_PLUGIN

        patchcanvas.addGroup(clientId, clientName, pcSplit, pcIcon)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int)
    def slot_handlePatchbayClientRemovedCallback(self, clientId):
        if not self.fEngineStarted: return
        patchcanvas.removeGroup(clientId)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int, str)
    def slot_handlePatchbayClientRenamedCallback(self, clientId, newClientName):
        patchcanvas.renameGroup(clientId, newClientName)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int, int, int, str)
    def slot_handlePatchbayPortAddedCallback(self, clientId, portId, portFlags, portName):
        if (portFlags & PATCHBAY_PORT_IS_INPUT):
            portMode = patchcanvas.PORT_MODE_INPUT
        elif (portFlags & PATCHBAY_PORT_IS_OUTPUT):
            portMode = patchcanvas.PORT_MODE_OUTPUT
        else:
            portMode = patchcanvas.PORT_MODE_NULL

        if (portFlags & PATCHBAY_PORT_IS_AUDIO):
            portType = patchcanvas.PORT_TYPE_AUDIO_JACK
        elif (portFlags & PATCHBAY_PORT_IS_MIDI):
            portType = patchcanvas.PORT_TYPE_MIDI_JACK
        else:
            portType = patchcanvas.PORT_TYPE_NULL

        patchcanvas.addPort(clientId, portId, portName, portMode, portType)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int)
    def slot_handlePatchbayPortRemovedCallback(self, portId):
        if not self.fEngineStarted: return
        patchcanvas.removePort(portId)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int, str)
    def slot_handlePatchbayPortRenamedCallback(self, portId, newPortName):
        patchcanvas.renamePort(portId, newPortName)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int, int, int)
    def slot_handlePatchbayConnectionAddedCallback(self, connectionId, portOutId, portInId):
        patchcanvas.connectPorts(connectionId, portOutId, portInId)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int)
    def slot_handlePatchbayConnectionRemovedCallback(self, connectionId):
        if not self.fEngineStarted: return
        patchcanvas.disconnectPorts(connectionId)
        QTimer.singleShot(0, self.ui.miniCanvasPreview, SLOT("update()"))

    @pyqtSlot(int, int)
    def slot_handlePatchbayIconChangedCallback(self, clientId, clientIcon):
        pcIcon = patchcanvas.ICON_APPLICATION

        if clientIcon == PATCHBAY_ICON_HARDWARE:
            pcIcon = patchcanvas.ICON_HARDWARE
        elif clientIcon == PATCHBAY_ICON_DISTRHO:
            pcIcon = patchcanvas.ICON_DISTRHO
        elif clientIcon == PATCHBAY_ICON_FILE:
            pcIcon = patchcanvas.ICON_FILE
        elif clientIcon == PATCHBAY_ICON_PLUGIN:
            pcIcon = patchcanvas.ICON_PLUGIN

        patchcanvas.setGroupIcon(clientId, pcIcon)

    @pyqtSlot(int)
    def slot_handleBufferSizeChangedCallback(self, newBufferSize):
        self.fBufferSize = newBufferSize
        self.fInfoText   = "Engine running | SampleRate: %g | BufferSize: %i" % (self.fSampleRate, self.fBufferSize)

    @pyqtSlot(float)
    def slot_handleSampleRateChangedCallback(self, newSampleRate):
        self.fSampleRate = newSampleRate
        self.fInfoText   = "Engine running | SampleRate: %g | BufferSize: %i" % (self.fSampleRate, self.fBufferSize)

    @pyqtSlot(str)
    def slot_handleNSM_AnnounceCallback(self, smName):
        self.fSessionManagerName = smName
        self.ui.act_file_new.setEnabled(False)
        self.ui.act_file_open.setEnabled(False)
        self.ui.act_file_save_as.setEnabled(False)
        self.ui.act_engine_start.setEnabled(True)
        self.ui.act_engine_stop.setEnabled(False)

    @pyqtSlot(str)
    def slot_handleNSM_OpenCallback(self, data):
        projectPath, clientId = data.rsplit(":", 1)
        self.fClientName = clientId

        # restart engine
        if self.fEngineStarted:
            self.stopEngine()

        self.slot_engineStart()

        if self.fEngineStarted:
            self.loadProject(projectPath)

        Carla.host.nsm_reply_open()

    @pyqtSlot()
    def slot_handleNSM_SaveCallback(self):
        self.saveProject(self.fProjectFilename)
        Carla.host.nsm_reply_save()

    @pyqtSlot(str)
    def slot_handleErrorCallback(self, error):
        QMessageBox.critical(self, self.tr("Error"), error)

    @pyqtSlot()
    def slot_handleQuitCallback(self):
        CustomMessageBox(self, QMessageBox.Warning, self.tr("Warning"),
            self.tr("Engine has been stopped or crashed.\nPlease restart Carla"),
            self.tr("You may want to save your session now..."), QMessageBox.Ok, QMessageBox.Ok)

    def loadSettings(self, geometry):
        settings = QSettings()

        if geometry:
            self.restoreGeometry(settings.value("Geometry", ""))

            showToolbar = settings.value("ShowToolbar", True, type=bool)
            self.ui.act_settings_show_toolbar.setChecked(showToolbar)
            self.ui.toolBar.setVisible(showToolbar)

            if settings.contains("SplitterState"):
                self.ui.splitter.restoreState(settings.value("SplitterState", ""))
            else:
                self.ui.splitter.setSizes([99999, 210])

            diskFolders = toList(settings.value("DiskFolders", [HOME]))

            self.ui.cb_disk.setItemData(0, HOME)

            for i in range(len(diskFolders)):
                if i == 0: continue
                folder = diskFolders[i]
                self.ui.cb_disk.addItem(os.path.basename(folder), folder)

            pal1 = app.palette().base().color()
            pal2 = app.palette().button().color()
            col1 = "stop:0 rgb(%i, %i, %i)" % (pal1.red(), pal1.green(), pal1.blue())
            col2 = "stop:1 rgb(%i, %i, %i)" % (pal2.red(), pal2.green(), pal2.blue())

            self.setStyleSheet("""
              QWidget#w_plugins {
                background-color: qlineargradient(spread:pad,
                    x1:0.0, y1:0.0,
                    x2:0.2, y2:1.0,
                    %s,
                    %s
                );
              }
            """ % (col1, col2))

            if MACOS and not settings.value("Main/UseProTheme", True, type=bool):
                self.setUnifiedTitleAndToolBarOnMac(True)

        useCustomMiniCanvasPaint = bool(settings.value("Main/UseProTheme", True, type=bool) and
                                        settings.value("Main/ProThemeColor", "Black", type=str) == "Black")

        self.fSavedSettings = {
            "Main/DefaultProjectFolder": settings.value("Main/DefaultProjectFolder", HOME, type=str),
            "Main/RefreshInterval": settings.value("Main/RefreshInterval", 50, type=int),
            "Canvas/Theme": settings.value("Canvas/Theme", patchcanvas.getDefaultThemeName(), type=str),
            "Canvas/AutoHideGroups": settings.value("Canvas/AutoHideGroups", False, type=bool),
            "Canvas/UseBezierLines": settings.value("Canvas/UseBezierLines", True, type=bool),
            "Canvas/EyeCandy": settings.value("Canvas/EyeCandy", patchcanvas.EYECANDY_SMALL, type=int),
            "Canvas/UseOpenGL": settings.value("Canvas/UseOpenGL", False, type=bool),
            "Canvas/Antialiasing": settings.value("Canvas/Antialiasing", patchcanvas.ANTIALIASING_SMALL, type=int),
            "Canvas/HighQualityAntialiasing": settings.value("Canvas/HighQualityAntialiasing", False, type=bool),
            "UseCustomMiniCanvasPaint": useCustomMiniCanvasPaint
        }

        # ---------------------------------------------
        # plugin checks

        if settings.value("Engine/DisableChecks", False, type=bool):
            os.environ["CARLA_DISCOVERY_NO_PROCESSING_CHECKS"] = "true"

        elif os.getenv("CARLA_DISCOVERY_NO_PROCESSING_CHECKS"):
            os.environ.pop("CARLA_DISCOVERY_NO_PROCESSING_CHECKS")

        # ---------------------------------------------
        # plugin paths

        Carla.LADSPA_PATH = toList(settings.value("Paths/LADSPA", Carla.LADSPA_PATH))
        Carla.DSSI_PATH = toList(settings.value("Paths/DSSI", Carla.DSSI_PATH))
        Carla.LV2_PATH = toList(settings.value("Paths/LV2", Carla.LV2_PATH))
        Carla.VST_PATH = toList(settings.value("Paths/VST", Carla.VST_PATH))
        Carla.GIG_PATH = toList(settings.value("Paths/GIG", Carla.GIG_PATH))
        Carla.SF2_PATH = toList(settings.value("Paths/SF2", Carla.SF2_PATH))
        Carla.SFZ_PATH = toList(settings.value("Paths/SFZ", Carla.SFZ_PATH))

        os.environ["LADSPA_PATH"] = splitter.join(Carla.LADSPA_PATH)
        os.environ["DSSI_PATH"] = splitter.join(Carla.DSSI_PATH)
        os.environ["LV2_PATH"] = splitter.join(Carla.LV2_PATH)
        os.environ["VST_PATH"] = splitter.join(Carla.VST_PATH)
        os.environ["GIG_PATH"] = splitter.join(Carla.GIG_PATH)
        os.environ["SF2_PATH"] = splitter.join(Carla.SF2_PATH)
        os.environ["SFZ_PATH"] = splitter.join(Carla.SFZ_PATH)

    def saveSettings(self):
        settings = QSettings()
        settings.setValue("Geometry", self.saveGeometry())
        settings.setValue("SplitterState", self.ui.splitter.saveState())
        settings.setValue("ShowToolbar", self.ui.toolBar.isVisible())
        settings.setValue("HorizontalScrollBarValue", self.ui.graphicsView.horizontalScrollBar().value())
        settings.setValue("VerticalScrollBarValue", self.ui.graphicsView.verticalScrollBar().value())

        diskFolders = []

        for i in range(self.ui.cb_disk.count()):
            diskFolders.append(self.ui.cb_disk.itemData(i))

        settings.setValue("DiskFolders", diskFolders)

    def dragEnterEvent(self, event):
        if event.source() == self.ui.fileTreeView:
            event.accept()
        elif self.ui.tabMain.contentsRect().contains(event.pos()):
            event.accept()
        else:
            QMainWindow.dragEnterEvent(self, event)

    def dropEvent(self, event):
        event.accept()

        urls = event.mimeData().urls()

        for url in urls:
            filename = url.toLocalFile()

            if not Carla.host.load_filename(filename):
                CustomMessageBox(self, QMessageBox.Critical, self.tr("Error"),
                                 self.tr("Failed to load file"),
                                 cString(Carla.host.get_last_error()), QMessageBox.Ok, QMessageBox.Ok)

    def resizeEvent(self, event):
        if self.ui.tabMain.currentIndex() == 0:
            # Force update of 2nd tab
            width  = self.ui.tab_plugins.width()-4
            height = self.ui.tab_plugins.height()-4
            self.ui.miniCanvasPreview.setViewSize(float(width) / DEFAULT_CANVAS_WIDTH, float(height) / DEFAULT_CANVAS_HEIGHT)
        else:
            QTimer.singleShot(0, self, SLOT("slot_miniCanvasCheckSize()"))

        self.updateInfoLabelSize()

        QMainWindow.resizeEvent(self, event)

    def timerEvent(self, event):
        if event.timerId() == self.fIdleTimerFast:
            if not self.fEngineStarted:
                return

            Carla.host.engine_idle()

            for pwidget in self.fPluginList:
                if pwidget is None:
                    break
                pwidget.idleFast()

            self.refreshTransport()

        elif event.timerId() == self.fIdleTimerSlow:
            if not self.fEngineStarted:
                return

            for pwidget in self.fPluginList:
                if pwidget is None:
                    break
                pwidget.idleSlow()

        QMainWindow.timerEvent(self, event)

    def closeEvent(self, event):
        self.saveSettings()

        if self.fEngineStarted:
            Carla.host.set_engine_about_to_close()
            self.removeAllPlugins()
            self.stopEngine()

        QMainWindow.closeEvent(self, event)

# ------------------------------------------------------------------------------------------------

def canvasCallback(action, value1, value2, valueStr):
    if action == patchcanvas.ACTION_GROUP_INFO:
        pass

    elif action == patchcanvas.ACTION_GROUP_RENAME:
        pass

    elif action == patchcanvas.ACTION_GROUP_SPLIT:
        groupId = value1
        patchcanvas.splitGroup(groupId)
        Carla.gui.ui.miniCanvasPreview.update()

    elif action == patchcanvas.ACTION_GROUP_JOIN:
        groupId = value1
        patchcanvas.joinGroup(groupId)
        Carla.gui.ui.miniCanvasPreview.update()

    elif action == patchcanvas.ACTION_PORT_INFO:
        pass

    elif action == patchcanvas.ACTION_PORT_RENAME:
        pass

    elif action == patchcanvas.ACTION_PORTS_CONNECT:
        portIdA = value1
        portIdB = value2

        if not Carla.host.patchbay_connect(portIdA, portIdB):
            print("Connection failed:", cString(Carla.host.get_last_error()))

    elif action == patchcanvas.ACTION_PORTS_DISCONNECT:
        connectionId = value1

        if not Carla.host.patchbay_disconnect(connectionId):
            print("Disconnect failed:", cString(Carla.host.get_last_error()))

def engineCallback(ptr, action, pluginId, value1, value2, value3, valueStr):
    if pluginId < 0 or not Carla.gui:
        return

    if action == CALLBACK_DEBUG:
        Carla.gui.emit(SIGNAL("DebugCallback(int, int, int, double, QString)"), pluginId, value1, value2, value3, cString(valueStr))
    elif action == CALLBACK_PLUGIN_ADDED:
        Carla.gui.emit(SIGNAL("PluginAddedCallback(int)"), pluginId)
    elif action == CALLBACK_PLUGIN_REMOVED:
        Carla.gui.emit(SIGNAL("PluginRemovedCallback(int)"), pluginId)
    elif action == CALLBACK_PLUGIN_RENAMED:
        Carla.gui.emit(SIGNAL("PluginRenamedCallback(int, QString)"), pluginId, valueStr)
    elif action == CALLBACK_PARAMETER_VALUE_CHANGED:
        Carla.gui.emit(SIGNAL("ParameterValueChangedCallback(int, int, double)"), pluginId, value1, value3)
    elif action == CALLBACK_PARAMETER_DEFAULT_CHANGED:
        Carla.gui.emit(SIGNAL("ParameterDefaultChangedCallback(int, int, double)"), pluginId, value1, value3)
    elif action == CALLBACK_PARAMETER_MIDI_CHANNEL_CHANGED:
        Carla.gui.emit(SIGNAL("ParameterMidiChannelChangedCallback(int, int, int)"), pluginId, value1, value2)
    elif action == CALLBACK_PARAMETER_MIDI_CC_CHANGED:
        Carla.gui.emit(SIGNAL("ParameterMidiCcChangedCallback(int, int, int)"), pluginId, value1, value2)
    elif action == CALLBACK_PROGRAM_CHANGED:
        Carla.gui.emit(SIGNAL("ProgramChangedCallback(int, int)"), pluginId, value1)
    elif action == CALLBACK_MIDI_PROGRAM_CHANGED:
        Carla.gui.emit(SIGNAL("MidiProgramChangedCallback(int, int)"), pluginId, value1)
    elif action == CALLBACK_NOTE_ON:
        Carla.gui.emit(SIGNAL("NoteOnCallback(int, int, int, int)"), pluginId, value1, value2, value3)
    elif action == CALLBACK_NOTE_OFF:
        Carla.gui.emit(SIGNAL("NoteOffCallback(int, int, int)"), pluginId, value1, value2)
    elif action == CALLBACK_SHOW_GUI:
        Carla.gui.emit(SIGNAL("ShowGuiCallback(int, int)"), pluginId, value1)
    elif action == CALLBACK_UPDATE:
        Carla.gui.emit(SIGNAL("UpdateCallback(int)"), pluginId)
    elif action == CALLBACK_RELOAD_INFO:
        Carla.gui.emit(SIGNAL("ReloadInfoCallback(int)"), pluginId)
    elif action == CALLBACK_RELOAD_PARAMETERS:
        Carla.gui.emit(SIGNAL("ReloadParametersCallback(int)"), pluginId)
    elif action == CALLBACK_RELOAD_PROGRAMS:
        Carla.gui.emit(SIGNAL("ReloadProgramsCallback(int)"), pluginId)
    elif action == CALLBACK_RELOAD_ALL:
        Carla.gui.emit(SIGNAL("ReloadAllCallback(int)"), pluginId)
    elif action == CALLBACK_PATCHBAY_CLIENT_ADDED:
        Carla.gui.emit(SIGNAL("PatchbayClientAddedCallback(int, int, QString)"), value1, value2, cString(valueStr))
    elif action == CALLBACK_PATCHBAY_CLIENT_REMOVED:
        Carla.gui.emit(SIGNAL("PatchbayClientRemovedCallback(int)"), value1)
    elif action == CALLBACK_PATCHBAY_CLIENT_RENAMED:
        Carla.gui.emit(SIGNAL("PatchbayClientRenamedCallback(int, QString)"), value1, cString(valueStr))
    elif action == CALLBACK_PATCHBAY_PORT_ADDED:
        Carla.gui.emit(SIGNAL("PatchbayPortAddedCallback(int, int, int, QString)"), value1, value2, int(value3), cString(valueStr))
    elif action == CALLBACK_PATCHBAY_PORT_REMOVED:
        Carla.gui.emit(SIGNAL("PatchbayPortRemovedCallback(int)"), value1)
    elif action == CALLBACK_PATCHBAY_PORT_RENAMED:
        Carla.gui.emit(SIGNAL("PatchbayPortRenamedCallback(int, QString)"), value1, cString(valueStr))
    elif action == CALLBACK_PATCHBAY_CONNECTION_ADDED:
        Carla.gui.emit(SIGNAL("PatchbayConnectionAddedCallback(int, int, int)"), value1, value2, value3)
    elif action == CALLBACK_PATCHBAY_CONNECTION_REMOVED:
        Carla.gui.emit(SIGNAL("PatchbayConnectionRemovedCallback(int)"), value1)
    elif action == CALLBACK_PATCHBAY_ICON_CHANGED:
        Carla.gui.emit(SIGNAL("PatchbayIconChangedCallback(int, int)"), value1, value2)
    elif action == CALLBACK_BUFFER_SIZE_CHANGED:
        Carla.gui.emit(SIGNAL("BufferSizeChangedCallback(int)"), value1)
    elif action == CALLBACK_SAMPLE_RATE_CHANGED:
        Carla.gui.emit(SIGNAL("SampleRateChangedCallback(double)"), value3)
    elif action == CALLBACK_NSM_ANNOUNCE:
        Carla.gui.emit(SIGNAL("NSM_AnnounceCallback(QString)"), cString(valueStr))
    elif action == CALLBACK_NSM_OPEN:
        Carla.gui.emit(SIGNAL("NSM_OpenCallback(QString)"), cString(valueStr))
    elif action == CALLBACK_NSM_SAVE:
        Carla.gui.emit(SIGNAL("NSM_SaveCallback()"))
    elif action == CALLBACK_ERROR:
        Carla.gui.emit(SIGNAL("ErrorCallback(QString)"), cString(valueStr))
    elif action == CALLBACK_QUIT:
        Carla.gui.emit(SIGNAL("QuitCallback()"))

#--------------- main ------------------
if __name__ == '__main__':
    # App initialization
    app = QApplication(sys.argv)
    app.setApplicationName("Carla")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("falkTX")
    app.setWindowIcon(QIcon(":/scalable/carla.svg"))

    argv = app.arguments()
    argc = len(argv)

    for i in range(argc):
        if i == 0: continue
        argument = argv[i]

        if argument.startswith("--with-appname="):
            appName = os.path.basename(argument.replace("--with-appname=", ""))

        elif argument.startswith("--with-libprefix="):
            libPrefix = argument.replace("--with-libprefix=", "")

        elif os.path.exists(argument):
            projectFilename = argument

    if libPrefix is not None:
        libPath = os.path.join(libPrefix, "lib", "carla")
        libName = os.path.join(libPath, carla_libname)
    else:
        libPath = carla_library_path.replace(carla_libname, "")
        libName = carla_library_path

    # Init backend
    Carla.host = Host(libName)
    Carla.host.set_engine_callback(engineCallback)

    if NSM_URL:
        Carla.host.nsm_announce(NSM_URL, appName, os.getpid())
    else:
        Carla.host.set_engine_option(OPTION_PROCESS_NAME, 0, "carla")

    Carla.host.set_engine_option(OPTION_PATH_RESOURCES, 0, libPath)

    # Set bridge paths
    if carla_bridge_native:
        Carla.host.set_engine_option(OPTION_PATH_BRIDGE_NATIVE, 0, carla_bridge_native)

    if carla_bridge_posix32:
        Carla.host.set_engine_option(OPTION_PATH_BRIDGE_POSIX32, 0, carla_bridge_posix32)

    if carla_bridge_posix64:
        Carla.host.set_engine_option(OPTION_PATH_BRIDGE_POSIX64, 0, carla_bridge_posix64)

    if carla_bridge_win32:
        Carla.host.set_engine_option(OPTION_PATH_BRIDGE_WIN32, 0, carla_bridge_win32)

    if carla_bridge_win64:
        Carla.host.set_engine_option(OPTION_PATH_BRIDGE_WIN64, 0, carla_bridge_win64)

    if WINDOWS:
        if carla_bridge_lv2_windows:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_WINDOWS, 0, carla_bridge_lv2_windows)

        if carla_bridge_vst_hwnd:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_VST_HWND, 0, carla_bridge_vst_hwnd)

    elif MACOS:
        if carla_bridge_lv2_cocoa:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_COCOA, 0, carla_bridge_lv2_cocoa)

        if carla_bridge_vst_cocoa:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_VST_COCOA, 0, carla_bridge_vst_cocoa)

    else:
        if carla_bridge_lv2_gtk2:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_GTK2, 0, carla_bridge_lv2_gtk2)

        if carla_bridge_lv2_gtk3:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_GTK3, 0, carla_bridge_lv2_gtk3)

        if carla_bridge_lv2_qt4:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_QT4, 0, carla_bridge_lv2_qt4)

        if carla_bridge_lv2_qt5:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_QT5, 0, carla_bridge_lv2_qt5)

        if carla_bridge_lv2_x11:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_LV2_X11, 0, carla_bridge_lv2_x11)

        if carla_bridge_vst_x11:
            Carla.host.set_engine_option(OPTION_PATH_BRIDGE_VST_X11, 0, carla_bridge_vst_x11)

    # Create GUI and start engine
    Carla.gui = CarlaMainW()

    # Set-up custom signal handling
    setUpSignals()

    # Show GUI
    Carla.gui.show()

    # Load project file if set
    if projectFilename and not NSM_URL:
        Carla.gui.loadProjectLater(projectFilename)

    # App-Loop
    ret = app.exec_()

    # Exit properly
    sys.exit(ret)
