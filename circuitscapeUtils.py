# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeUtils.py
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
import stat
import tempfile
import subprocess
import configparser

from qgis.core import Qgis, QgsMessageLog, QgsProcessingFeedback, QgsProcessingUtils
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig

from processing.tools.system import isWindows

CIRCUITSCAPE_ACTIVE = "CIRCUITSCAPE_ACTIVE"
CIRCUITSCAPE_DIRECTORY = "CIRCUITSCAPE_DIRECTORY"
CIRCUITSCAPE_VERBOSE = "CIRCUITSCAPE_VERBOSE"

FOUR_NEIGHBOURS = "FOUR_NEIGHBOURS"
AVERAGE_CONDUCTANCE = "AVERAGE_CONDUCTANCE"
PREEMPT_MEMORY = "PREEMPT_MEMORY"
MAX_CURRENT_MAPS = "MAX_CURRENT_MAPS"
CUM_MAX_MAPS = "CUM_MAX_MAPS"
ZERO_FOCAL = "ZERO_FOCAL"
COMPRESS_OUTPUT = "COMPRESS_OUTPUT"
LOG_TRANSFORM = "LOG_TRANSFORM"


def circuitscapeDirectory():
    filePath = ProcessingConfig.getSetting(CIRCUITSCAPE_DIRECTORY)
    return filePath if filePath is not None else ""


def writeConfiguration():
    cfg = configparser.ConfigParser()

    cfg["Options for advanced mode"] = {}
    section = cfg["Options for advanced mode"]
    section["ground_file_is_resistances"] = "True"
    section["remove_src_or_gnd"] = "keepall"
    section["ground_file"] = ""
    section["use_unit_currents"] = "False"
    section["source_file"] = ""
    section["use_direct_grounds"] = "False"

    cfg["Mask file"] = {}
    section = cfg["Mask file"]
    section["mask_file"] = ""
    section["use_mask"] = "False"

    cfg["Calculation options"] = {}
    section = cfg["Calculation options"]
    section["low_memory_mode"] = "False"
    section["parallelize"] = "False"
    section["solver"] = "cg+amg"
    section["print_timings"] = "True"
    section["preemptive_memory_release"] = str(ProcessingConfig.getSetting(PREEMPT_MEMORY))
    section["print_rusages"] = "False"
    section["max_parallel"] = "0"

    cfg["Short circuit regions (aka polygons)"] = {}
    section = cfg["Short circuit regions (aka polygons)"]
    section["polygon_file"] = ""
    section["use_polygons"] = "False"

    cfg["Options for one-to-all and all-to-one modes"] = {}
    section = cfg["Options for one-to-all and all-to-one modes"]
    section["use_variable_source_strengths"] = "False"
    section["variable_source_file"] = ""

    cfg["Output options"] = {}
    section = cfg["Output options"]
    section["set_null_currents_to_nodata"] = "False"
    section["set_focal_node_currents_to_zero"] = str(ProcessingConfig.getSetting(ZERO_FOCAL))
    section["set_null_voltages_to_nodata"] = "False"
    section["compress_grids"] = str(ProcessingConfig.getSetting(COMPRESS_OUTPUT))
    section["write_cur_maps"] = "True"
    section["write_volt_maps"] = "True"
    section["output_file"] = ""
    section["write_cum_cur_map_only"] = str(ProcessingConfig.getSetting(CUM_MAX_MAPS))
    section["log_transform_maps"] = str(ProcessingConfig.getSetting(LOG_TRANSFORM))
    section["write_max_cur_maps"] = str(ProcessingConfig.getSetting(MAX_CURRENT_MAPS))

    cfg["Options for reclassification of habitat data"] = {}
    section = cfg["Options for reclassification of habitat data"]
    section["reclass_file"] = ""
    section["use_reclass_table"] = "False"

    cfg["Logging Options"] = {}
    section = cfg["Logging Options"]
    section["log_level"] = "INFO"
    section["log_file"] = "None"
    section["profiler_log_file"] = "None"
    section["screenprint_log"] = "False"

    cfg["Options for pairwise and one-to-all and all-to-one modes"] = {}
    section = cfg["Options for pairwise and one-to-all and all-to-one modes"]
    section["included_pairs_file"] = ""
    section["use_included_pairs"] = "False"
    section["point_file"] = ""

    cfg["Connection scheme for raster habitat data"] = {}
    section = cfg["Connection scheme for raster habitat data"]
    section["connect_using_avg_resistances"] = str(ProcessingConfig.getSetting(AVERAGE_CONDUCTANCE))
    section["connect_four_neighbors_only"] = str(ProcessingConfig.getSetting(FOUR_NEIGHBOURS))

    cfg["Habitat raster or graph"] = {}
    section = cfg["Habitat raster or graph"]
    section["habitat_map_is_resistances"] = "True"
    section["Habitat raster or graph"] = "habitat_file"

    cfg["Circuitscape mode"] = {}
    section["data_type"] = "raster"
    section["scenario"] = ""

    iniPath = QgsProcessingUtils.generateTempFilename("circuitscape.ini")
    with open(iniPath, "w") as f:
        cfg.write(f)

    return iniPath


def jobFile():
    if isWindows():
        fileName = "circuitscape_job.bat"
    else:
        fileName = "circuitscape_job.sh"

    return os.path.join(tempfile.gettempdir(), fileName)


def jobFileFromCommands(commands):
    with open(jobFile(), "w") as f:
        for command in commands:
            f.write("{}\n".format(command))

        f.write("exit")


def execute(feedback):
    if isWindows():
        commands = ["cmd.exe", "/C", batchJobFilename()]
    else:
        os.chmod(jobFile(), stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
        commands = [jobFile()]

    fused_command = " ".join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, "Processing", Qgis.Info)
    feedback.pushInfo("Circuitscape command:")
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo("Circuitscape command output:")

    loglines = []
    with subprocess.Popen(fused_command,
                          shell=True,
                          stdout=subprocess.PIPE,
                          stdin=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True) as proc:
        try:
            for line in iter(proc.stdout.readline, ""):
                feedback.pushConsoleInfo(line)
                loglines.append(line)
        except:
            pass

    if ProcessingConfig.getSetting(CIRCUITSCAPE_VERBOSE):
        QgsMessageLog.logMessage("\n".join(loglines), "Processing", Qgis.Info)
