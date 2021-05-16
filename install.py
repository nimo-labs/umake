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

import platform
import os

osType = platform.system()

if 'Linux' == osType:
    if os.geteuid() != 0:
        print("This script needs to be run as root. Try sudo !!")
        exit(1)
    os.system('cp -f ./umake.py /usr/local/bin/umake')
	os.system('wget https://github.com/nimo-labs/hid_bootloader_console_client/releases/download/latest/hidBoot'
    os.system('chmod +x ./hidBoot')
    os.system('cp -f ./hidBoot /usr/local/bin')

else:
    print("Sorry, your operating system isn't supported just yet")
    exit(1)
