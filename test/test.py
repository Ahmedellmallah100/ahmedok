# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# Keep this small for gate-level simulation.
SLOW_CLOCK_CYCLES = 5000

SEG_TO_DIGIT = {
    0b0000001: 0,
    0b1001111: 1,
    0b0010010: 2,
    0b0000110: 3,
    0b1001100: 4,
    0b0100100: 5,
    0b0100000: 6,
    0b0001111: 7,
    0b0000000: 8,
    0b0000100: 9,
}


def decode_7seg(value):
    value &= 0x7F
    assert value in SEG_TO_DIGIT, f"Unknown 7-segment pattern: {value:07b}"
    return SEG_TO_DIGIT[value]


def check_outputs_resolvable(dut):
    assert dut.uo_out.value.is_resolvable, f"uo_out contains X/Z: {dut.uo_out.value}"
    assert dut.uio_out.value.is_resolvable, f"uio_out contains X/Z: {dut.uio_out.value}"


async def reset(dut):
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)
    check_outputs_resolvable(dut)


async def press_button(dut, button):
    dut.uio_in.value = button
    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)
    check_outputs_resolvable(dut)


async def set_a(dut, value):
    dut.ui_in.value = value
    await press_button(dut, 0b001)


async def set_b(dut, value):
    dut.ui_in.value = value
    await press_button(dut, 0b010)


async def execute(dut, opcode):
    dut.ui_in.value = opcode
    await press_button(dut, 0b100)


def current_anode(dut):
    return (dut.uio_out.value.to_unsigned() >> 3) & 0xF


def current_digit(dut):
    return decode_7seg(dut.uo_out.value.to_unsigned() & 0x7F)


async def observe_display(dut, cycles=20000):
    """Sample every clock so we don't depend on multiplexing phase."""
    seen = {}
    for _ in range(cycles):
        await ClockCycles(dut.clk, 1)
        an = current_anode(dut)

        if an == 0b1110:
            seen[0] = current_digit(dut)
        elif an == 0b1101:
            seen[1] = current_digit(dut)
        elif an == 0b1011:
            seen[2] = current_digit(dut)
        elif an == 0b0111:
            seen[3] = current_digit(dut)

        if len(seen) == 4:
            break

    dut._log.info(f"ANODES/DIGITS DETECTED: {seen}")
    return seen


def expected_result(a, b, opcode):
    if opcode == 0b001:
        return (a + b) & 0xFF
    if opcode == 0b010:
        return (a - b) & 0xFF
    if opcode == 0b011:
        return ((~a) + 1) & 0xFF
    if opcode == 0b100:
        return a & b
    if opcode == 0b101:
        return a | b
    if opcode == 0b110:
        return a ^ b
    return 0


async def test_operation(dut, a, b, opcode, name):
    dut._log.info(f"TEST: {name} | A={a} B={b}")

    await set_a(dut, a)
    await set_b(dut, b)
    await execute(dut, opcode)

    expected = expected_result(a, b, opcode)
    digits = await observe_display(dut)

    # Require the four anodes to be seen.
    assert set(digits) == {0, 1, 2, 3}, (
        f"Not all 4 anodes detected. Detected: {digits}"
    )

    # Display is hundreds/tens/ones on AN2/AN1/AN0.
    actual = digits[2] * 100 + digits[1] * 10 + digits[0]

    assert actual == expected, (
        f"{name}: expected {expected}, got {actual}, digits={digits}"
    )

    dut._log.info(f"PASS: {name} -> {actual}")


@cocotb.test()
async def test_project(dut):
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1

    dut._log.info("=== START SMALL ALU TEST ===")
    await reset(dut)

    # A small but useful functional set.
    await test_operation(dut, 20, 10, 0b001, "ADD")
    await test_operation(dut, 20, 10, 0b010, "SUB")
    await test_operation(dut, 0, 0, 0b001, "ZERO ADD")
    await test_operation(dut, 200, 100, 0b001, "ADD OVERFLOW")

    dut._log.info("=== ALL SMALL TESTS PASSED ===")
