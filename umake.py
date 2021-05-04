#!/usr/bin/python3

import json
import os
import sys


def WORKING_DIR():
    return "umake"


def DEP_FILE():
    return "depfile"


def processLibs(umakefileJson, makefileHandle, depfileHandle):
    for lib in umakefileJson["libraries"]:
        currentLib = lib["libName"]
        print("Processing library: %s" % currentLib)
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
            print(cmd)
            os.system(cmd)

            # Make sure we get the latest branch commits
            # os.system("git reset --hard origin/" + lib["branch"])
            cmd = "git fetch origin " + lib["branch"]
            print(cmd)
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
            for files in bookJson['files']:
                makefileHandle.write("# %s include path\n" % currentBook)
                makefileHandle.write(
                    "INCLUDES += -I ./umake/nimolib/%s/\n" % currentBook)
                makefileHandle.write("# %s source files\n" % currentBook)
                if files["language"] == 'c':
                    makefileHandle.write(
                        "SRCS += ./umake/nimolib/%s/%s\n" % (currentBook, files["fileName"]))
                    depfileHandle.write(
                        "./build/%s.o: ./umake/nimolib/%s/%s\n" % (files["fileName"][:-2], currentBook, files["fileName"]))
                    depfileHandle.write("\t$(UMAKE_MAKEC)\n")
                elif files["language"] == 'cpp':
                    makefileHandle.write(
                        "CPPSRCS += ./umake/nimolib/%s/%s\n" % (currentBook, files["fileName"]))
                elif files["language"] == 'asm':
                    makefileHandle.write(
                        "ARCS += ./umake/nimolib/%s/%s\n" % (currentBook, files["fileName"]))
                else:
                    print("Unknown language for %s/%s/%s" %
                          (currentLib, currentBook, files['fileName']))
            bookHandle.close()
            os.chdir("..")


def processUc(umakefileJson, makefileHandle, depfileHandle):
    microcontroller = umakefileJson['microcontroller']
    restoreDir = os.getcwd()
    os.chdir("uC")
    print(os.getcwd())

    uCHandle = open("uc_"+microcontroller+"-linux-gcc.json", 'r')
    uCJson = json.load(uCHandle)

    if uCJson['microcontroller'] != microcontroller:
        print("Microcontroller: %s doesn't match requested: %s" %
              (uCJson['microcontroller'], microcontroller))
        exit()
    makefileHandle.write("\n\n# Microcontroller defines\n")
    for uCDefines in uCJson["defines"]:
        makefileHandle.write("DEFINES += -D %s\n" % uCDefines)

    makefileHandle.write("\n# Microcontroller CFLAGS\n")
    for uCCflags in uCJson["cflags"]:
        makefileHandle.write("CFLAGS += %s\n" % uCCflags)
    makefileHandle.write("\n# Microcontroller LDFLAGS\n")

    for uCLdflags in uCJson["ldflags"]:
        makefileHandle.write("LDFLAGS += %s\n" % uCLdflags)

    makefileHandle.write("\n# Linker file\n")
    makefileHandle.write("LDFLAGS += -Wl,--script=%s\n" %
                         uCJson['linkerFile'])

    makefileHandle.write("\n# Startup file\n")
    makefileHandle.write("SRCS += %s\n" % uCJson['startupFile'])

    startupFnLst = uCJson['startupFile'].split('/')
    startupFn = startupFnLst[len(startupFnLst)-1]
    depfileHandle.write(
        "./build/%s.o: ./%s\n" % (startupFn[:-2], uCJson['startupFile']))
    depfileHandle.write("\t$(UMAKE_MAKEC)\n")

    os.chdir(restoreDir)


def writeBoilerPlate(makefileHandle):
    makefileHandle.write("""
CFLAGS += $(INCLUDES) $(DEFINES)
OBJS = $(addprefix $(BUILD)/, $(subst .c,.o, $(notdir $(SRCS))))
OBJS += $(addprefix $(BUILD)/, $(subst .S,.o, $(notdir $(ASRCS))))
OBJS += $(addprefix $(BUILD)/, $(subst .cpp,.o, $(CPPSRCS)))

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
chip-erase:
	killall -s 9 openocd || true
	openocd -d1 -f ./openocd.cfg -c init -c \"at91samd chip-erase\" -c \"exit\"""")


def defaultTgtSize():
    makefileHandle.write(
            """
size: $(BUILD)/$(BIN).elf
	@echo size:
	@$(SIZE) -t $^""")


def defaultTgtClean():
    makefileHandle.write(
            """
clean:
	@echo clean
	find ./build ! -name 'depfile' -type f -exec rm -f {} +
	@-rm -rf ../*~""")


def umakeClean(umakefileJson):
    os.system("make clean")
    os.system("rm -rf ./"+WORKING_DIR())
    os.system("rm -rf ./"+umakefileJson["buildDir"])


# MAIN
try:
    os.makedirs(WORKING_DIR(), exist_ok=True)
except OSError:
    print("Creation of the directory %s failed" % WORKING_DIR())

try:
    with open('./umakefile', 'r') as handle:
        umakefileJson = json.load(handle)
except:
    print("./umakefile not found.")
    exit(0)

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
    '# File autogenerated by umake, DO NOT hand edit. Changes will be overwritten\n')

os.chdir(WORKING_DIR())

# Process libraries
processLibs(umakefileJson, makefileHandle, depfileHandle)

# Add phony statement
makefileHandle.write("\n.PHONY: all clean size\n")
# Add build dir
makefileHandle.write("\nBUILD = %s\n" % buildDir)
# Add binary filename
makefileHandle.write("BIN = %s\n" % umakefileJson['target'])

# Add project level sources
makefileHandle.write("\n# Project sources\n")
makefileHandle.write("# C sources\n")
for projSources in umakefileJson["c_sources"]:
    makefileHandle.write("SRCS += %s\n" % projSources)
    rawFileName = os.path.basename(projSources)
    rawFileName = rawFileName[:-2]
    depfileHandle.write(
        "./build/"+rawFileName+".o: "+projSources+"\n")
    depfileHandle.write("\t$(UMAKE_MAKEC)\n")

makefileHandle.write("\n\n# Project include directories\n")
for projIncludes in umakefileJson["includes"]:
    makefileHandle.write("INCLUDES += -I %s" % projIncludes)

# Process microcontroller
processUc(umakefileJson, makefileHandle, depfileHandle)

# Define toolchain
makefileHandle.write("\n# Define toolchain\n")
makefileHandle.write("CC = " + umakefileJson["toolchain"]+"-gcc\n")
makefileHandle.write("CPP = " + umakefileJson["toolchain"]+"-g++\n")
makefileHandle.write("OBJCOPY = " + umakefileJson["toolchain"]+"-objcopy\n")
makefileHandle.write("SIZE = " + umakefileJson["toolchain"]+"-size\n")

# Primary ALL target
makefileHandle.write("\n# Primary target\n")
makefileHandle.write("all: _all\n")


# Custom targets
makefileHandle.write("\n# Custom targets\n")

# Default targets
makefileHandle.write("\n# Default targets\n")
defaultTgtMain()
defaultTgtReset()
defaultTgtChipErase()
defaultTgtSize()
defaultTgtClean()

# Boiler plate
makefileHandle.write("\n# Boiler plate\n")
writeBoilerPlate(makefileHandle)

# Depfile
makefileHandle.write("\n\n# Depfile\n")
makefileHandle.write("include "+buildDir+"/"+DEP_FILE()+"\n")


makefileHandle.close()
depfileHandle.close()
