#!/usr/bin/python3

# This file is part of the hid_bootloader_console_client distribution
# (https: // github.com/nimo-labs/hid_bootloader_console_client).
# Copyright(c) 2021 Nimolabs Ltd. www.nimo.uk
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see < http: // www.gnu.org/licenses/>.


import json
import os
import sys
from sys import exit
import platform
import shutil

# setting these to True inhibits generation of the corrisponding default target
inhibDefaultTgtMain = False
inhibDefaultTgtReset = False
inhibDefaultTgtChipErase = False
inhibDefaultTgtSize = False
inhibDefaultTgtClean = False
inhibDefaultTgtProgram = False
projectLinkerFile = False


def WORKING_DIR():
    return "umake"


def DEP_FILE():
    return "depfile"


def processLibs(umakefileJson, makefileHandle, depfileHandle):
    for lib in umakefileJson["libraries"]:
        currentLib = lib["libName"]
        print("Processing library: %s" % currentLib)

        if "checkout" in lib:
            cmd = "git clone --quiet  %s" % lib["libPath"]
        else:
            cmd = "git clone --quiet --depth 1 %s" % lib["libPath"]

        print(cmd)
        if 0 != os.system(cmd):
            # We've already cloned the repo, so check for updates
            os.chdir(currentLib)
            os.system("git pull")
            os.chdir("..")

        # Check to see if umakefile specifies a checkout hash
        if "checkout" in lib:
            os.chdir(currentLib)
            os.system("git checkout %s" % lib["checkout"])
            os.chdir("..")

        # Check to see if umkaefile specifies a checkout branch
        if "branch" in lib:
            os.chdir(currentLib)
            cmd = "git checkout -b %s" % lib["branch"]
            # print(cmd)
            os.system(cmd)

            # Make sure we get the latest branch commits
            # os.system("git reset --hard origin/" + lib["branch"])
            cmd = "git fetch origin " + lib["branch"]
            # print(cmd)
            os.system(cmd)

            os.system("git reset --hard FETCH_HEAD")
            os.chdir("..")

        os.chdir(currentLib)
        makefileHandle.write("# %s: books\n" % currentLib)

        for book in lib["books"]:
            currentBook = book
            os.chdir(currentBook)
            print("Processing book: %s/%s" % (currentLib, currentBook))
            bookHandle = open(currentBook+".json", 'r')
            bookJson = json.load(bookHandle)

            if bookJson['book'] != currentBook:
                print("Book: %s doesn't match current book: %s" %
                      (bookJson['book'], currentBook))
                exit()
            makefileHandle.write("# %s include path\n" % currentBook)
            makefileHandle.write(
                "INCLUDES += -I ./umake/%s/%s/\n" % (currentLib, currentBook))
            if "files" in bookJson:
                for files in bookJson['files']:
                    makefileHandle.write("# %s source files\n" % currentBook)
                    if files["language"] == 'c':
                        makefileHandle.write(
                            "SRCS += ./umake/%s/%s/%s\n" % (currentLib, currentBook, files["fileName"]))
                        depfileHandle.write(
                            "./build/%s.o: ./umake/%s/%s/%s\n" % (files["fileName"][:-2], currentLib, currentBook, files["fileName"]))
                        depfileHandle.write("\t$(UMAKE_MAKEC)\n")
                    elif files["language"] == 'cpp':
                        makefileHandle.write(
                            "CPPSRCS += ./umake/%s/%s/%s\n" % (currentLib, currentBook, files["fileName"]))
                    elif files["language"] == 'asm':
                        makefileHandle.write(
                            "ARCS += ./umake/%s/%s/%s\n" % (currentLib, currentBook, files["fileName"]))
                    else:
                        print("Unknown language for %s/%s/%s" %
                              (currentLib, currentBook, files['fileName']))
                    if "cflags" in bookJson:
                        makefileHandle.write("# Book CFLAGS\n")
                        for cflags in bookJson["cflags"]:
                            makefileHandle.write("CFLAGS += %s\n" % cflags)

                    if "ldflags" in bookJson:
                        makefileHandle.write("# Book LDFLAGS\n")
                        for ldflags in bookJson["ldflags"]:
                            makefileHandle.write(
                                "LDFLAGS += %s\n" % ldflags)

            makefileHandle.write("\n")

            bookHandle.close()
            os.chdir("..")
        os.chdir("..")


def processUc(umakefileJson, makefileHandle, depfileHandle):
    microcontroller = umakefileJson['microcontroller']
    restoreDir = os.getcwd()
    os.chdir("nimolib/uC")

    uCHandle = open("uc_"+microcontroller+"-linux-gcc.json", 'r')
    uCJson = json.load(uCHandle)

    if uCJson['microcontroller'] != microcontroller:
        print("Microcontroller: %s doesn't match requested: %s" %
              (uCJson['microcontroller'], microcontroller))
        exit()
    makefileHandle.write("# Microcontroller defines\n")
    for uCDefines in uCJson["defines"]:
        makefileHandle.write("DEFINES += -D %s\n" % uCDefines)

    makefileHandle.write("\n# Microcontroller CFLAGS\n")
    for uCCflags in uCJson["cflags"]:
        makefileHandle.write("CFLAGS += %s\n" % uCCflags)
    makefileHandle.write("\n# Microcontroller LDFLAGS\n")

    for uCLdflags in uCJson["ldflags"]:
        makefileHandle.write("LDFLAGS += %s\n" % uCLdflags)

    if False == projectLinkerFile:
        makefileHandle.write("\n# Linker file\n")
        makefileHandle.write("LDFLAGS += -Wl,--script=%s\n" %
                             uCJson['linkerFile'])


# supportFiles superseeds startupFiles
    if "supportFiles" in uCJson:
        makefileHandle.write("\n# Support files\n")
        for uCSupportFiles in uCJson["supportFiles"]:
            filename, fileExt = os.path.splitext(uCSupportFiles)
            if ".c" == fileExt:
                makefileHandle.write("SRCS += %s\n" % uCSupportFiles)
            if ".cpp" == fileExt:
                makefileHandle.write("CPPSRCS += %s\n" % uCSupportFiles)
            elif ".S" == fileExt:
                makefileHandle.write("ASRCS += %s\n" % uCSupportFiles)
            elif ".s" == fileExt:
                makefileHandle.write("ASRCS += %s\n" % uCSupportFiles)
            elif ".asm" == fileExt:
                makefileHandle.write("ASRCS += %s\n" % uCSupportFiles)

            startupFnLst = uCSupportFiles.split('/')
            startupFn = startupFnLst[len(startupFnLst)-1]
            depfileHandle.write(
                "./build/%s.o: ./%s\n" % (startupFn[:-2], uCSupportFiles))
            depfileHandle.write("\t$(UMAKE_MAKEC)\n")
    else:
        # This can probably be removed once supportFiles is implemented
        print("Warning: The startupFile entry in uC books has been deprecated, use supportFiles instead")
        makefileHandle.write("\n# Startup file\n")
        makefileHandle.write("SRCS += %s\n" % uCJson['startupFile'])
        startupFnLst = uCJson['startupFile'].split('/')
        startupFn = startupFnLst[len(startupFnLst)-1]
        depfileHandle.write(
            "./build/%s.o: ./%s\n" % (startupFn[:-2], uCJson['startupFile']))
        depfileHandle.write("\t$(UMAKE_MAKEC)\n")

    os.chdir(restoreDir)


def writeBoilerPlate(makefileHandle):
    makefileHandle.write("""CFLAGS += $(INCLUDES) $(DEFINES)
AASRCS = $(subst .s,.S, $(notdir $(ASRCS)))
ABSRCS = $(subst .asm,.S, $(notdir $(AASRCS)))

OBJS = $(addprefix $(BUILD)/, $(subst .c,.o, $(notdir $(SRCS))))
OBJS += $(addprefix $(BUILD)/, $(subst .S,.o, $(notdir $(ABSRCS))))
OBJS += $(addprefix $(BUILD)/, $(subst .cpp,.o, $(notdir $(CPPSRCS))))

define UMAKE_MAKEC
@echo CC $@
@${CC}  $(CPPFLAGS) $(CFLAGS) -c $< -o $(addprefix ${BUILD}/, $(notdir $@))
endef

define UMAKE_MAKECPP
@echo CPP $@
@${CPP}  $(CPPFLAGS) $(CFLAGS) -c $< -o $(addprefix ${BUILD}/, $(notdir $@))
endef


$(BUILD)/$(BIN).elf: $(OBJS)
	@echo LD $@
	@$(CC) $(LDFLAGS) $(addprefix ${BUILD}/, $(notdir ${OBJS})) $(LIBS) -o $@

$(BUILD)/$(BIN).hex: $(BUILD)/$(BIN).elf
	@echo OBJCOPY $@
	@$(OBJCOPY) -O ihex $^ $@

$(BUILD)/$(BIN).bin: $(BUILD)/$(BIN).elf
	@echo OBJCOPY $@
	@$(OBJCOPY) -O binary $^ $@""")


def defaultTgtMain():
    makefileHandle.write(
        "_all: $(BUILD)/$(BIN).hex $(BUILD)/$(BIN).bin size")


def defaultTgtReset():
    makefileHandle.write(
        """
reset: $(BUILD)/$(BIN).hex
	killall -s 9 openocd || true
	openocd -d1 -f ./openocd.cfg -c init -c \"reset\" -c \"exit\"""")


def defaultTgtChipErase():
    makefileHandle.write(
            """
chiperase:
	killall -s 9 openocd || true
	openocd -d1 -f ./openocd.cfg -c init -c \"at91samd chip-erase\" -c \"exit\"""")


def defaultTgtSize():
    makefileHandle.write(
        """
size: $(BUILD)/$(BIN).elf
	@echo size:
	@$(SIZE) -t $^""")


def defaultTgtClean():
    if "Linux" == platform.system():
        makefileHandle.write(
            """
clean:
\t@echo clean
\tfind ./build ! -name 'depfile' -type f -exec rm -f {} +
\t@-rm -rf ../*~""")
    else:
        makefileHandle.write(
            """
clean:
	@echo clean
	find ./build ! -name 'depfile' -type f -exec del -Force -Recurse {} +
	@-del -Force -Recurse ../*~""")


def defaultTgtProgram():
    makefileHandle.write(
        """
program: all
	hidBoot w 0x3000 $(BUILD)/$(BIN).bin""")


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


def umakeClean(umakefileJson):
    os.system("make clean")
    if "Windows" == platform.system():
        shutil.rmtree(WORKING_DIR(), onerror=remove_readonly)
        shutil.rmtree(umakefileJson["buildDir"], onerror=remove_readonly)
        shutil.rmtree("./Makefile", onerror=remove_readonly)
    else:
        shutil.rmtree(WORKING_DIR())
        shutil.rmtree(umakefileJson["buildDir"])
        os.remove("./Makefile")


# MAIN
try:
    handle = open('./umakefile', 'r')
except:
    print("./umakefile not found.")
    exit(0)

try:
    umakefileJson = json.load(handle)
except:
    print("JSON load failed.")
    exit(0)

try:
    os.makedirs(WORKING_DIR(), exist_ok=True)
except OSError:
    print("Creation of the directory %s failed" % WORKING_DIR())

if(len(sys.argv) > 1):
    # We have command line args
    if "clean" == sys.argv[1]:
        umakeClean(umakefileJson)
        exit(0)

makefileHandle = open('Makefile', 'w')
makefileHandle.write(
    '# File autogenerated by umake, DO NOT hand edit. Changes will be overwritten\n')

# Create build directory
buildDir = umakefileJson['buildDir']
try:
    os.makedirs(buildDir, exist_ok=True)
except OSError:
    print("Creation of the directory %s failed" % buildDir)

depfileHandle = open(buildDir+"/"+DEP_FILE(), 'w')
depfileHandle.write(
    '# File autogenerated by umake, DO NOT hand edit. Changes will be overwritten\n\n')

os.chdir(WORKING_DIR())

# Process libraries
processLibs(umakefileJson, makefileHandle, depfileHandle)

# Add phony statement
makefileHandle.write("\n.PHONY: all clean size\n")
# Add build dir
makefileHandle.write("\nBUILD = %s\n" % buildDir)
# Add binary filename
makefileHandle.write("BIN = %s\n\n" % umakefileJson['target'])

# Add project level sources
makefileHandle.write("# Project sources\n")
makefileHandle.write("# C sources\n")
for projSources in umakefileJson["c_sources"]:
    rawFileName = os.path.basename(projSources)
    filename, fileExt = os.path.splitext(projSources)

    if ".c" == fileExt:
        makefileHandle.write("SRCS += %s\n" % projSources)
        rawFileName = rawFileName[:-2]
        depfileHandle.write("./build/"+rawFileName+".o: "+projSources+"\n")
        depfileHandle.write("\t$(UMAKE_MAKEC)\n")
    elif ".S" == fileExt:
        makefileHandle.write("ASRCS += %s\n" % projSources)
        rawFileName = rawFileName[:-2]
        depfileHandle.write("./build/"+rawFileName+".o: "+projSources+"\n")
        depfileHandle.write("\t$(UMAKE_MAKEC)\n")
    elif ".asm" == fileExt:
        makefileHandle.write("ASRCS += %s\n" % projSources)
        rawFileName = rawFileName[:-4]
        depfileHandle.write("./build/"+rawFileName+".o: "+projSources+"\n")
        depfileHandle.write("\t$(UMAKE_MAKEC)\n")
    elif ".cpp" == fileExt:
        makefileHandle.write("CPPSRCS += %s\n" % projSources)
        rawFileName = rawFileName[:-4]
        depfileHandle.write("./build/"+rawFileName+".o: "+projSources+"\n")
        depfileHandle.write("\t$(UMAKE_MAKECPP)\n")

makefileHandle.write("\n")


makefileHandle.write("# Project include directories\n")
for projIncludes in umakefileJson["includes"]:
    makefileHandle.write("INCLUDES += -I %s" % projIncludes)
    makefileHandle.write("\n")
makefileHandle.write("\n\n")

# Project level compiler defines
if "defines" in umakefileJson:
    makefileHandle.write("# Project level compiler defines\n")
    for defines in umakefileJson["defines"]:
        makefileHandle.write("DEFINES += %s\n" % defines)
    makefileHandle.write("\n")

# Project level LD FLAGS
if "ldflags" in umakefileJson:
    makefileHandle.write("# Project level linker flags\n")
    for ldFlags in umakefileJson["ldflags"]:
        makefileHandle.write("LDFLAGS += %s\n" % ldFlags)
    makefileHandle.write("\n")

# Custom linker file
if "linkerFile" in umakefileJson:
    projectLinkerFile = True
    makefileHandle.write("# custom linkerfile\n")
    makefileHandle.write("LDFLAGS += -Wl,--script=%s\n" %
                         umakefileJson["linkerFile"])
    makefileHandle.write("\n")

# Process microcontroller
processUc(umakefileJson, makefileHandle, depfileHandle)

# Define toolchain
makefileHandle.write("# Define toolchain\n")
makefileHandle.write("CC = " + umakefileJson["toolchain"]+"-gcc\n")
makefileHandle.write("CPP = " + umakefileJson["toolchain"]+"-g++\n")
makefileHandle.write("OBJCOPY = " + umakefileJson["toolchain"]+"-objcopy\n")
makefileHandle.write("SIZE = " + umakefileJson["toolchain"]+"-size\n")

# Primary ALL target
makefileHandle.write("\n# Primary target\n")
makefileHandle.write("all: _all\n\n")


# Custom targets
makefileHandle.write("# Custom targets\n")
if "targets" in umakefileJson:
    for custTargs in umakefileJson["targets"]:
        # Check if there is a default for this target, if so disable its generation
        if(custTargs["targetName"].lower() == "main"):
            inhibDefaultTgtMain = True
        if(custTargs["targetName"].lower() == "reset"):
            inhibDefaultTgtReset = True
        if(custTargs["targetName"].lower() == "chiperase"):
            inhibDefaultTgtChipErase = True
        if(custTargs["targetName"].lower() == "size"):
            inhibDefaultTgtSize = True
        if(custTargs["targetName"].lower() == "clean"):
            inhibDefaultTgtClean = True
        if(custTargs["targetName"].lower() == "program"):
            inhibDefaultTgtProgram = True

        # Generate custom target
        try:
            makefileHandle.write("%s: %s\n" %
                                 (custTargs["targetName"], custTargs["depends"]))
        except:
            print("Error, Target: \"%s\" missing depends key." %
                  custTargs["targetName"])
            exit(0)
        for content in custTargs["content"]:
            makefileHandle.write("\t%s\n" % content)
        makefileHandle.write("\n")


# Default targets
makefileHandle.write("# Default targets\n")
if False == inhibDefaultTgtMain:
    defaultTgtMain()
if False == inhibDefaultTgtReset:
    defaultTgtReset()
if False == inhibDefaultTgtChipErase:
    defaultTgtChipErase()
if False == inhibDefaultTgtSize:
    defaultTgtSize()
if False == inhibDefaultTgtClean:
    defaultTgtClean()
if False == inhibDefaultTgtProgram:
    defaultTgtProgram()
makefileHandle.write("\n\n")

# Boiler plate
makefileHandle.write("# Boiler plate\n")
writeBoilerPlate(makefileHandle)

# Depfile
makefileHandle.write("\n\n# Depfile\n")
makefileHandle.write("include "+buildDir+"/"+DEP_FILE()+"\n")


makefileHandle.close()
depfileHandle.close()
