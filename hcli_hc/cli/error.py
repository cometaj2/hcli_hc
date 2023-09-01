import re
import logger

messages = {
    "error:1" : "G-code words consist of a letter and a value. Letter was not found.",
    "error:2" : "Missing the expected G-code word value or numeric value format is not valid.",
    "error:3" : "Grbl ‘$’ system command was not recognized or supported.",
    "error:4" : "Negative value received for an expected positive value.",
    "error:5" : "Homing cycle failure. Homing is not enabled via settings.",
    "error:6" : "Minimum step pulse time must be greater than 3usec.",
    "error:7" : "An EEPROM read failed. Auto-restoring affected EEPROM to default values.",
    "error:8" : "Grbl ‘$’ command cannot be used unless Grbl is IDLE. Ensures smooth operation during a job.",
    "error:9" : "G-code commands are locked out during alarm or jog state.",
    "error:10" : "Soft limits cannot be enabled without homing also enabled.",
    "error:11" : "Max characters per line exceeded. Received command line was not executed.",
    "error:12" : "Grbl ‘$’ setting value cause the step rate to exceed the maximum supported.",
    "error:13" : "Safety door detected as opened and door state initiated.",
    "error:14" : "Build info or startup line exceeded EEPROM line length limit. Line not stored.",
    "error:15" : "Jog target exceeds machine travel. Jog command has been ignored.",
    "error:16" : "Jog command has no ‘:’ or contains prohibited g-code.",
    "error:17" : "Laser mode requires PWM output.",
    "error:20" : "Unsupported or invalid g-code command found in block.",
    "error:21" : "More than one g-code command from same modal group found in block.",
    "error:22" : "Feed rate has not yet been set or is undefined.",
    "error:23" : "G-code command in block requires an integer value.",
    "error:24" : "More than one g-code command that requires axis words found in block.",
    "error:25" : "Repeated g-code word found in block.",
    "error:26" : "No axis words found in block for g-code command or current modal state which requires them.",
    "error:27" : "Line number value is invalid.",
    "error:28" : "G-code command is missing a required value word.",
    "error:29" : "G59.x work coordinate systems are not supported.",
    "error:30" : "G53 only allowed with G0 and G1 motion modes.",
    "error:31" : "Axis words found in block when no command or current modal state uses them.",
    "error:32" : "G2 and G3 arcs require at least one in-plane axis word.",
    "error:33" : "Motion command target is invalid.",
    "error:34" : "Arc radius value is invalid.",
    "error:35" : "G2 and G3 arcs require at least one in-plane offset word.",
    "error:36" : "Unused value words found in block.",
    "error:37" : "G43.1 dynamic tool length offset is not assigned to configured tool length axis.",
    "error:38" : "Tool number greater than max supported value."
}

logging = logger.Logger()


def match(message):
    error_msg = re.search(r'error:\d+', message)
    if error_msg:
        logging.info(message + " " + messages[error_msg.group()])
        return True
    else:
        return False
