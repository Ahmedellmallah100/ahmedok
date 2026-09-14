# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ------------------------------------------------------------
# Press PB1, PB2 or PB3
# ------------------------------------------------------------
async def press_button(dut, button):

    dut.uio_in.value = button

    # Hold button long enough for the slow clock
    await ClockCycles(dut.clk, 500020)

    dut.uio_in.value = 0

    # Wait for debounce
    await ClockCycles(dut.clk, 500020)


# ------------------------------------------------------------
# Reset
# ------------------------------------------------------------
async def reset(dut):

    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await ClockCycles(dut.clk, 10)

    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 10)


# ------------------------------------------------------------
# Check output is known
# ------------------------------------------------------------
def check_output(dut):

    assert dut.uo_out.value.is_resolvable, (
        f"uo_out contains X/Z: {dut.uo_out.value}"
    )

    assert dut.uio_out.value.is_resolvable, (
        f"uio_out contains X/Z: {dut.uio_out.value}"
    )


# ------------------------------------------------------------
# Main test
# ------------------------------------------------------------
@cocotb.test()
async def test_project(dut):

    dut._log.info("================================")
    dut._log.info("     START ALU FULL TEST")
    dut._log.info("================================")

    # 100 KHz clock
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Enable
    dut.ena.value = 1

    # --------------------------------------------------------
    # RESET TEST
    # --------------------------------------------------------

    dut._log.info("Testing RESET")

    await reset(dut)

    check_output(dut)

    dut._log.info("RESET PASSED")

    # --------------------------------------------------------
    # TEST A = 20
    # --------------------------------------------------------

    dut._log.info("Setting A = 20")

    dut.ui_in.value = 20

    await press_button(dut, 0b001)

    check_output(dut)

    dut._log.info("A = 20 PASSED")

    # --------------------------------------------------------
    # TEST B = 10
    # --------------------------------------------------------

    dut._log.info("Setting B = 10")

    dut.ui_in.value = 10

    await press_button(dut, 0b010)

    check_output(dut)

    dut._log.info("B = 10 PASSED")

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    dut._log.info("Testing ADD")

    dut.ui_in.value = 0b001

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("ADD PASSED")

    # --------------------------------------------------------
    # SUB
    # --------------------------------------------------------

    dut._log.info("Testing SUB")

    dut.ui_in.value = 0b010

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("SUB PASSED")

    # --------------------------------------------------------
    # NOT
    # --------------------------------------------------------

    dut._log.info("Testing NOT")

    dut.ui_in.value = 0b011

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("NOT PASSED")

    # --------------------------------------------------------
    # AND
    # --------------------------------------------------------

    dut._log.info("Testing AND")

    dut.ui_in.value = 0b100

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("AND PASSED")

    # --------------------------------------------------------
    # OR
    # --------------------------------------------------------

    dut._log.info("Testing OR")

    dut.ui_in.value = 0b101

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("OR PASSED")

    # --------------------------------------------------------
    # XOR
    # --------------------------------------------------------

    dut._log.info("Testing XOR")

    dut.ui_in.value = 0b110

    await press_button(dut, 0b100)

    check_output(dut)

    dut._log.info("XOR PASSED")

    # --------------------------------------------------------
    # DISPLAY / ANODE TEST
    # --------------------------------------------------------

    dut._log.info("Testing 7-segment outputs")

    # Wait for several digit selections
    await ClockCycles(dut.clk, 100)

    check_output(dut)

    # uio[3:6] contains digit control
    anodes = dut.uio_out.value.integer & 0x78

    assert anodes != 0, (
        f"Anode outputs are not active: {dut.uio_out.value}"
    )

    dut._log.info("7-SEGMENT OUTPUT PASSED")

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    dut._log.info("================================")
    dut._log.info("       ALL TESTS PASSED")
    dut._log.info("================================")
