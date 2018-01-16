# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeProvider.py
    ---------------------
    Date                 : May 2014
    Copyright            : (C) 2014-2018 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'May 2014'
__copyright__ = '(C) 2014-2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import QgsProcessingProvider

from processing.core.ProcessingConfig import ProcessingConfig, Setting
from processing.tools.system import isWindows

from processing_circuitscape.Pairwise import Pairwise
from processing_circuitscape.OneToAll import OneToAll
from processing_circuitscape.Advanced import Advanced
from processing_circuitscape import CircuitscapeUtils

pluginPath = os.path.dirname(__file__)


class CircuitscapeProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        return "circuitscape"

    def name(self):
        return "Circuitscape"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "circuitscape.png"))

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()

        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.CIRCUITSCAPE_ACTIVE,
                                            self.tr("Activate"),
                                            False))
        if isWindows():
            ProcessingConfig.addSetting(Setting(self.name(),
                                                CircuitscapeUtils.CIRCUITSCAPE_DIRECTORY,
                                                self.tr("Circuitscape directory"),
                                                CircuitscapeUtils.circuitscapeDirectory(),
                                                valuetype=Setting.FOLDER))

        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.CIRCUITSCAPE_VERBOSE,
                                            self.tr("Log commands output"),
                                            False))

        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.FOUR_NEIGHBOURS,
                                            self.tr("Connect raster cells to 4 neighbors instead of 8"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.AVERAGE_CONDUCTANCE,
                                            self.tr("Use average conductance instead of resistance for connections between cells"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.PREEMPT_MEMORY,
                                            self.tr("Preemptively release memory when possible"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.MAX_CURRENT_MAPS,
                                            self.tr("Write maximum of current maps"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.CUM_MAX_MAPS,
                                            self.tr("Write cumulative & maximum current maps only"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.ZERO_FOCAL,
                                            self.tr("Set focal nodes currents to zero"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.LOG_TRANSFORM,
                                            self.tr("Log-transform current maps"),
                                            False))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            CircuitscapeUtils.COMPRESS_OUTPUT,
                                            self.tr("Compress output grids"),
                                            False))

        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(CircuitscapeUtils.CIRCUITSCAPE_ACTIVE)
        if isWindows():
            ProcessingConfig.removeSetting(CircuitscapeUtils.CIRCUITSCAPE_DIRECTORY)
        ProcessingConfig.removeSetting(CircuitscapeUtils.CIRCUITSCAPE_VERBOSE)

        ProcessingConfig.removeSetting(CircuitscapeUtils.FOUR_NEIGHBOURS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.AVERAGE_CONDUCTANCE)
        ProcessingConfig.removeSetting(CircuitscapeUtils.PREEMPT_MEMORY)
        ProcessingConfig.removeSetting(CircuitscapeUtils.MAX_CURRENT_MAPS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.CUM_MAX_MAPS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.ZERO_FOCAL)
        ProcessingConfig.removeSetting(CircuitscapeUtils.LOG_TRANSFORM)
        ProcessingConfig.removeSetting(CircuitscapeUtils.COMPRESS_OUTPUT)

    def isActive(self):
        return ProcessingConfig.getSetting(CircuitscapeUtils.CIRCUITSCAPE_ACTIVE)

    def setActive(self, active):
        ProcessingConfig.setSettingValue(CircuitscapeUtils.CIRCUITSCAPE_ACTIVE, active)

    def supportsNonFileBasedOutput(self):
        return False

    def getAlgs(self):
        algs = [Pairwise(),
                OneToAll(),
                Advanced()
               ]

        return algs

    def loadAlgorithms(self):
        self.algs = self.getAlgs()
        for a in self.algs:
            self.addAlgorithm(a)

    def tr(self, string, context=''):
        if context == "":
            context = "CircuitscapeProvider"
        return QCoreApplication.translate(context, string)
