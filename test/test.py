# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Clock: 100 KHz
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 10)

    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    # Set switches
    dut.ui_in.value = 20

    # Wait for the circuit
    await ClockCycles(dut.clk, 20)

    # Output must be known
    assert dut.uo_out.value.is_resolvable

    dut._log.info("Output is resolvable")
