/*
 * This file is part of the umake distribution (https://github.com/nimo-labs/umake).
 * Copyright (c) 2021 Nimolabs Ltd. www.nimo.uk
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
#include "stdio.h"
#include "NuMicro.h"


/*---------------------------------------------------------------------------------------------------------
* Main Function
* Turns on the red LED of the NuMaker-M032LD dev board
*
* Note that the Nuvoton version of OpenOCD is required: https://github.com/OpenNuvoton/OpenOCD-Nuvoton
*---------------------------------------------------------------------------------------------------------*/
int32_t main(void)
{
    GPIO_SetMode(PB, BIT14, GPIO_MODE_OUTPUT);
    PB14 = 0;

    while(1);
}
