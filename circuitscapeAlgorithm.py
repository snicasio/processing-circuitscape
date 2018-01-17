# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeAlgorithm.py
    ---------------------
    Date                 : June 2014
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
__date__ = 'June 2014'
__copyright__ = '(C) 2014-2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterRasterLayer
                      )

pluginPath = os.path.dirname(__file__)

sessionExportedLayers = {}


class CircuitscapeAlgorithm(QgsProcessingAlgorithm):

    def __init__(self):
        super().__init__()

    def createInstance(self):
        return type(self)()

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "circuitscape.png"))

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)

    def exportRasterLayer(self, source):
        global sessionExportedLayers

        if source in sessionExportedLayers:
            self.exportedLayers[source] = sessionExportedLayers[source]
            return None

        fileName = os.path.basename(source)
        validChars = \
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        fileName = ''.join(c for c in fileName if c in validChars)
        if len(fileName) == 0:
            fileName = 'layer'

        destFilename = QgsProcessingUtils.generateTempFilename("{}.asc".format(fileName))
        self.exportedLayers[source] = destFilename
        sessionExportedLayers[source] = destFilename

        return "gdal_translate -of AAIGrid {} {}".format(source, destFilename)

    def prepareInputs(self, parameters, context):
        commands = []
        self.exportedLayers = {}
        for param in self.parameterDefinitions():
            if isinstance(param, QgsProcessingParameterRasterLayer):
                layer = self.parameterAsRasterLayer(parameters, param.name(), context)
                if layer is None:
                    continue
                if not layer.source().lower().endswith("asc"):
                    exportCommand = self.exportRasterLayer(layer.source())
                    if exportCommand is not None:
                        commands.append(exportCommand)
        return commands
