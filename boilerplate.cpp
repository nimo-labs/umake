/*
 * This file is part of the umake distribution (https://github.com/nimo-labs/umake).
 * Copyright (c) 2020 Nimolabs Ltd. www.nimo.uk
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include <string>
#include <fstream>
#include <iostream>

#include "boilerplate.h"

using namespace std;

void generateToolchainArm_none_eabi(std::ofstream &makefile)
{
    makefile << "CC = arm-none-eabi-gcc\n";
    makefile << "CPP = arm-none-eabi-g++\n";
    makefile << "OBJCOPY = arm-none-eabi-objcopy\n";
    makefile << "SIZE = arm-none-eabi-size\n\n";
}

void generateBoilerPlate(std::ofstream &makefile)
{
    /*Add includes and defines to CFLAGS*/
    makefile << "CFLAGS += ${INCLUDES} ${DEFINES}" << endl;

    /*Generate object list with reference to build directory*/
    makefile << "OBJS = $(addprefix $(BUILD)/, $(subst .c,.o, $(notdir $(SRCS))))" << endl;
    makefile << "OBJS += $(addprefix $(BUILD)/, $(subst .cpp,.o, $(CPPSRCS)))" << endl;

    makefile << endl;
    makefile << "define UMAKE_MAKEC" << endl;
    makefile << "@echo CC $@" << endl;
    makefile << "@${CC}  $(CPPFLAGS) $(CFLAGS) -c $< -o $(addprefix ${BUILD}/, $(notdir $@))" << endl;
    makefile << "endef" << endl;
    makefile << endl;
    makefile << "define UMAKE_MAKECPP" << endl;
    makefile << "@echo CPP $@" << endl;
    makefile << "@${CPP}  $(CPPFLAGS) $(CFLAGS) -c $< -o $(addprefix ${BUILD}/, $(notdir $@))" << endl;
    makefile << "endef" << endl;
    makefile << endl
             << endl;

    makefile << "$(BUILD)/$(BIN).elf: $(OBJS)\n";
    makefile << "\t@echo LD $@\n";
    makefile << "\t@$(CC) $(LDFLAGS) $(addprefix ${BUILD}/, $(notdir ${OBJS})) $(LIBS) -o $@\n\n";

    makefile << "$(BUILD)/$(BIN).hex: $(BUILD)/$(BIN).elf\n";
    makefile << "\t@echo OBJCOPY $@\n";
    makefile << "\t@$(OBJCOPY) -O ihex $^ $@\n\n";

    makefile << "$(BUILD)/$(BIN).bin: $(BUILD)/$(BIN).elf\n";
    makefile << "\t@echo OBJCOPY $@\n";
    makefile << "\t@$(OBJCOPY) -O binary $^ $@\n\n";

    // makefile << "# c++ source\n";
    // makefile << "$(BUILD)/%.o: %.cpp\n";
    // makefile << "\t@echo CPP $@\n";
    // makefile << "\t@${CPP}  $(CPPFLAGS) $(CFLAGS) -c $< -o $(addprefix ${BUILD}/, $(notdir $@))\n\n";

    makefile << "size: $(BUILD)/$(BIN).elf\n";
    makefile << "\t@echo size:\n";
    makefile << "\t@$(SIZE) -t $^\n";

    makefile << "clean:\n";
    makefile << "\t@echo clean\n";
    makefile << "\t@-rm -rf $(BUILD)\n";
    makefile << "\t@-rm -rf ../*~\n\n";

    makefile << "include build/depfile" << endl;
}

void generateTargetAll(std::ofstream &makefile)
{
    makefile << "_all: $(BUILD)/$(BIN).hex $(BUILD)/$(BIN).bin size\n\n";
}

void generateTargetProgram(std::ofstream &makefile)
{
    makefile << "program: $(BUILD)/$(BIN).hex\n";
    makefile << "\tkillall -s 9 openocd || true\n";
    makefile << "\topenocd -d1 -f ./openocd.cfg -c init -c \" halt \" -c \" flash write_image erase $(BUILD)/${BIN}.hex \" -c \" verify_image $(BUILD)/${BIN}.hex \" -c \" reset run \" -c \" exit \"\n\n";
}

void generateTargetReset(std::ofstream &makefile)
{
    makefile << "reset: $(BUILD)/$(BIN).hex\n";
    makefile << "\tkillall -s 9 openocd || true\n";
    makefile << "\topenocd -d1 -f ./openocd.cfg -c init -c \" reset \" -c \" exit \"\n\n";
}

void generateTargetChipErase(std::ofstream &makefile)
{
    makefile << "chip-erase:\n";
    makefile << "\tkillall -s 9 openocd || true\n";
    makefile << "\topenocd -d1 -f ./openocd.cfg -c init -c \"at91samd chip-erase\" -c \"exit\"\n\n";
}