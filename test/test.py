import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ============================================================
# Configuration
# ============================================================

# Your clk_divider needs about 250,001 input clock cycles
# for one slow_clk toggle.
#
# Four anodes therefore need roughly:
# 4 * 250,001 = ~1,000,000 clock cycles
#
# Keep this large enough to observe all 4 digits.
SLOW_CLOCK_CYCLES = 5000


# ============================================================
# 7-Segment Decoder
# ============================================================

SEGMENTS = {
    0x3F: 0,
    0x06: 1,
    0x5B: 2,
    0x4F: 3,
    0x66: 4,
    0x6D: 5,
    0x7D: 6,
    0x07: 7,
    0x7F: 8,
    0x6F: 9,
}


def decode_7seg(value):
    """
    Decode 7-segment output.

    out_seg[6:0] is used.
    out_seg[7] is ignored.
    """

    value = value & 0x7F

    return SEGMENTS.get(value, None)


# ============================================================
# Reset
# ============================================================

async def reset_dut(dut):

    dut.rst_n.value = 0

    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1

    await ClockCycles(dut.clk, 20)

    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 20)


# ============================================================
# Button Control
# ============================================================

async def press_button(dut, button):

    """
    button:
        1 -> PB1
        2 -> PB2
        3 -> PB3
    """

    if button == 1:
        value = 0b00000001

    elif button == 2:
        value = 0b00000010

    elif button == 3:
        value = 0b00000100

    else:
        raise ValueError("Invalid button")

    # Press
    dut.uio_in.value = value

    # Debouncer is driven by slow_clk,
    # so wait enough source clock cycles.
    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)

    # Release
    dut.uio_in.value = 0

    await ClockCycles(dut.clk, SLOW_CLOCK_CYCLES)


# ============================================================
# Set A
# ============================================================

async def set_a(dut, value):

    dut.ui_in.value = value

    await press_button(dut, 1)


# ============================================================
# Set B
# ============================================================

async def set_b(dut, value):

    dut.ui_in.value = value

    await press_button(dut, 2)


# ============================================================
# Execute Operation
# ============================================================

async def execute_operation(dut):

    await press_button(dut, 3)


# ============================================================
# Read Current Display
# ============================================================

def get_anode(dut):

    """
    uio_out:

        bits [3:0] = anodes

    Expected:

        1110 -> digit 0
        1101 -> digit 1
        1011 -> digit 2
        0111 -> digit 3
    """

    value = int(dut.uio_out.value)

    return value & 0x0F


def get_segment(dut):

    value = int(dut.uo_out.value)

    return value & 0x7F


# ============================================================
# Observe Display
# ============================================================

async def observe_display(dut, cycles=1100000):

    """
    Observe the multiplexed 7-segment display.

    The design changes the anode using slow_clk.

    We need approximately 1,000,000 source-clock cycles
    to see all four anodes.
    """

    digits = {}

    for _ in range(cycles):

        an = get_anode(dut)
        seg = get_segment(dut)

        digit = decode_7seg(seg)

        if digit is not None:

            if an == 0b1110:
                digits[0] = digit

            elif an == 0b1101:
                digits[1] = digit

            elif an == 0b1011:
                digits[2] = digit

            elif an == 0b0111:
                digits[3] = digit

        # Stop once all four digits were observed.
        if len(digits) == 4:
            break

        await ClockCycles(dut.clk, 1)

    cocotb.log.info(
        f"DISPLAY DIGITS DETECTED: {digits}"
    )

    return digits


# ============================================================
# Convert Display Digits To Number
# ============================================================

def digits_to_number(digits):

    if 0 not in digits:
        raise AssertionError("ONES digit was not detected")

    if 1 not in digits:
        raise AssertionError("TENS digit was not detected")

    if 2 not in digits:
        raise AssertionError("HUNDREDS digit was not detected")

    hundreds = digits[2]
    tens = digits[1]
    ones = digits[0]

    return hundreds * 100 + tens * 10 + ones


# ============================================================
# Check All Anodes
# ============================================================

async def check_all_anodes(dut):

    seen = set()

    # Need enough time for the slow clock to move
    # through all four states.
    for _ in range(1100000):

        an = get_anode(dut)

        if an == 0b1110:
            seen.add(0)

        elif an == 0b1101:
            seen.add(1)

        elif an == 0b1011:
            seen.add(2)

        elif an == 0b0111:
            seen.add(3)

        if len(seen) == 4:
            break

        await ClockCycles(dut.clk, 1)

    cocotb.log.info(
        f"ANODES DETECTED: {seen}"
    )

    assert seen == {0, 1, 2, 3}, (
        f"Not all anodes detected. Seen={seen}"
    )


# ============================================================
# ADD Test
# ============================================================

async def test_add(dut):

    cocotb.log.info(
        "TEST: ADD | A=20 B=10"
    )

    await set_a(dut, 20)
    await set_b(dut, 10)

    # ADD opcode = 001
    dut.ui_in.value = 0b00000001

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"ADD RESULT = {result}"
    )

    assert result == 30, (
        f"ADD failed: expected 30, got {result}"
    )


# ============================================================
# SUB Test
# ============================================================

async def test_sub(dut):

    cocotb.log.info(
        "TEST: SUB | A=20 B=10"
    )

    await set_a(dut, 20)
    await set_b(dut, 10)

    # SUB opcode = 010
    dut.ui_in.value = 0b00000010

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"SUB RESULT = {result}"
    )

    assert result == 10, (
        f"SUB failed: expected 10, got {result}"
    )


# ============================================================
# ZERO ADD Test
# ============================================================

async def test_zero_add(dut):

    cocotb.log.info(
        "TEST: ZERO ADD | A=0 B=0"
    )

    await set_a(dut, 0)
    await set_b(dut, 0)

    # ADD
    dut.ui_in.value = 0b00000001

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"ZERO ADD RESULT = {result}"
    )

    assert result == 0, (
        f"ZERO ADD failed: expected 0, got {result}"
    )


# ============================================================
# Overflow / Carry Test
# ============================================================

async def test_add_overflow(dut):

    cocotb.log.info(
        "TEST: ADD OVERFLOW | A=200 B=100"
    )

    await set_a(dut, 200)
    await set_b(dut, 100)

    # ADD
    dut.ui_in.value = 0b00000001

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"OVERFLOW ADD RESULT = {result}"
    )

    # ALU output is 9-bit internally:
    #
    # 200 + 100 = 300
    #
    # But BCD converter receives:
    #
    # alu_result[7:0]
    #
    # 300 -> 8-bit value = 44
    #
    # Therefore the display is expected to show 44.
    assert result == 44, (
        f"Overflow ADD failed: expected 44, got {result}"
    )


# ============================================================
# AND Test
# ============================================================

async def test_and(dut):

    cocotb.log.info(
        "TEST: AND | A=15 B=3"
    )

    await set_a(dut, 15)
    await set_b(dut, 3)

    # AND opcode = 100
    dut.ui_in.value = 0b00000100

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"AND RESULT = {result}"
    )

    assert result == 3, (
        f"AND failed: expected 3, got {result}"
    )


# ============================================================
# OR Test
# ============================================================

async def test_or(dut):

    cocotb.log.info(
        "TEST: OR | A=8 B=3"
    )

    await set_a(dut, 8)
    await set_b(dut, 3)

    # OR opcode = 101
    dut.ui_in.value = 0b00000101

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"OR RESULT = {result}"
    )

    assert result == 11, (
        f"OR failed: expected 11, got {result}"
    )


# ============================================================
# XOR Test
# ============================================================

async def test_xor(dut):

    cocotb.log.info(
        "TEST: XOR | A=15 B=3"
    )

    await set_a(dut, 15)
    await set_b(dut, 3)

    # XOR opcode = 110
    dut.ui_in.value = 0b00000110

    await execute_operation(dut)

    digits = await observe_display(dut)

    result = digits_to_number(digits)

    cocotb.log.info(
        f"XOR RESULT = {result}"
    )

    assert result == 12, (
        f"XOR failed: expected 12, got {result}"
    )


# ============================================================
# Main Test
# ============================================================

@cocotb.test()
async def test_alu(dut):

    cocotb.log.info(
        "========================================"
    )

    cocotb.log.info(
        "=== START ALU GATE-LEVEL TEST ==="
    )

    cocotb.log.info(
        "========================================"
    )

    # Start clock
    cocotb.start_soon(
        Clock(
            dut.clk,
            10,
            unit="us"
        ).start()
    )

    # Reset
    await reset_dut(dut)

    cocotb.log.info(
        "RESET PASSED"
    )

    # --------------------------------------------------------
    # Check display multiplexing
    # --------------------------------------------------------

    cocotb.log.info(
        "CHECKING DISPLAY ANODES..."
    )

    await check_all_anodes(dut)

    cocotb.log.info(
        "DISPLAY ANODES PASSED"
    )

    # --------------------------------------------------------
    # ALU tests
    # --------------------------------------------------------

    await test_add(dut)

    await test_sub(dut)

    await test_zero_add(dut)

    await test_add_overflow(dut)

    await test_and(dut)

    await test_or(dut)

    await test_xor(dut)

    # --------------------------------------------------------
    # Finish
    # --------------------------------------------------------

    cocotb.log.info(
        "========================================"
    )

    cocotb.log.info(
        "=== ALL ALU TESTS PASSED ==="
    )

    cocotb.log.info(
        "========================================"
    )