# -*- coding: utf-8 -*-

"""
***************************************************************************
    Pairwise.py
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
import configparser

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFolderDestination
                      )
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import system

from processing_circuitscape.CircuitscapeAlgorithm import CircuitscapeAlgorithm
from processing_circuitscape import CircuitscapeUtils


class Pairwise(CircuitscapeAlgorithm):

    RESISTANCE_MAP = "RESISTANCE_MAP"
    IS_CONDUCTANCES = "IS_CONDUCTANCES"
    FOCAL_NODE = "FOCAL_NODE"
    WRITE_CURRENT_MAP = "WRITE_CURRENT_MAP"
    WRITE_VOLTAGE_MAP = "WRITE_VOLTAGE_MAP"
    MASK = "MASK"
    SHORT_CIRCUIT = "SHORT_CIRCUIT"
    EXCLUDE_INCLUDE = "EXCLUDE_INCLUDE"
    LOW_MEMORY = "LOW_MEMORY"
    BASENAME = "BASENAME"
    DIRECTORY = "DIRECTORY"

    def name(self):
        return "pairwise"

    def displayName(self):
        return self.tr("Pairwise")

    def group(self):
        return self.tr("Circuitscape")

    def groupId(self):
        return "circuitscape"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.RESISTANCE_MAP,
                                                            self.tr("Resistance map")))
        self.addParameter(QgsProcessingParameterBoolean(self.IS_CONDUCTANCES,
                                                        self.tr("Data represent conductances instead of resistances"),
                                                        False))
        self.addParameter(QgsProcessingParameterRasterLayer(self.FOCAL_NODE,
                                                            self.tr("Focal node location")))
        self.addParameter(QgsProcessingParameterBoolean(self.WRITE_CURRENT_MAP,
                                                        self.tr("Create current map"),
                                                        True))
        self.addParameter(QgsProcessingParameterBoolean(self.WRITE_VOLTAGE_MAP,
                                                        self.tr("Create voltage map"),
                                                        True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.MASK,
                                                            self.tr("Mask raster"),
                                                            optional=True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.SHORT_CIRCUIT,
                                                            self.tr("Short-circuit region"),
                                                            optional=True))
        self.addParameter(QgsProcessingParameterRasterLayer(self.EXCLUDE_INCLUDE,
                                                            self.tr("Focal node pairs to exclude/include"),
                                                            optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.LOW_MEMORY,
                                                        self.tr("Run in low memory mode"),
                                                        False))
        self.addParameter(QgsProcessingParameterString(self.BASENAME,
                                                       self.tr("Output basename"),
                                                       "csoutput"))

        self.addParameter(QgsProcessingParameterFolderDestination(self.DIRECTORY,
                                                                  self.tr("Output directory")))

    def processAlgorithm(self, parameters, context, feedback):
        resistance = self.parameterAsRasterLayer(parameters, self.RESISTANCE_MAP, context).source()
        useConductance = str(not self.parameterAsBool(parameters, self.IS_CONDUCTANCES, context))
        focal = self.parameterAsRasterLayer(parameters, self.FOCAL_NODE, context).source()
        writeCurrent = str(self.parameterAsBool(parameters, self.WRITE_CURRENT_MAP, context))
        writeVoltage = str(self.parameterAsBool(parameters, self.WRITE_VOLTAGE_MAP, context))

        # advanced parameters
        mask = self.parameterAsRasterLayer(parameters, self.MASK, context)
        shortCircuit = self.parameterAsRasterLayer(parameters, self.SHORT_CIRCUIT, context)
        focalPairs = self.parameterAsRasterLayer(parameters, self.EXCLUDE_INCLUDE, context)
        lowMemory = str(self.parameterAsBool(parameters, self.LOW_MEMORY, context))

        baseName = self.parameterAsString(parameters, self.BASENAME, context)
        directory = self.parameterAsString(parameters, self.DIRECTORY, context)
        basePath = os.path.join(directory, baseName)

        commands = self.prepareInputs(parameters, context)

        iniPath = CircuitscapeUtils.writeConfiguration()
        cfg = configparser.ConfigParser()
        cfg.read(iniPath)

        # set parameters
        cfg["Circuitscape mode"]["scenario"] = "pairwise"

        section = cfg["Habitat raster or graph"]
        section["habitat_map_is_resistances"] = useConductance
        if resistance in self.exportedLayers.keys():
            section["habitat_file"] = self.exportedLayers[resistance]

        if focal in self.exportedLayers.keys():
            section = cfg["Options for pairwise and one-to-all and all-to-one modes"]
            section["point_file"] = self.exportedLayers[focal]

        if focalPairs is not None:
            section["included_pairs_file"] = focalPairs
            section["use_included_pairs"] = "True"

        if mask is not None:
            if mask in self.exportedLayers.keys():
                section = cfg["Mask file"]
                section["mask_file"] = self.exportedLayers[mask]
                section["use_mask"] = "True"

        if shortCircuit is not None:
            if shortCircuit in self.exportedLayers.keys():
                section = cfg["Short circuit regions (aka polygons)"]
                section["polygon_file"] = self.exportedLayers[shortCircuit]
                section["use_polygons"] = "True"

        cfg["Calculation options"]["low_memory_mode"] = lowMemory
        cfg["Output options"]["write_cur_maps"] = writeCurrent
        cfg["Output options"]["write_volt_maps"] = writeVoltage
        cfg["Output options"]["output_file"] = basePath

        # write configuration back to the file
        with open(iniPath, "w") as f:
            cfg.write(f)

        if system.isWindows():
            csPath = CircuitscapeUtils.circuitscapeDirectory()
            if csPath == "":
                csPath = "cs_run.exe"
            else:
                csPath = os.path.join(csPath, "cs_run.exe")

            commands.append('"{}" {}'.format(csPath, iniPath))
        else:
            commands.append("csrun.py {}".format(iniPath))

        CircuitscapeUtils.jobFileFromCommands(commands)
        CircuitscapeUtils.execute(feedback)
