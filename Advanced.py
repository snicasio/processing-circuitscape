# -*- coding: utf-8 -*-

"""
***************************************************************************
    Advanced.py
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
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFolderDestination
                      )
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import system

from processing_circuitscape.CircuitscapeAlgorithm import CircuitscapeAlgorithm
from processing_circuitscape import CircuitscapeUtils


class Advanced(CircuitscapeAlgorithm):

    RESISTANCE_MAP = "RESISTANCE_MAP"
    IS_CONDUCTANCES = "IS_CONDUCTANCES"
    CURRENT_SOURCE = "CURRENT_SOURCE"
    GROUND_POINT = "GROUND_POINT"
    GP_CONDUCTANCES = "GP_CONDUCTANCES"
    MODE = "MODE"
    UNIT_CURRENTS = "UNIT_CURRENTS"
    DIRECT_CONNECTIONS = "DIRECT_CONNECTIONS"
    WRITE_CURRENT_MAP = "WRITE_CURRENT_MAP"
    WRITE_VOLTAGE_MAP = "WRITE_VOLTAGE_MAP"
    MASK = "MASK"
    SHORT_CIRCUIT = "SHORT_CIRCUIT"
    BASENAME = "BASENAME"
    DIRECTORY = "DIRECTORY"

    def name(self):
        return "advanced"

    def displayName(self):
        return self.tr("Advanced")

    def group(self):
        return self.tr("Circuitscape")

    def groupId(self):
        return "circuitscape"

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.modes = ((self.tr("Keep both when possible"), "keepall"),
                      (self.tr("Remove source"), "rmvsrc"),
                      (self.tr("Remove ground"), "rmvgnd"),
                      (self.tr("Remove both"), "rmvall"))

        self.addParameter(QgsProcessingParameterRasterLayer(self.RESISTANCE_MAP,
                                                            self.tr("Raster resistance map")))
        self.addParameter(QgsProcessingParameterBoolean(self.IS_CONDUCTANCES,
                                                        self.tr("Data represent conductances instead of resistances"),
                                                        False))
        self.addParameter(QgsProcessingParameterRasterLayer(self.CURRENT_SOURCE,
                                                            self.tr("Current source")))
        self.addParameter(QgsProcessingParameterRasterLayer(self.GROUND_POINT,
                                                            self.tr("Ground point")))
        self.addParameter(QgsProcessingParameterBoolean(self.GP_CONDUCTANCES,
                                                        self.tr("Data represent conductances instead of resistances to ground"),
                                                        False))
        self.addParameter(QgsProcessingParameterEnum(self.MODE,
                                                     self.tr("When a source and ground are at the same node"),
                                                     options=[i[0] for i in self.modes],
                                                     allowMultiple=False,
                                                     defaultValue=0))
        self.addParameter(QgsProcessingParameterBoolean(self.UNIT_CURRENTS,
                                                        self.tr("Use unit currents (i = 1) for all current sources"),
                                                        False))
        self.addParameter(QgsProcessingParameterBoolean(self.DIRECT_CONNECTIONS,
                                                        self.tr("Use direct connections to ground (R = 0) for all ground points"),
                                                        False))
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
        self.addParameter(QgsProcessingParameterString(self.BASENAME,
                                                       self.tr("Output basename"),
                                                       "csoutput"))

        self.addParameter(QgsProcessingParameterFolderDestination(self.DIRECTORY,
                                                                  self.tr("Output directory")))

    def processAlgorithm(self, parameters, context, feedback):
        resistance = self.parameterAsRasterLayer(parameters, self.RESISTANCE_MAP, context).source()
        useConductance = str(not self.parameterAsBool(parameters, self.IS_CONDUCTANCES, context))
        currentSources = self.parameterAsRasterLayer(parameters, self.CURRENT_SOURCE, context).source()
        groundPoints = self.parameterAsRasterLayer(parameters, self.GROUND_POINT, context)
        gpConductance = str(not self.parameterAsBool(parameters, self.GP_CONDUCTANCES, context))
        writeCurrent = str(self.parameterAsBool(parameters, self.WRITE_CURRENT_MAP, context))
        writeVoltage = str(self.parameterAsBool(parameters, self.WRITE_VOLTAGE_MAP, context))

        # advanced parameters
        mode = self.modes[self.parameterAsEnum(parameters, self.MODE, context)][1]
        unitCurrents = str(self.parameterAsBool(parameters, self.UNIT_CURRENTS, context))
        directConnections = str(self.parameterAsBool(parameters, self.DIRECT_CONNECTIONS, context))
        mask = self.parameterAsRasterLayer(parameters, self.MASK, context)
        shortCircuit = self.parameterAsRasterLayer(parameters, self.SHORT_CIRCUIT, context)

        baseName = self.parameterAsString(parameters, self.BASENAME, context)
        directory = self.parameterAsString(parameters, self.DIRECTORY, context)
        basePath = os.path.join(directory, baseName)

        commands = self.prepareInputs(parameters, context)

        iniPath = CircuitscapeUtils.writeConfiguration()
        cfg = configparser.ConfigParser()
        cfg.read(iniPath)

        # set parameters
        cfg["Circuitscape mode"]["scenario"] = "advanced"

        section = cfg["Habitat raster or graph"]
        section["habitat_map_is_resistances"] = useConductance
        if resistance in self.exportedLayers.keys():
            section["habitat_file"] = self.exportedLayers[resistance]

        section = cfg["Options for advanced mode"]
        if currentSources in self.exportedLayers.keys():
            section["source_file"] = self.exportedLayers[currentSources]

        if groundPoints in self.exportedLayers.keys():
            section["ground_file"] = self.exportedLayers[groundPoints]

        section["ground_file_is_resistances"] = gpConductance
        section["remove_src_or_gnd"] = unitCurrents
        section["use_direct_grounds"] = directConnections

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
