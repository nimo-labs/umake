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

#include <sam.h>
#include <gpio.h>
#include <delay.h>
#include <osc.h>

#include "hal.h"
#include "system.h"

void main(void)
{
    unsigned long delayLast;

    oscSet(OSC_INT8);

    GPIO_PIN_DIR(SAM_GPIO_PMUX_A, 6, GPIO_DIR_OUT);
    GPIO_PIN_OUT(SAM_GPIO_PMUX_A, 6, GPIO_OUT_LOW);

    GPIO_PIN_DIR(SAM_GPIO_PMUX_A, 7, GPIO_DIR_OUT);
    GPIO_PIN_OUT(SAM_GPIO_PMUX_A, 7, GPIO_OUT_HIGH);

    delaySetup(UP_CLK / 1000); /*Clock timer at 1mS*/

    delayLast = delayGetTicks();
    while (1)
    {
        if (delayMillis(delayLast, 1000))
        {
            delayLast = delayGetTicks();
            GPIO_PIN_TGL(SAM_GPIO_PMUX_A, 7);
            GPIO_PIN_TGL(SAM_GPIO_PMUX_A, 6);
        }
    }
}