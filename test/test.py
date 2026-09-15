# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ============================================================
# Configuration
# ============================================================


SLOW_CLOCK_CYCLES = 500000


# ============================================================
# 7-Segment Decoder
# ============================================================


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

    value = value & 0x7F

    assert value in SEG_TO_DIGIT, (
        f"Unknown 7-segment pattern: {value:07b}"
    )

    return SEG_TO_DIGIT[value]


# ============================================================
# Output Checks
# ============================================================

def check_outputs_resolvable(dut):

    assert dut.uo_out.value.is_resolvable, (
        f"uo_out contains X/Z: {dut.uo_out.value}"
    )

    assert dut.uio_out.value.is_resolvable, (
        f"uio_out contains X/Z: {dut.uio_out.value}"
    )


# ============================================================
# Reset
# ============================================================

async def reset(dut):

    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await ClockCycles(dut.clk, 10)

    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 10)

    check_outputs_resolvable(dut)


# ============================================================
# Button Press
# ============================================================

async def press_button(dut, button):

    # Press button
    dut.uio_in.value = button

    # Wait until debounce detects it
    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)

    # Release button
    dut.uio_in.value = 0

    # Wait for debounce to return to idle
    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)

    check_outputs_resolvable(dut)


# ============================================================
# Read Anode
# ============================================================

def get_current_anode(dut):

    value = dut.uio_out.value.to_unsigned()

    # uio_out[6:3] = AN3 AN2 AN1 AN0
    return (value >> 3) & 0xF


# ============================================================
# Read Current 7-Segment Digit
# ============================================================

def get_current_digit(dut):

    seg = dut.uo_out.value.to_unsigned() & 0x7F

    return decode_7seg(seg)


# ============================================================
# Read Complete Display
# ============================================================

async def read_display(dut, slow_cycles=2):

    digits = {}

    # Wait through multiple complete multiplexing cycles.
    for _ in range(slow_cycles):

        for _ in range(4):

            # Wait for the next slow clock.
            await ClockCycles(
                dut.clk,
                SLOW_CLOCK_CYCLES
            )

            check_outputs_resolvable(dut)

            an = get_current_anode(dut)
            digit = get_current_digit(dut)

      

            if an == 0b1110:
                digits[0] = digit

            elif an == 0b1101:
                digits[1] = digit

            elif an == 0b1011:
                digits[2] = digit

            elif an == 0b0111:
                digits[3] = digit

    return digits


# ============================================================
# Convert Display Digits to Integer
# ============================================================

def digits_to_number(digits):

    assert 0 in digits, "AN0 was not detected"
    assert 1 in digits, "AN1 was not detected"
    assert 2 in digits, "AN2 was not detected"

    ones = digits[0]
    tens = digits[1]
    hundreds = digits[2]

    return hundreds * 100 + tens * 10 + ones


# ============================================================
# Check Internal LEDs / Letters (RTL)
# ============================================================

def check_internal_outputs(dut, expected_result, expected_letter):
    try:
        led = dut.core.led.value.to_unsigned() & 0xFF
        letters = dut.core.A1.letters.value.to_unsigned() & 0xF

        assert led == expected_result, (
            f"LED ERROR: expected {expected_result}, got {led}"
        )
        assert letters == expected_letter, (
            f"LETTERS ERROR: expected {expected_letter:X}, got {letters:X}"
        )

        dut._log.info(
            f"LED PASSED -> {led}, LETTERS PASSED -> {letters:X}"
        )
    except (AttributeError, ValueError):
        # Gate-level synthesis may remove internal signal names.
        pass


# ============================================================
# Check Display Result
# ============================================================

async def check_display(dut, expected):

    digits = await read_display(dut)

    actual = digits_to_number(digits)

    assert actual == expected, (
        f"\nDISPLAY ERROR\n"
        f"Expected : {expected}\n"
        f"Actual   : {actual}\n"
        f"Digits   : {digits}"
    )

    dut._log.info(
        f"DISPLAY PASSED -> {actual}"
    )


# ============================================================
# Check All Anodes
# ============================================================

async def check_all_anodes(dut):

    seen = set()

    # Give the multiplexer enough time to visit
    # all four digits.
    for _ in range(4):

        await ClockCycles(
            dut.clk,
            SLOW_CLOCK_CYCLES
        )

        an = get_current_anode(dut)

        seen.add(an)

    expected = {
        0b1110,
        0b1101,
        0b1011,
        0b0111
    }

    assert expected.issubset(seen), (
        f"\nANODE ERROR\n"
        f"Expected: {expected}\n"
        f"Detected: {seen}"
    )

    dut._log.info(
        f"ALL 4 ANODES PASSED -> {seen}"
    )


# ============================================================
# Set A
# ============================================================

async def set_a(dut, value):

    dut._log.info(
        f"Setting A = {value}"
    )

    dut.ui_in.value = value

    await press_button(
        dut,
        0b001
    )


# ============================================================
# Set B
# ============================================================

async def set_b(dut, value):

    dut._log.info(
        f"Setting B = {value}"
    )

    dut.ui_in.value = value

    await press_button(
        dut,
        0b010
    )


# ============================================================
# Execute Operation
# ============================================================

async def execute_operation(dut, opcode):

    dut._log.info(
        f"Executing opcode = {opcode:03b}"
    )

    # Opcode is taken from SW[2:0]
    dut.ui_in.value = opcode

    await press_button(
        dut,
        0b100
    )


# ============================================================
# Expected ALU Result
# ============================================================

def expected_result(a, b, opcode):

    # ADD
    if opcode == 0b001:
        return (a + b) & 0xFF

    # SUB
    elif opcode == 0b010:
        return (a - b) & 0xFF

    # TWO'S COMPLEMENT
    elif opcode == 0b011:
        return ((~a) + 1) & 0xFF

    # AND
    elif opcode == 0b100:
        return a & b

    # OR
    elif opcode == 0b101:
        return a | b

    # XOR
    elif opcode == 0b110:
        return a ^ b

    # Invalid opcode
    else:
        return 0


# ============================================================
# Test One Operation
# ============================================================

async def test_operation(
    dut,
    a,
    b,
    opcode,
    name,
    expected_letter
):

    dut._log.info(
        "========================================"
    )

    dut._log.info(
        f"TESTING {name}"
    )

    dut._log.info(
        f"A      = {a}"
    )

    dut._log.info(
        f"B      = {b}"
    )

    dut._log.info(
        f"OPCODE = {opcode:03b}"
    )

    # --------------------------------------------
    # Store A
    # --------------------------------------------

    await set_a(
        dut,
        a
    )

    # --------------------------------------------
    # Store B
    # --------------------------------------------

    await set_b(
        dut,
        b
    )

    # --------------------------------------------
    # Calculate expected result
    # --------------------------------------------

    expected = expected_result(
        a,
        b,
        opcode
    )

    dut._log.info(
        f"EXPECTED RESULT = {expected}"
    )

    # --------------------------------------------
    # Execute operation
    # --------------------------------------------

    await execute_operation(
        dut,
        opcode
    )

    # --------------------------------------------
    # Check 7-segment display
    # --------------------------------------------

    await check_display(
        dut,
        expected
    )

    check_internal_outputs(
        dut,
        expected,
        expected_letter
    )

    dut._log.info(
        f"{name} PASSED"
    )


# ============================================================
# Main Test
# ============================================================

@cocotb.test()
async def test_project(dut):

    dut._log.info(
        "========================================"
    )

    dut._log.info(
        "       START COMPLETE ALU TEST"
    )

    dut._log.info(
        "========================================"
    )

    # --------------------------------------------------------
    # Start clock
    # --------------------------------------------------------

    # 100 KHz
    clock = Clock(
        dut.clk,
        10,
        unit="us"
    )

    cocotb.start_soon(
        clock.start()
    )

    # Enable Tiny Tapeout design
    dut.ena.value = 1

    # ========================================================
    # RESET
    # ========================================================

    dut._log.info(
        "TESTING RESET"
    )

    await reset(dut)

    dut._log.info(
        "RESET PASSED"
    )

    # ========================================================
    # BASIC OPERATIONS
    # ========================================================

    A = 20
    B = 10

    # ADD
    await test_operation(
        dut,
        A,
        B,
        0b001,
        "ADD",
        0x1
    )

    # SUB
    await test_operation(
        dut,
        A,
        B,
        0b010,
        "SUB",
        0x2
    )

    # NOT
    await test_operation(
        dut,
        A,
        B,
        0b011,
        "TWO'S COMPLEMENT",
        0x3
    )

    # AND
    await test_operation(
        dut,
        A,
        B,
        0b100,
        "AND",
        0x4
    )

    # OR
    await test_operation(
        dut,
        A,
        B,
        0b101,
        "OR",
        0x5
    )

    # XOR
    await test_operation(
        dut,
        A,
        B,
        0b110,
        "XOR",
        0x6
    )

    # ========================================================
    # ZERO TEST
    # ========================================================

    await test_operation(
        dut,
        0,
        0,
        0b001,
        "ADD 0 + 0",
        0x1
    )

    # ========================================================
    # MAXIMUM VALUE TEST
    # ========================================================

    await test_operation(
        dut,
        255,
        0,
        0b001,
        "ADD 255 + 0",
        0x1
    )

    # ========================================================
    # OVERFLOW TEST
    # ========================================================

    # 200 + 100 = 300
    #
    # 8-bit result = 44

    await test_operation(
        dut,
        200,
        100,
        0b001,
        "ADD OVERFLOW",
        0x1
    )

    # ========================================================
    # UNDERFLOW TEST
    # ========================================================

    # 10 - 20 = -10
    #
    # 8-bit unsigned result = 246

    await test_operation(
        dut,
        10,
        20,
        0b010,
        "SUB UNDERFLOW",
        0x2
    )

    # ========================================================
    # DIFFERENT VALUES
    # ========================================================

    await test_operation(
        dut,
        123,
        45,
        0b001,
        "ADD 123 + 45",
        0x1
    )

    await test_operation(
        dut,
        255,
        255,
        0b100,
        "AND 255 & 255",
        0x4
    )

    await test_operation(
        dut,
        170,
        85,
        0b110,
        "XOR 170 ^ 85",
        0x6
    )

    # ========================================================
    # DISPLAY TEST
    # ========================================================

    dut._log.info(
        "========================================"
    )

    dut._log.info(
        "TESTING 7-SEGMENT DISPLAY"
    )

    dut._log.info(
        "========================================"
    )

    await check_display(
        dut,
        expected_result(
            170,
            85,
            0b110
        )
    )

    dut._log.info(
        "7-SEGMENT DISPLAY PASSED"
    )

    # ========================================================
    # ANODE TEST
    # ========================================================

    dut._log.info(
        "========================================"
    )

    dut._log.info(
        "TESTING ALL DISPLAY ANODES"
    )

    dut._log.info(
        "========================================"
    )

    await check_all_anodes(
        dut
    )

    # ========================================================
    # FINAL
    # ========================================================

    dut._log.info(
        "========================================"
    )

    dut._log.info(
        "       ALL TESTS PASSED"
    )

    dut._log.info(
        "========================================"
    )
